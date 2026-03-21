"""
Utilidades para Ollama: listar modelos disponibles.
"""
from __future__ import annotations

import urllib.request
import json
from config import OLLAMA_BASE_URL


def _ollama_base() -> str:
    """URL base de Ollama (sin /v1) para /api/tags."""
    url = OLLAMA_BASE_URL.rstrip("/")
    if url.endswith("/v1"):
        return url[:-3]
    return url


def listar_modelos_ollama() -> list[str]:
    """
    Devuelve la lista de nombres de modelos instalados en Ollama.
    Vacía si Ollama no responde o hay error.
    """
    try:
        base = _ollama_base()
        req = urllib.request.Request(
            f"{base}/api/tags",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        models = data.get("models") or []
        return [m.get("name", "").strip() for m in models if m.get("name")]
    except Exception:
        return []
