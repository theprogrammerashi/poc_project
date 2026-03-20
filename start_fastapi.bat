@echo off
cd d:\clinicalaudit_rag\backend
call venv\Scripts\activate.bat
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
