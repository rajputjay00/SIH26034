@echo off
title LegalMetriX Frontend
cd /d "%~dp0frontend"
echo ====================================================
echo Starting LegalMetriX Next.js Frontend on port 3000...
echo ====================================================
call npm.cmd run dev
pause
