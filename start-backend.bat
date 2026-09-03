@echo off
title LegalMetriX Backend API
cd /d "%~dp0backend"
echo ====================================================
echo Starting LegalMetriX FastAPI Backend on port 8000...
echo ====================================================
if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
) else (
    python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
)
pause
