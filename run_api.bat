@echo off
REM Ejecuta la API REST del proyecto RAG (FastAPI + Swagger).
REM Uso: run_api.bat   o   doble clic en run_api.bat
REM Documentación: http://localhost:8000/docs

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

uvicorn api:app --reload --host 0.0.0.0 --port 8000 %*
