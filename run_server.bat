@echo off
echo Starting NER Smart Logistics Platform...
echo Checking virtual environment...
if not exist "venv\Scripts\Activate.ps1" (
    echo Error: Virtual environment not found. Please setup venv first.
    exit /b
)
call venv\Scripts\activate.bat
echo Starting FastAPI Uvicorn Server...
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
