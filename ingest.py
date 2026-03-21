"""
Apartado A: carga, chunking e indexación en Chroma (persistido en disco).
Soporta PDF, TXT y DOCX. Uso: `python ingest.py` o funciones desde la app Streamlit.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DOCS_DIR,
    EMBEDDING_DEVICE,
    EMBEDDING_MODEL,
    ensure_dirs,
)


def get_embeddings() -> HuggingFaceEmbeddings:
    kwargs: dict = {"model_name": EMBEDDING_MODEL}
    if EMBEDDING_DEVICE and EMBEDDING_DEVICE != "cpu":
        kwargs["model_kwargs"] = {"device": EMBEDDING_DEVICE}
    return HuggingFaceEmbeddings(**kwargs)


def get_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )


def _normalize_source(path: Path) -> str:
    return str(path.resolve())


def load_file(path: Path) -> list[Document]:
    path = path.resolve()
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        loader = PyPDFLoader(str(path))
    elif suffix == ".txt":
        loader = TextLoader(str(path), encoding="utf-8")
    elif suffix == ".docx":
        loader = Docx2txtLoader(str(path))
    else:
        return []
    docs = loader.load()
    for d in docs:
        d.metadata["source"] = _normalize_source(path)
    return docs


def load_folder(folder: Path) -> list[Document]:
    documentos: list[Document] = []
    for root, _, files in os.walk(folder):
        for name in files:
            p = Path(root) / name
            documentos.extend(load_file(p))
    return documentos


def get_vectorstore() -> Chroma:
    ensure_dirs()
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=get_embeddings(),
    )


def delete_chunks_for_source(vs: Chroma, source: str) -> None:
    """Elimina chunks cuyo metadata['source'] coincide (reindexar sin duplicar)."""
    try:
        col = vs._collection
        res = col.get(where={"source": source})
        ids = res.get("ids") or []
        if ids:
            col.delete(ids=ids)
    except Exception:
        return


def index_documents_safe(documents: list[Document]) -> Chroma:
    """
    Indexa usando add_documents sobre el vectorstore existente,
    eliminando antes los chunks de los mismos ficheros.
    """
    ensure_dirs()
    if not documents:
        print("No hay documentos para indexar.")
        return get_vectorstore()

    splitter = get_splitter()
    chunks = splitter.split_documents(documents)
    embeddings = get_embeddings()

    vs = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
    )
    sources = {d.metadata.get("source", "") for d in documents}
    for s in sources:
        if s:
            delete_chunks_for_source(vs, s)
    if chunks:
        vs.add_documents(chunks)
    print(f"Indexados {len(chunks)} chunks en {CHROMA_DIR}")
    return vs


def ingest_folder(folder: Path | None = None) -> None:
    ensure_dirs()
    folder = folder or DOCS_DIR
    docs = load_folder(folder)
    print(f"Ficheros cargados: {len(docs)} documentos base")
    index_documents_safe(docs)


def ingest_file(path: Path) -> int:
    """Indexa un único fichero. Devuelve número de chunks añadidos."""
    ensure_dirs()
    path = path.resolve()
    docs = load_file(path)
    if not docs:
        return 0
    splitter = get_splitter()
    chunks = splitter.split_documents(docs)
    embeddings = get_embeddings()
    vs = Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=embeddings,
    )
    delete_chunks_for_source(vs, str(path))
    if chunks:
        vs.add_documents(chunks)
    print(f"Indexados {len(chunks)} chunks de {path.name}")
    return len(chunks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Indexar docs/ en Chroma")
    parser.add_argument(
        "--dir",
        type=Path,
        default=DOCS_DIR,
        help="Carpeta a indexar (por defecto ./docs)",
    )
    args = parser.parse_args()
    ingest_folder(args.dir)
