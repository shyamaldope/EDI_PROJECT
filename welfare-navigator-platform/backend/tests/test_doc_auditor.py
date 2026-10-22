import pytest
from pathlib import Path
from modules.doc_auditor.cross_validator import cross_validator
from modules.doc_auditor.media_compressor import media_compressor

def test_rapidfuzz_name_validation():
    # Exact match
    res1 = cross_validator.validate_name_match("Ramesh Shamrao Patil", "Ramesh Shamrao Patil")
    assert res1["passed"] is True
    assert res1["score"] == 100.0

    # Minor abbreviation / token sort match (Ramesh Shamrao Patil vs Shamrao Ramesh Patil)
    res2 = cross_validator.validate_name_match("Ramesh Shamrao Patil", "Shamrao Ramesh Patil")
    assert res2["passed"] is True
    assert res2["score"] == 100.0

    # Abbreviated name (Ramesh Shamrao Patil vs Ramesh S. Patil) -> Score around 82.5 < 85 -> Trigger Alert!
    res3 = cross_validator.validate_name_match("Ramesh Shamrao Patil", "Ramesh S. Patil")
    assert res3["alert"] is True
    assert res3["score"] < 85.0

def test_expiry_validation():
    # Expired date vs 2026-10-22
    exp_res = cross_validator.validate_expiry("2023-03-31", "2026-10-22")
    assert exp_res["is_expired"] is True
    assert exp_res["days_expired"] > 1000

    # Valid future date
    val_res = cross_validator.validate_expiry("2028-12-31", "2026-10-22")
    assert val_res["is_expired"] is False

    # Lifetime certificate
    life_res = cross_validator.validate_expiry("LIFETIME", "2026-10-22")
    assert life_res["is_expired"] is False

def test_media_compression_bracket(tmp_path):
    # Test Pillow binary-search compression enforces [20KB, 50KB]
    from PIL import Image
    test_img = tmp_path / "large_doc.jpg"
    out_img = tmp_path / "compressed_doc.jpg"

    # Create 1000x800 image
    img = Image.new("RGB", (1000, 800), color="#e2e8f0")
    img.save(str(test_img), "JPEG", quality=95)

    res = media_compressor.compress_for_portal(str(test_img), str(out_img))
    assert res["is_within_bracket"] is True
    assert 20 * 1024 <= res["compressed_size_bytes"] <= 51 * 1024
