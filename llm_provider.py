"""
Proveedor único de chat LLM: Ollama (por defecto), LM Studio o GGUF vía llama-cpp.
"""
from __future__ import annotations

import os
from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel

from config import (
    GGUF_MODEL_PATH,
    LLM_BACKEND,
    LLM_TEMPERATURE,
    LM_STUDIO_API_KEY,
    LM_STUDIO_BASE_URL,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
)

_llm_singleton: BaseChatModel | None = None
_llm_model_used: str | None = None
_current_ollama_model: str | None = None


def set_ollama_model(model: str | None) -> None:
    """
    Establece el modelo Ollama a usar en las siguientes llamadas a get_chat_llm().
    Útil cuando el frontend permite elegir modelo. Llama reset_llm_cache() si cambias de modelo.
    """
    global _current_ollama_model
    _current_ollama_model = model


def is_ollama_backend() -> bool:
    return LLM_BACKEND == "ollama"


def is_llamacpp_backend() -> bool:
    return LLM_BACKEND in ("llamacpp", "gguf", "local")


def reset_llm_cache() -> None:
    """Útil para tests o tras cambiar .env (no usado por defecto en Streamlit)."""
    global _llm_singleton, _llm_model_used
    _llm_singleton = None
    _llm_model_used = None


def get_chat_llm(model: str | None = None) -> BaseChatModel:
    """
    Devuelve la instancia de LLM. Para Ollama, usa `model`, o el de set_ollama_model(), o OLLAMA_MODEL.
    Al cambiar el modelo se invalida la caché.
    """
    global _llm_singleton, _llm_model_used
    if is_ollama_backend() and model is None and _current_ollama_model:
        model = _current_ollama_model
    effective_model = model if model else (OLLAMA_MODEL or "qwen2.5:7b")
    if _llm_singleton is None or _llm_model_used != effective_model:
        _llm_singleton = _build_chat_llm(model=effective_model)
        _llm_model_used = effective_model
    return _llm_singleton


def _build_chat_llm(model: str | None = None) -> BaseChatModel:
    if is_ollama_backend():
        return _build_ollama(model=model)
    if is_llamacpp_backend():
        return _build_llama_cpp()
    return _build_lm_studio()


def _build_ollama(model: str | None = None) -> BaseChatModel:
    from langchain_openai import ChatOpenAI

    model = model or OLLAMA_MODEL or "qwen2.5:7b"
    return ChatOpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama",
        model=model,
        temperature=LLM_TEMPERATURE,
        timeout=OLLAMA_TIMEOUT,
        max_retries=0,
    )


def _build_lm_studio() -> BaseChatModel:
    from langchain_openai import ChatOpenAI

    from lmstudio_model import resolve_lm_studio_model_id

    return ChatOpenAI(
        base_url=LM_STUDIO_BASE_URL,
        api_key=LM_STUDIO_API_KEY,
        model=resolve_lm_studio_model_id(),
        temperature=LLM_TEMPERATURE,
        timeout=120.0,
        max_retries=0,
    )


def _build_llama_cpp() -> BaseChatModel:
    try:
        from langchain_community.chat_models import ChatLlamaCpp
    except ImportError as e:
        raise ImportError(
            "Modo llamacpp: instala llama-cpp-python con: "
            "pip install -r requirements-llamacpp.txt"
        ) from e

    if not GGUF_MODEL_PATH:
        raise ValueError(
            "Define GGUF_MODEL_PATH en .env con la ruta al fichero .gguf "
            "(por ejemplo el que descargaste para LM Studio)."
        )
    path = Path(GGUF_MODEL_PATH).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"No existe el fichero GGUF: {path}")

    n_ctx = int(os.getenv("LLAMA_N_CTX", "4096"))
    n_gpu_layers = int(os.getenv("LLAMA_N_GPU_LAYERS", "0"))
    max_tokens = int(os.getenv("LLAMA_MAX_TOKENS", "512"))

    return ChatLlamaCpp(
        model_path=str(path),
        temperature=LLM_TEMPERATURE,
        n_ctx=n_ctx,
        n_gpu_layers=n_gpu_layers,
        max_tokens=max_tokens,
        verbose=os.getenv("LLAMA_VERBOSE", "").lower() in ("1", "true", "yes"),
    )
