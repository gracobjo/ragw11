@echo off
REM Ejecuta la aplicación RAG local en Windows.
REM Uso: run.bat   o   doble clic en run.bat

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

streamlit run app.py %*
