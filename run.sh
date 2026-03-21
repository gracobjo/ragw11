#!/usr/bin/env bash
# Ejecuta la aplicación RAG local en Ubuntu/Linux.
# Uso: ./run.sh   o   bash run.sh

cd "$(dirname "$0")"

if [ -z "$VIRTUAL_ENV" ] && [ -d ".venv" ]; then
    source .venv/bin/activate
fi

streamlit run app.py --server.headless true "$@"
