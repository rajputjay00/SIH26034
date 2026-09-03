import os
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.core.database import get_db
from app.schemas.pydantic_models import HealthResponse

router = APIRouter()

@router.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """
    Detailed system health check verifying API execution, database connectivity,
    and storage accessibility without exposing internal secrets or filesystem details.
    """
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    storage_writable = False
    try:
        test_dir = settings.STORAGE_EVIDENCE_PATH
        if os.path.exists(test_dir) and os.access(test_dir, os.W_OK):
            storage_writable = True
    except Exception:
        storage_writable = False

    overall_status = "HEALTHY" if (db_connected and storage_writable) else "DEGRADED"

    return {
        "status": overall_status,
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "database_connected": db_connected,
        "storage_ready": storage_writable,
        "server_time": datetime.now(timezone.utc).isoformat(),
        "subsystems": {
            "rule_engine": "READY",
            "ocr_engine": "READY",
            "audit_chain": "ONLINE"
        }
    }
