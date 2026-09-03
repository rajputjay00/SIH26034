import os
from typing import List

try:
    from pydantic_settings import BaseSettings
    class Settings(BaseSettings):
        APP_NAME: str = "LegalMetriX Compliance & Inspection System"
        ENVIRONMENT: str = "development"
        DEBUG: bool = True
        SECRET_KEY: str = "DEV_ONLY_SECURE_SECRET_KEY_MUST_BE_REPLACED_IN_PROD_123456789"
        ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
        DATABASE_URL: str = "sqlite:///./legalmetrix.db"
        ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
        REPORT_VERIFICATION_BASE_URL: str = "http://localhost:3000/verify"
        STORAGE_EVIDENCE_PATH: str = "storage/evidence"
        STORAGE_DERIVED_PATH: str = "storage/derived"
        STORAGE_REPORTS_PATH: str = "storage/reports"
except ImportError:
    class Settings:
        APP_NAME: str = os.getenv("APP_NAME", "LegalMetriX Compliance & Inspection System")
        ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")
        SECRET_KEY: str = os.getenv("SECRET_KEY", "DEV_ONLY_SECURE_SECRET_KEY_MUST_BE_REPLACED_IN_PROD_123456789")
        ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
        ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
        DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./legalmetrix.db")
        ALLOWED_ORIGINS: List[str] = [
            origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if origin.strip()
        ]
        REPORT_VERIFICATION_BASE_URL: str = os.getenv("REPORT_VERIFICATION_BASE_URL", "http://localhost:3000/verify")
        STORAGE_EVIDENCE_PATH: str = os.getenv("STORAGE_EVIDENCE_PATH", "storage/evidence")
        STORAGE_DERIVED_PATH: str = os.getenv("STORAGE_DERIVED_PATH", "storage/derived")
        STORAGE_REPORTS_PATH: str = os.getenv("STORAGE_REPORTS_PATH", "storage/reports")

settings = Settings()
