"""
Apartado B: cadena RAG (retriever + LLM local).
LM Studio (API OpenAI) o GGUF vía llama-cpp; ver llm_provider.py.
RetrievalQA (stuff) en langchain_classic, compatible con LangChain 1.x.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from langchain_classic.chains import RetrievalQA
from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from config import CHROMA_DIR, RETRIEVER_K, ensure_dirs
from ingest import get_embeddings
from llm_provider import get_chat_llm

PROMPT_TEMPLATE = """Eres un asistente experto. Usa ÚNICAMENTE el siguiente contexto para responder.
Si la respuesta no está en el contexto, di exactamente: No tengo información sobre eso.

Contexto:
{context}

Pregunta: {question}
Respuesta:"""


_vectorstore: Chroma | None = None


def get_vectorstore() -> Chroma:
    """Vectorstore en caché para evitar recargar Chroma en cada petición."""
    global _vectorstore
    if _vectorstore is None:
        ensure_dirs()
        _vectorstore = Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=get_embeddings(),
        )
    return _vectorstore


def get_retriever(k: int | None = None, source_filter: str | None = None):
    kwargs: dict = {"k": k or RETRIEVER_K}
    if source_filter:
        kwargs["filter"] = {"source": source_filter}
    return get_vectorstore().as_retriever(search_kwargs=kwargs)


def listar_fuentes_indexadas() -> list[str]:
    """Devuelve las rutas únicas de documentos indexados en Chroma."""
    try:
        vs = get_vectorstore()
        col = vs._collection
        res = col.get(include=["metadatas"], limit=100_000)
        metas = res.get("metadatas") or []
        seen: set[str] = set()
        for m in metas:
            src = (m or {}).get("source", "")
            if src and src not in seen:
                seen.add(src)
        return sorted(seen)
    except Exception:
        return []


def crear_cadena_rag(k: int | None = None, source_filter: str | None = None):
    llm = get_chat_llm()
    retriever = get_retriever(k=k, source_filter=source_filter)
    prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=PROMPT_TEMPLATE,
    )
    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt},
    )


def consultar(
    pregunta: str, k: int | None = None, source_filter: str | None = None
) -> dict[str, Any]:
    cadena = crear_cadena_rag(k=k, source_filter=source_filter)
    out = cadena.invoke({"query": pregunta})
    docs = out.get("source_documents") or []
    return {
        "answer": out.get("result", ""),
        "source_documents": docs,
    }


def consultar_streaming(
    pregunta: str, k: int | None = None, source_filter: str | None = None
) -> tuple[Iterator[str], list]:
    """
    Versión con streaming para el chat. Devuelve (generador, source_documents).
    Uso: text = st.write_stream(gen); sources = docs
    """
    from langchain_core.prompts import ChatPromptTemplate

    retriever = get_retriever(k=k, source_filter=source_filter)
    docs = list(retriever.invoke(pregunta))
    context = "\n\n".join(d.page_content for d in docs)

    llm = get_chat_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Usa ÚNICAMENTE el contexto. Si no está, di: No tengo información sobre eso."),
        ("human", "Contexto:\n{context}\n\nPregunta: {question}\nRespuesta:"),
    ])
    chain = prompt | llm

    def _gen():
        try:
            for chunk in chain.stream({"context": context, "question": pregunta}):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content
        except Exception:
            # Fallback sin streaming
            r = consultar(pregunta, k=k, source_filter=source_filter)
            yield r.get("answer", "")

    return _gen(), docs


# Prompts específicos para generación tipo NotebookLM
INFORME_INSTRUCCION = """Genera un informe estructurado sobre el siguiente tema, usando ÚNICAMENTE la información del contexto.

Tema: {tema}

Estructura obligatoria en Markdown:
- # Título del informe
- ## Introducción (2-3 párrafos)
- ## Desarrollo (varias ## secciones según el contenido)
- ## Conclusiones
- Referencias a las fuentes si es relevante

Sé detallado y preciso. Si el contexto no contiene información suficiente, indica qué aspectos no pudiste cubrir."""

PRESENTACION_INSTRUCCION = """Genera el contenido para una presentación sobre el siguiente tema, usando ÚNICAMENTE la información del contexto.

Tema: {tema}
Número de diapositivas: {num_slides}

Formato: para cada diapositiva escribe exactamente:
---
## Slide [N]: [Título]
- Punto 1
- Punto 2
- ...

Sé conciso (3-5 puntos por slide). La primera debe ser portada, la última conclusiones o cierre. Si el contexto no basta, indica qué falta."""


def generar_informe(
    tema: str, k: int = 8, source_filter: str | None = None
) -> dict[str, Any]:
    """Genera un informe estructurado a partir de los documentos indexados."""
    instruccion = INFORME_INSTRUCCION.format(tema=tema.strip())
    return consultar(instruccion, k=k, source_filter=source_filter)


def generar_presentacion(
    tema: str,
    num_slides: int = 8,
    k: int = 8,
    source_filter: str | None = None,
) -> dict[str, Any]:
    """Genera el contenido para una presentación a partir de los documentos indexados."""
    num_slides = max(3, min(20, num_slides))
    instruccion = PRESENTACION_INSTRUCCION.format(
        tema=tema.strip(), num_slides=num_slides
    )
    return consultar(instruccion, k=k, source_filter=source_filter)


CUESTIONARIO_INSTRUCCION = """Genera un cuestionario de {num_preguntas} preguntas tipo test basado ÚNICAMENTE en el contexto.

REGLAS:
- Cada pregunta debe tener exactamente 4 opciones (A, B, C, D).
- Solo UNA opción es la correcta.
- Incluye una explicación breve de por qué la respuesta correcta es la adecuada (para mostrar si el usuario falla).
- Las preguntas deben cubrir distintos aspectos del documento, sin repetirse.

Formato de salida: responde ÚNICAMENTE con un JSON válido, sin texto antes ni después. La estructura debe ser exactamente:

[
  {{"pregunta": "texto de la pregunta", "opciones": ["opción A", "opción B", "opción C", "opción D"], "correcta": 0, "explicacion": "por qué A es correcta"}},
  ...
]

Donde "correcta" es el índice (0-3) de la opción correcta. Usa únicamente la información del contexto."""


def generar_cuestionario(
    num_preguntas: int = 100,
    k: int = 50,
    source_filter: str | None = None,
) -> dict[str, Any]:
    """
    Genera un cuestionario de preguntas tipo test a partir del documento indexado.
    Si source_filter está definido, solo usa chunks de ese documento.
    """
    num_preguntas = max(5, min(100, num_preguntas))
    instruccion = CUESTIONARIO_INSTRUCCION.format(num_preguntas=num_preguntas)
    return consultar(instruccion, k=k, source_filter=source_filter)


if __name__ == "__main__":
    q = input("Pregunta: ").strip()
    if q:
        r = consultar(q)
        print("\nRespuesta:\n", r["answer"])
        print("\nFuentes:")
        for d in r["source_documents"]:
            src = d.metadata.get("source", "?")
            print(" -", src)
