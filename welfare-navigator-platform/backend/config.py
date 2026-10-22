import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    APP_NAME: str = "welfare-navigator-platform"
    ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    FRONTEND_PORT: int = 5173
    MOCK_PORTAL_PORT: int = 8001

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./welfare.db"
    SYNC_DATABASE_URL: str = "sqlite:///./welfare.db"

    # Redis & Background Tasks
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_CELERY: bool = False

    # Security & DPDP Act 2023 Cryptographic Salt
    SECRET_SALT: str = "welfare_platform_salt_secure_2026_dpdp_compliant"
    ENCRYPTION_KEY: str = "s3cr3t_3ncrypt10n_k3y_w3lf4r3_2026_k10sk_s4f3"

    # Dual-Mode AI
    USE_LOCAL_AI_FALLBACK: bool = True

    # Google Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Bhashini ULCA
    BHASHINI_API_KEY: str = ""
    BHASHINI_USER_ID: str = ""
    BHASHINI_PIPELINE_ID: str = ""

    # Twilio
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"

    # Reference Date for Expiry & SLA Evaluations
    REFERENCE_DATE: str = "2026-10-22"

    class Config:
        env_file = [
            str(BASE_DIR / ".env"),
            str(BASE_DIR.parent / ".env"),
            ".env"
        ]
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
