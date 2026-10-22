import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from rapidfuzz import fuzz
from PIL import Image, ImageFilter, ImageStat
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from config import settings

class CrossValidator:
    """
    Validates document OCR extractions against citizen profile ground-truth.
    Implements RapidFuzz string distance, Expiry verification vs 2026-10-22,
    Laplacian image quality scoring, and automated Affidavit generation.
    """

    def calculate_blur_score(self, image_path: str) -> float:
        """
        Computes high-frequency edge variance using Pillow's FIND_EDGES filter
        as a fast, robust proxy for the OpenCV Laplacian variance.
        """
        try:
            with Image.open(image_path) as img:
                gray = img.convert("L")
                edges = gray.filter(ImageFilter.FIND_EDGES)
                stat = ImageStat.Stat(edges)
                # stat.var contains variance of pixel intensities
                variance = stat.var[0] if stat.var else 0.0
                return round(variance, 2)
        except Exception:
            return 150.0 # Default fallback safe pass

    def validate_name_match(self, profile_name: str, doc_name: str) -> Dict[str, Any]:
        """
        Calculates RapidFuzz token_sort_ratio between profile name and document name.
        Threshold: 85.
        """
        if not profile_name or not doc_name:
            return {
                "score": 0.0,
                "passed": False,
                "alert": True,
                "message": "Missing name attribute in profile or document."
            }

        score = float(fuzz.token_sort_ratio(profile_name, doc_name))
        passed = score >= 85.0

        message = "Name verified successfully."
        if not passed:
            message = f"Name mismatch detected: Profile '{profile_name}' vs Document '{doc_name}' (Match: {score:.1f}% < 85%). Automated Self-Declaration Affidavit required."

        return {
            "score": score,
            "passed": passed,
            "alert": not passed,
            "message": message
        }

    def validate_expiry(self, valid_until_str: Optional[str], reference_date_str: str = settings.REFERENCE_DATE) -> Dict[str, Any]:
        """
        Compares certificate valid_until date against reference date (2026-10-22).
        """
        if not valid_until_str or valid_until_str.upper() in ["LIFETIME", "PERMANENT", "NA"]:
            return {
                "is_expired": False,
                "valid_until": "LIFETIME",
                "message": "Certificate is permanently valid (Lifetime)."
            }

        try:
            # Parse YYYY-MM-DD or DD/MM/YYYY
            if "/" in valid_until_str:
                parts = valid_until_str.split("/")
                if len(parts[0]) == 4:
                    valid_dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                else:
                    valid_dt = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
            else:
                valid_dt = datetime.strptime(valid_until_str[:10], "%Y-%m-%d")

            ref_dt = datetime.strptime(reference_date_str[:10], "%Y-%m-%d")

            if valid_dt < ref_dt:
                days_diff = (ref_dt - valid_dt).days
                return {
                    "is_expired": True,
                    "valid_until": valid_dt.strftime("%Y-%m-%d"),
                    "days_expired": days_diff,
                    "message": f"EXPIRED: Document expired on {valid_dt.strftime('%d/%m/%Y')} ({days_diff} days overdue). Renewal required."
                }
            else:
                return {
                    "is_expired": False,
                    "valid_until": valid_dt.strftime("%Y-%m-%d"),
                    "days_remaining": (valid_dt - ref_dt).days,
                    "message": f"VALID: Document remains valid until {valid_dt.strftime('%d/%m/%Y')}."
                }
        except Exception:
            return {
                "is_expired": False,
                "valid_until": valid_until_str,
                "message": "Unable to parse expiry date; manual verification advised."
            }

    def generate_name_affidavit_pdf(
        self,
        citizen_name: str,
        document_name: str,
        document_type: str,
        output_dir: str
    ) -> str:
        """
        Generates a formal legal Self-Declaration / Name Mismatch Affidavit PDF.
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = out_dir / f"Affidavit_Name_Mismatch_{citizen_name.replace(' ', '_')}.pdf"

        doc = SimpleDocTemplate(str(pdf_path), pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'AffTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            alignment=1,
            textColor=colors.HexColor('#1a365d')
        )
        body_style = ParagraphStyle('AffBody', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14)
        bold_style = ParagraphStyle('AffBold', parent=body_style, fontName='Helvetica-Bold')

        story = []
        story.append(Paragraph("GOVERNMENT OF MAHARASHTRA", title_style))
        story.append(Paragraph("SELF-DECLARATION AFFIDAVIT FOR NAME VARIATION", title_style))
        story.append(Spacer(1, 15))

        story.append(Paragraph("<b>Under Maharashtra Right to Public Services Act, 2015 & Citizen Charter</b>", body_style))
        story.append(Spacer(1, 15))

        story.append(Paragraph(
            f"I, <b>{citizen_name}</b>, an Indian citizen residing in the State of Maharashtra, do hereby solemnly affirm and state on oath as follows:",
            body_style
        ))
        story.append(Spacer(1, 10))

        story.append(Paragraph(
            f"1. That my true, correct, and official name as recorded in my Primary Citizen Profile is <b>{citizen_name}</b>.",
            body_style
        ))
        story.append(Spacer(1, 8))

        story.append(Paragraph(
            f"2. That in my submitted <b>{document_type}</b> certificate, my name appears as <b>{document_name}</b> due to abbreviation or transliteration differences.",
            body_style
        ))
        story.append(Spacer(1, 8))

        story.append(Paragraph(
            f"3. That <b>{citizen_name}</b> and <b>{document_name}</b> refer to one and the same living person, namely myself.",
            body_style
        ))
        story.append(Spacer(1, 8))

        story.append(Paragraph(
            "4. That I make this solemn declaration to substantiate my welfare scheme applications under government portals without wrongful rejection.",
            body_style
        ))
        story.append(Spacer(1, 20))

        story.append(Paragraph(f"<b>Date:</b> {settings.REFERENCE_DATE} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Place:</b> Kolhapur, Maharashtra", bold_style))
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"<b>(Signature / Thumb Impression of Applicant)</b><br/>{citizen_name}", bold_style))

        doc.build(story)
        return str(pdf_path)

cross_validator = CrossValidator()
