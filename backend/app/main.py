import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.api.router import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging_config import setup_logging, logger
from app.utils.errors import LegalMetrixException

# Setup logging
setup_logging()

# Ensure storage directories exist
os.makedirs(settings.STORAGE_EVIDENCE_PATH, exist_ok=True)
os.makedirs(settings.STORAGE_DERIVED_PATH, exist_ok=True)
os.makedirs(settings.STORAGE_REPORTS_PATH, exist_ok=True)

# Create database tables automatically on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    description="Evidence-Oriented Packaged Commodity Compliance & Inspection Decision-Support System",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Permissions-Policy"] = "camera=*, geolocation=()"
    return response

# Mount local storage for serving evidence previews
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# CORS middleware configuration with strict environment origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info(f"System starting in {settings.ENVIRONMENT} mode. CORS Allowed Origins: {settings.ALLOWED_ORIGINS}")


# Custom exception handler for structured application errors
@app.exception_handler(LegalMetrixException)
async def legalmetrix_exception_handler(request: Request, exc: LegalMetrixException):
    logger.warning(f"Handled error [{exc.error_code}]: {exc.detail} on {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.detail,
            "metadata": exc.metadata,
            "path": request.url.path
        }
    )

# Generic fallback exception handler preventing internal traceback leaks
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled system error on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An internal processing error occurred. Please contact the system administrator.",
            "metadata": {},
            "path": request.url.path
        }
    )

# Include API Router
app.include_router(api_router)

@app.get("/")
def root_redirect():
    return {
        "system": settings.APP_NAME,
        "status": "ONLINE",
        "phase": "Phase 7 - Hardening & Security Complete",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

@app.get("/health")
def top_level_health():
    from app.api.v1.health import health_check
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        return health_check(db=db)
    finally:
        db.close()
