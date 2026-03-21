"""Configuración central (URL LM Studio, rutas, hiperparámetros RAG)."""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
UPLOADS_DIR = DOCS_DIR / "uploads"
CHROMA_DIR = BASE_DIR / "chroma_db"

# Compatible con la práctica: servidor OpenAI local
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/")
# Si está vacío, se resuelve el primer modelo vía /v1/models
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "").strip()
LM_STUDIO_API_KEY = os.getenv("OPENAI_API_KEY", "lm-studio")

# LLM: "ollama" (por defecto), "llamacpp" (GGUF directo) o "lmstudio"
LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama").strip().lower()
# Ollama (API en localhost:11434)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b").strip()
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))  # segundos; respuestas largas necesitan más
# Ruta al .gguf cuando LLM_BACKEND=llamacpp
GGUF_MODEL_PATH = os.getenv("GGUF_MODEL_PATH", "").strip()

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
# Dispositivo para embeddings: "cpu" o "cuda" (GPU). En Ubuntu con NVIDIA: EMBEDDING_DEVICE=cuda
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu").strip().lower()

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
RETRIEVER_K = int(os.getenv("RETRIEVER_K", "4"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

# Agente ReAct
AGENT_MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "5"))


def ensure_dirs() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
