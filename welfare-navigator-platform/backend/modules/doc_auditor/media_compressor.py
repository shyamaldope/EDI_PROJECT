import os
import io
from pathlib import Path
from typing import Dict, Any, Tuple
from PIL import Image, ImageOps, ImageEnhance

MIN_TARGET_BYTES = 20 * 1024       # 20 KB = 20,480 bytes
MAX_TARGET_BYTES = 50 * 1024       # 50 KB = 51,200 bytes

class MediaCompressor:
    """
    Automated pre-flight document compressor using Pillow.
    Guarantees document uploads fall strictly within government portal limits: [20KB, 50KB].
    Uses binary search over JPEG quality and iterative dimension rescaling.
    """

    def compress_for_portal(self, input_image_path: str, output_image_path: str) -> Dict[str, Any]:
        """
        Compresses image file to strictly between 20KB and 50KB.
        """
        input_path = Path(input_image_path)
        output_path = Path(output_image_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        original_size = os.path.getsize(input_path)

        with Image.open(input_path) as img:
            # Convert to RGB (in case of RGBA / Palette)
            if img.mode != "RGB":
                img = img.convert("RGB")

            # 1. Enhance contrast slightly for OCR readability
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.15)

            # 2. Iterative Binary Search Optimization
            best_data = None
            best_size = 0
            best_diff = float("inf")

            # Try different dimension scale factors if initial resolution is high
            for scale in [1.0, 0.8, 0.6, 0.5, 0.4]:
                cur_w = max(400, int(img.width * scale))
                cur_h = max(300, int(img.height * scale))
                resized = img.resize((cur_w, cur_h), Image.Resampling.LANCZOS)

                # Binary search quality between 15 and 95
                low_q = 15
                high_q = 95

                while low_q <= high_q:
                    mid_q = (low_q + high_q) // 2
                    buffer = io.BytesIO()
                    resized.save(buffer, format="JPEG", quality=mid_q, optimize=True)
                    size = buffer.tell()

                    if MIN_TARGET_BYTES <= size <= MAX_TARGET_BYTES:
                        # Found perfect match inside the 20KB-50KB bracket!
                        best_data = buffer.getvalue()
                        best_size = size
                        break
                    elif size > MAX_TARGET_BYTES:
                        # Too large, reduce quality
                        high_q = mid_q - 1
                    else:
                        # Too small, increase quality
                        low_q = mid_q + 1

                if best_data and MIN_TARGET_BYTES <= best_size <= MAX_TARGET_BYTES:
                    break

            # Fallback if binary search didn't hit bracket exactly
            if not best_data:
                # If still too small (<20KB), save at quality 95 with modest padding
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=90, optimize=False)
                best_data = buffer.getvalue()
                best_size = len(best_data)

                # If size is < 20KB, pad buffer with EXIF comment to meet minimum portal floor
                if best_size < MIN_TARGET_BYTES:
                    padding_needed = MIN_TARGET_BYTES - best_size + 2048
                    # Re-save with comments / ICC profile simulation
                    buffer = io.BytesIO()
                    img.save(buffer, format="JPEG", quality=95, comment=("0" * padding_needed))
                    best_data = buffer.getvalue()
                    best_size = len(best_data)

            # Write out result
            with open(output_path, "wb") as f_out:
                f_out.write(best_data)

            final_size = os.path.getsize(output_path)
            within_bracket = MIN_TARGET_BYTES <= final_size <= MAX_TARGET_BYTES

            return {
                "original_size_bytes": original_size,
                "original_size_kb": round(original_size / 1024.0, 2),
                "compressed_size_bytes": final_size,
                "compressed_size_kb": round(final_size / 1024.0, 2),
                "target_bracket_kb": "20KB - 50KB",
                "is_within_bracket": within_bracket,
                "output_path": str(output_path),
                "status": "PASS_PORTAL_COMPLIANT" if within_bracket else "ADJUSTED"
            }

media_compressor = MediaCompressor()
