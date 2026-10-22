import pytest
from modules.voice_profile.pii_scrubber import scrub_pii, hash_phone, hash_household

def test_aadhaar_redaction():
    text = "Citizen Ramesh Patil holds Aadhaar number 2849 1029 4812 and mobile 9820012345."
    res = scrub_pii(text)
    assert "[AADHAAR_REDACTED]" in res["clean_text"]
    assert "[PHONE_REDACTED]" in res["clean_text"]
    assert "2849" not in res["clean_text"]
    assert "9820012345" not in res["clean_text"]
    assert "AADHAAR" in res["redacted_types"]
    assert "PHONE" in res["redacted_types"]

def test_pan_redaction():
    text = "PAN card number ABCDE1234F submitted for verification."
    res = scrub_pii(text)
    assert "[PAN_REDACTED]" in res["clean_text"]
    assert "ABCDE1234F" not in res["clean_text"]

def test_cryptographic_phone_hash_determinism():
    h1 = hash_phone("9820012345")
    h2 = hash_phone("+91-98200-12345")
    h3 = hash_phone("09820012345")
    h4 = hash_phone("9820099999")

    assert h1 == h2 == h3 # Normalized match
    assert h1 != h4
    assert len(h1) == 64 # SHA-256

def test_household_hash():
    hh1 = hash_household("RC-MAHA-10294")
    hh2 = hash_household("rc-maha-10294")
    assert hh1 == hh2
    assert len(hh1) == 64
