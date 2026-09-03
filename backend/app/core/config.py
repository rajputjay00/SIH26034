import os
from typing import List, Union


def _parse_origins(val: Union[str, List[str], None]) -> List[str]:
    if not val:
        return ["http://localhost:3000", "http://127.0.0.1:3000"]
    if isinstance(val, list):
        origins = [str(o).strip() for o in val if str(o).strip()]
    elif isinstance(val, str):
        if val.startswith("[") and val.endswith("]"):
            import json
            try:
                origins = json.loads(val)
            except Exception:
                origins = [v.strip().strip("\"'") for v in val.strip("[]").split(",") if v.strip()]
        else:
            origins = [o.strip() for o in val.split(",") if o.strip()]
    else:
        origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # If FRONTEND_URL is additionally specified, include it
    frontend_url = os.getenv("FRONTEND_URL", "").strip()
    if frontend_url and frontend_url not in origins:
        origins.append(frontend_url)

    # In development, ensure localhost is always accessible
    for dev_origin in ["http://localhost:3000", "http://127.0.0.1:3000"]:
        if dev_origin not in origins and os.getenv("ENVIRONMENT", "development") != "production":
            origins.append(dev_origin)

    return origins


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "NIRIKSHAN - Legal Metrology Compliance & Inspection System")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "DEV_ONLY_SECURE_SECRET_KEY_MUST_BE_REPLACED_IN_PROD_123456789")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./legalmetrix.db")
    ALLOWED_ORIGINS: List[str] = _parse_origins(os.getenv("ALLOWED_ORIGINS"))
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    REPORT_VERIFICATION_BASE_URL: str = os.getenv("REPORT_VERIFICATION_BASE_URL", "http://localhost:3000/verify")
    STORAGE_EVIDENCE_PATH: str = os.getenv("STORAGE_EVIDENCE_PATH", "storage/evidence")
    STORAGE_DERIVED_PATH: str = os.getenv("STORAGE_DERIVED_PATH", "storage/derived")
    STORAGE_REPORTS_PATH: str = os.getenv("STORAGE_REPORTS_PATH", "storage/reports")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()

# Automatically adjust debug flag in production if not explicitly overridden
if settings.ENVIRONMENT == "production" and os.getenv("DEBUG") is None:
    settings.DEBUG = False
