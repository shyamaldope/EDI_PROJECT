import re
import hashlib
from config import settings

# 12-digit Aadhaar pattern (with optional spaces or dashes)
# Must not start with 0 or 1 per UIDAI specification
AADHAAR_REGEX = re.compile(r'\b[2-9]\d{3}[\s-]?[0-9]{4}[\s-]?[0-9]{4}\b')

# 10-digit Indian Mobile pattern (optional +91 or 0 prefix, starts with 6-9)
PHONE_REGEX = re.compile(r'\b(?:\+91[\s-]?)?(?:0)?[6-9]\d{9}\b')

# 10-character PAN pattern (5 uppercase letters, 4 digits, 1 uppercase letter)
PAN_REGEX = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b')

def scrub_pii(text: str) -> dict:
    """
    Detects and redacts Aadhaar, Phone, and PAN from any text.
    Returns cleaned text and a metadata dict detailing redacted items.
    Enforces DPDP Act 2023 technical privacy guidelines.
    """
    if not text:
        return {"clean_text": "", "redacted_count": 0, "pii_badge": "[PII CLEAN]"}

    redacted_items = []

    def replace_aadhaar(match):
        redacted_items.append("AADHAAR")
        return "[AADHAAR_REDACTED]"

    def replace_phone(match):
        redacted_items.append("PHONE")
        return "[PHONE_REDACTED]"

    def replace_pan(match):
        redacted_items.append("PAN")
        return "[PAN_REDACTED]"

    clean_text = AADHAAR_REGEX.sub(replace_aadhaar, text)
    clean_text = PHONE_REGEX.sub(replace_phone, clean_text)
    clean_text = PAN_REGEX.sub(replace_pan, clean_text)

    badge = "[PII CLEAN]"
    if redacted_items:
        unique_types = sorted(list(set(redacted_items)))
        badge = f"[PII SCRUBBED: {', '.join(unique_types)} REDACTED]"

    return {
        "clean_text": clean_text,
        "redacted_count": len(redacted_items),
        "redacted_types": list(set(redacted_items)),
        "pii_badge": badge
    }

def hash_phone(phone: str, salt: str = None) -> str:
    """
    Computes a deterministic salted SHA-256 hash for citizen phone numbers.
    Prevents storage of cleartext telephone numbers.
    """
    salt = salt or settings.SECRET_SALT
    # Normalize: strip spaces, dashes, leading +91 or 0
    clean_phone = re.sub(r'[\s\-+]', '', phone)
    if clean_phone.startswith('91') and len(clean_phone) == 12:
        clean_phone = clean_phone[2:]
    elif clean_phone.startswith('0') and len(clean_phone) == 11:
        clean_phone = clean_phone[1:]
    
    return hashlib.sha256(f"{clean_phone}_{salt}".encode('utf-8')).hexdigest()

def hash_household(ration_card: str, salt: str = None) -> str:
    """
    Computes a deterministic salted SHA-256 hash for ration card / household ID.
    Enables family member grouping without storing raw ration card numbers.
    """
    salt = salt or settings.SECRET_SALT
    clean_rc = ration_card.strip().upper()
    return hashlib.sha256(f"{clean_rc}_{salt}".encode('utf-8')).hexdigest()
