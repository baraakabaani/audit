@echo off
echo ========================================
echo  Audit Automation System
echo ========================================
echo.

cd /d "%~dp0"

REM Optional: set your Groq API key here for AI classification
REM set GROQ_API_KEY=your_key_here

REM Build the frontend (skip if already built)
if not exist "frontend\dist\index.html" (
    echo Building frontend...
    cd frontend
    call npm install
    call npm run build
    cd ..
)

echo Starting server on http://localhost:8000
echo.
echo Share this address with coworkers on the same network:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set IP=%%a
    goto :found
)
:found
echo   http://%IP: =%.8000
echo.

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
