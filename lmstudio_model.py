"""Resolución del id de modelo cargado en LM Studio (OpenAI-compatible)."""
from __future__ import annotations

import os

from config import LM_STUDIO_API_KEY, LM_STUDIO_BASE_URL, LM_STUDIO_MODEL


def resolve_lm_studio_model_id() -> str:
    if LM_STUDIO_MODEL:
        return LM_STUDIO_MODEL
    try:
        from openai import OpenAI

        # Sin timeout, si LM Studio no está activo el cliente puede bloquear mucho tiempo
        # y Streamlit se queda en pantalla en blanco hasta que expira la conexión.
        client = OpenAI(
            base_url=LM_STUDIO_BASE_URL,
            api_key=LM_STUDIO_API_KEY or "lm-studio",
            timeout=5.0,
            max_retries=0,
        )
        models = client.models.list()
        if models.data:
            return models.data[0].id
    except Exception:
        pass
    return os.getenv("LM_STUDIO_MODEL_FALLBACK", "local-model")
