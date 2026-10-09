@echo off
title Smart Logistics and Accessibility Intelligence Platform
echo Starting FastAPI Server on http://127.0.0.1:8000 ...
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
pause
