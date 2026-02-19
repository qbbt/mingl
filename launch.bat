@echo off
REM launch.bat - Sentinel-guarded launch script for Decision Wave
echo [LAUNCH] Starting Decision Wave Sentinel...

python sentinel.py
if %ERRORLEVEL% NEQ 0 (
    echo [LAUNCH] ERROR: Sentinel check failed. Aborting launch.
    pause
    exit /b %ERRORLEVEL%
)

echo [LAUNCH] Starting FastAPI Backend on Port 8000...
cd backend
start "Decision Wave Backend" python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

echo [LAUNCH] Waiting for Backend to initialize locking...
python -c "import time; time.sleep(5)"

echo [LAUNCH] Starting Streamlit Data Manager on Port 8001...
cd ..
python -m streamlit run dashboard.py --server.port 8001 --server.headless true
