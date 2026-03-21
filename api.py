"""
API REST para el sistema RAG local.
Documentación Swagger: /docs  |  ReDoc: /redoc  |  OpenAPI JSON: /openapi.json

Ejecutar: uvicorn api:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import DOCS_DIR, UPLOADS_DIR, ensure_dirs
from ingest import index_documents_safe, ingest_folder, load_file, load_folder
from llm_provider import is_ollama_backend, set_ollama_model
from rag_chain import (
    consultar,
    generar_cuestionario,
    generar_informe,
    generar_presentacion,
    listar_fuentes_indexadas,
)


def _format_sources(source_documents) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for d in source_documents or []:
        src = (d.metadata or {}).get("source", "?")
        if src not in seen:
            seen.add(src)
            out.append(src)
    return out


app = FastAPI(
    title="RAG Local API",
    description="API REST para consultar documentos, generar informes, presentaciones y cuestionarios usando RAG local (Ollama, LM Studio o llamacpp).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Schemas Pydantic ---


class QueryRequest(BaseModel):
    """Petición de consulta RAG."""

    pregunta: str = Field(..., description="Pregunta a responder con el contexto de los documentos")
    k: int | None = Field(default=None, description="Número de chunks a recuperar (por defecto: config)")
    source_filter: str | None = Field(default=None, description="Ruta del documento para filtrar (opcional)")


class QueryResponse(BaseModel):
    """Respuesta de consulta RAG."""

    answer: str = Field(..., description="Respuesta generada")
    sources: list[str] = Field(default_factory=list, description="Rutas de los documentos usados como contexto")


class IndexFolderRequest(BaseModel):
    """Petición para indexar una carpeta."""

    path: str = Field(..., description="Ruta absoluta de la carpeta a indexar")


class IndexResponse(BaseModel):
    """Respuesta de indexación."""

    chunks_indexados: int = Field(..., description="Número de chunks indexados")
    mensaje: str = Field(..., description="Mensaje descriptivo")


class InformeRequest(BaseModel):
    """Petición para generar un informe."""

    tema: str = Field(..., description="Tema del informe")
    k: int = Field(default=8, ge=1, le=50)
    source_filter: str | None = None


class PresentacionRequest(BaseModel):
    """Petición para generar una presentación."""

    tema: str = Field(..., description="Tema de la presentación")
    num_slides: int = Field(default=8, ge=3, le=20)
    k: int = Field(default=8, ge=1, le=50)
    source_filter: str | None = None


class CuestionarioRequest(BaseModel):
    """Petición para generar un cuestionario."""

    num_preguntas: int = Field(default=20, ge=5, le=100)
    source_filter: str | None = None


class CuestionarioResponse(BaseModel):
    """Respuesta con preguntas del cuestionario."""

    preguntas: list[dict[str, Any]] = Field(..., description="Lista de preguntas con opciones, correcta y explicación")
    sources: list[str] = Field(default_factory=list)


class ModelSelectRequest(BaseModel):
    """Petición para cambiar el modelo Ollama (solo si backend=ollama)."""

    model: str = Field(..., description="Nombre del modelo Ollama a usar")


# --- Endpoints ---


@app.get("/health")
def health():
    """Comprueba que la API está operativa."""
    return {"status": "ok"}


@app.get("/api/sources")
def get_sources():
    """
    Devuelve la lista de rutas de documentos indexados en ChromaDB.
    Útil para saber qué documentos están disponibles para consultas.
    """
    try:
        sources = listar_fuentes_indexadas()
        return {"sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query", response_model=QueryResponse)
def post_query(req: QueryRequest):
    """
    Consulta el sistema RAG con una pregunta.
    Recupera el contexto relevante de los documentos indexados y genera una respuesta.
    """
    try:
        r = consultar(
            pregunta=req.pregunta,
            k=req.k,
            source_filter=req.source_filter,
        )
        sources = _format_sources(r.get("source_documents"))
        return QueryResponse(answer=r.get("answer", ""), sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/index/folder", response_model=IndexResponse)
def index_folder(req: IndexFolderRequest):
    """
    Indexa todos los PDF, TXT y DOCX de una carpeta.
    La ruta debe ser absoluta y accesible desde el servidor.
    """
    try:
        path = Path(req.path.strip().strip('"')).expanduser().resolve()
        if not path.is_dir():
            raise HTTPException(status_code=400, detail=f"Carpeta no encontrada: {path}")
        ensure_dirs()
        docs = load_folder(path)
        if not docs:
            return IndexResponse(chunks_indexados=0, mensaje="No se encontraron PDF, TXT o DOCX en la carpeta")
        index_documents_safe(docs)
        return IndexResponse(chunks_indexados=len(docs), mensaje=f"Indexada carpeta: {path}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/index/upload", response_model=IndexResponse)
async def index_upload(files: list[UploadFile] = File(...)):
    """
    Sube uno o más archivos (PDF, TXT, DOCX) y los indexa.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No se enviaron archivos")
    ensure_dirs()
    paths: list[Path] = []
    for uf in files:
        suffix = Path(uf.filename or "").suffix.lower()
        if suffix not in (".pdf", ".txt", ".docx"):
            continue
        dest = UPLOADS_DIR / (uf.filename or "upload")
        dest.parent.mkdir(parents=True, exist_ok=True)
        content = await uf.read()
        dest.write_bytes(content)
        paths.append(dest)
    if not paths:
        raise HTTPException(status_code=400, detail="Ningún archivo era PDF, TXT o DOCX")
    all_docs = []
    for p in paths:
        all_docs.extend(load_file(p))
    index_documents_safe(all_docs)
    return IndexResponse(
        chunks_indexados=len(all_docs),
        mensaje=f"Indexados {len(paths)} archivo(s): {', '.join(p.name for p in paths)}",
    )


@app.post("/api/index/docs")
def index_docs_folder():
    """
    Reindexa la carpeta docs/ del proyecto.
    """
    try:
        ensure_dirs()
        ingest_folder(DOCS_DIR)
        return IndexResponse(chunks_indexados=0, mensaje="Carpeta docs/ reindexada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/informe")
def post_informe(req: InformeRequest):
    """
    Genera un informe estructurado en Markdown sobre el tema indicado.
    """
    try:
        r = generar_informe(
            tema=req.tema,
            k=req.k,
            source_filter=req.source_filter,
        )
        sources = _format_sources(r.get("source_documents"))
        return {"answer": r.get("answer", ""), "sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/presentacion")
def post_presentacion(req: PresentacionRequest):
    """
    Genera el contenido de una presentación (diapositivas) en Markdown.
    """
    try:
        r = generar_presentacion(
            tema=req.tema,
            num_slides=req.num_slides,
            k=req.k,
            source_filter=req.source_filter,
        )
        sources = _format_sources(r.get("source_documents"))
        return {"answer": r.get("answer", ""), "sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cuestionario", response_model=CuestionarioResponse)
def post_cuestionario(req: CuestionarioRequest):
    """
    Genera un cuestionario tipo test (preguntas de respuesta múltiple).
    Devuelve una lista de preguntas con opciones, índice de la correcta y explicación.
    """
    try:
        r = generar_cuestionario(
            num_preguntas=req.num_preguntas,
            k=50,
            source_filter=req.source_filter,
        )
        raw = r.get("answer", "").strip()
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
        if m:
            raw = m.group(1).strip()
        try:
            preguntas = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=500, detail=f"El modelo no devolvió JSON válido: {exc}")
        if not isinstance(preguntas, list) or not all(
            isinstance(p, dict) and "pregunta" in p and "opciones" in p for p in preguntas
        ):
            raise HTTPException(status_code=500, detail="Formato de preguntas inválido")
        sources = _format_sources(r.get("source_documents"))
        return CuestionarioResponse(preguntas=preguntas, sources=sources)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models")
def get_models():
    """
    Devuelve la lista de modelos Ollama disponibles (solo si LLM_BACKEND=ollama).
    """
    if not is_ollama_backend():
        return {"models": [], "message": "Solo disponible con Ollama como backend"}
    try:
        from ollama_utils import listar_modelos_ollama
        models = listar_modelos_ollama()
        return {"models": models}
    except Exception as e:
        return {"models": [], "error": str(e)}


@app.post("/api/models/select")
def select_model(req: ModelSelectRequest):
    """
    Establece el modelo Ollama a usar en las siguientes peticiones (solo si LLM_BACKEND=ollama).
    """
    if not is_ollama_backend():
        raise HTTPException(status_code=400, detail="Solo disponible con Ollama como backend")
    set_ollama_model(req.model)
    return {"selected": req.model}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
