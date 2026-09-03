from fastapi import APIRouter
from app.api.v1 import auth, cases, evidence, extraction, findings, audit, reports, health, calibration, dashboard

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(cases.router)
api_router.include_router(dashboard.router)
api_router.include_router(evidence.router)
api_router.include_router(calibration.router)
api_router.include_router(extraction.router)
api_router.include_router(findings.router)
api_router.include_router(audit.router)
api_router.include_router(reports.router)


