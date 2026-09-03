@echo off
title LegalMetriX Launcher
echo ====================================================
echo Starting LegalMetriX Full-Stack System...
echo ====================================================
start "LegalMetriX Backend" cmd /k "%~dp0start-backend.bat"
timeout /t 2 /nobreak >nul
start "LegalMetriX Frontend" cmd /k "%~dp0start-frontend.bat"
echo.
echo Both servers have been launched in separate windows!
echo Backend:  http://127.0.0.1:8000 (API Docs: http://127.0.0.1:8000/docs)
echo Frontend: http://localhost:3000
echo.
