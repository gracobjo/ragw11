#!/usr/bin/env bash
# Ejecuta la API REST del proyecto RAG (FastAPI + Swagger).
# Uso: ./run_api.sh
# Documentación: http://localhost:8000/docs

cd "$(dirname "$0")"

if [ -z "$VIRTUAL_ENV" ] && [ -d ".venv" ]; then
    source .venv/bin/activate
fi

uvicorn api:app --reload --host 0.0.0.0 --port 8000 "$@"
