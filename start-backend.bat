@echo off
echo Starting Aarogya AI Backend...
cd /d "%~dp0backend"
call .venv\Scripts\activate.bat
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
