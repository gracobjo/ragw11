"""
Interfaz Streamlit: chat RAG / agente, subida de documentos e indexación.
Ejecutar: streamlit run app.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import streamlit as st

IS_WINDOWS = sys.platform == "win32"

from config import (
    DOCS_DIR,
    GGUF_MODEL_PATH,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    UPLOADS_DIR,
    ensure_dirs,
)
from ingest import index_documents_safe, ingest_folder, load_file
from llm_provider import is_ollama_backend, is_llamacpp_backend, set_ollama_model
from rag_chain import (
    consultar,
    consultar_streaming,
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


def main() -> None:
    st.set_page_config(
        page_title="RAG local",
        page_icon="📚",
        layout="wide",
    )
    ensure_dirs()

    st.title("RAG local (Ollama)")
    st.caption(
        "Documentos en disco + ChromaDB. LLM vía Ollama (por defecto), llama-cpp o LM Studio."
    )

    with st.sidebar:
        st.subheader("Conexión LLM")
        if is_ollama_backend():
            try:
                from ollama_utils import listar_modelos_ollama
                modelos = listar_modelos_ollama()
            except Exception:
                modelos = []
            modelo_default = OLLAMA_MODEL or "qwen2.5:7b"
            if modelos:
                idx = modelos.index(modelo_default) if modelo_default in modelos else 0
                modelo_elegido = st.selectbox(
                    "Modelo Ollama",
                    modelos,
                    index=idx if idx < len(modelos) else 0,
                    key="ollama_model_select",
                )
                set_ollama_model(modelo_elegido)
                st.success(f"Modo **Ollama** — `{modelo_elegido}`")
            else:
                set_ollama_model(modelo_default)
                st.success(f"Modo **Ollama** — `{modelo_default}`")
            st.caption(f"{OLLAMA_BASE_URL}")
        elif is_llamacpp_backend():
            gguf = Path(GGUF_MODEL_PATH).expanduser() if GGUF_MODEL_PATH else None
            if gguf and gguf.is_file():
                st.success(f"Modo **llamacpp** — `{gguf.name}`")
                st.caption(str(gguf.resolve()))
            else:
                st.error(
                    "Modo `LLM_BACKEND=llamacpp`: define `GGUF_MODEL_PATH` en `.env` "
                    "con la ruta completa al fichero `.gguf`."
                )
        else:
            try:
                from lmstudio_model import resolve_lm_studio_model_id
                mid = resolve_lm_studio_model_id()
                st.success(f"Modo **LM Studio** — modelo: `{mid}`")
            except Exception as e:
                st.warning(
                    f"LM Studio no responde: {e}. Usa `LLM_BACKEND=ollama` en `.env`."
                )

        st.subheader("Modo de respuesta")
        modo = st.radio(
            "Cómo responder",
            ("RAG directo (recomendado)", "Agente ReAct + tools"),
            help="RAG directo siempre recupera contexto. El agente elige tools (fecha, estadística, RAG).",
        )

        st.subheader("Documentos")
        st.caption(
            f"Copia de trabajo del proyecto: `{DOCS_DIR}`. "
            "Puedes añadir PDF desde cualquier carpeta de tu equipo con el selector de abajo."
        )

        st.markdown(
            "**Selector de archivos (recomendado)** — Pulsa *Examinar archivos*; "
            "se abre el diálogo nativo del sistema para elegir uno o varios PDF (también TXT o DOCX). "
            "No hace falta moverlos a mano a `docs/`."
        )
        uploaded = st.file_uploader(
            "Examinar archivos",
            type=["pdf", "txt", "docx"],
            accept_multiple_files=True,
            help="Navega por tus carpetas para elegir los archivos.",
            key="rag_file_uploader",
        )

        if st.button("Indexar los archivos seleccionados arriba", type="primary"):
            if not uploaded:
                st.warning("Primero elige archivos con «Examinar archivos» (o arrástralos a la zona).")
            else:
                paths: list[Path] = []
                for uf in uploaded:
                    dest = UPLOADS_DIR / uf.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(uf.getvalue())
                    paths.append(dest)
                all_docs = []
                for p in paths:
                    all_docs.extend(load_file(p))
                with st.spinner("Indexando…"):
                    index_documents_safe(all_docs)
                nombres = ", ".join(p.name for p in paths)
                st.success(f"Indexados {len(paths)} archivo(s): {nombres}")

        with st.expander("Indexar una carpeta por ruta (solo en este ordenador)"):
            st.caption(
                "Si ejecutas Streamlit aquí mismo, puedes indexar todos los PDF/TXT/DOCX "
                "de una carpeta sin subirlos uno a uno. Pega la ruta que ves en la barra de direcciones del Explorador."
            )
            _placeholder = (
                r"Ej.: C:\Users\tu_usuario\Documents\MisPDFs"
                if IS_WINDOWS
                else "Ej.: /home/tu_usuario/Documentos/MisPDFs"
            )
            carpeta_txt = st.text_input(
                "Ruta de la carpeta",
                placeholder=_placeholder,
                key="folder_path_input",
                label_visibility="visible",
            )
            if st.button("Indexar todo el contenido de esa carpeta"):
                raw = (carpeta_txt or "").strip().strip('"')
                if not raw:
                    st.warning("Escribe o pega una ruta de carpeta.")
                else:
                    carpeta = Path(raw).expanduser().resolve()
                    if not carpeta.is_dir():
                        st.error(
                            f"No se encuentra la carpeta o no es accesible: `{carpeta}`"
                        )
                    else:
                        with st.spinner(f"Indexando {carpeta}…"):
                            ingest_folder(carpeta)
                        st.success(f"Carpeta indexada: `{carpeta}`")

        if st.button("Reindexar solo la carpeta docs/ del proyecto"):
            with st.spinner("Indexando docs/…"):
                ingest_folder(DOCS_DIR)
            st.success("Carpeta `docs/` del proyecto indexada.")

        st.divider()
        st.markdown(
            "**Ollama:** solo hace falta tenerlo en ejecución una vez (escritorio o terminal). "
            "Elige el modelo en el selector superior. Luego indexa documentos y pregunta en el chat."
        )

    tab_chat, tab_informes, tab_presentaciones, tab_cuestionario = st.tabs([
        "💬 Chat",
        "📄 Informes",
        "🖥️ Presentaciones",
        "📝 Cuestionario",
    ])

    with tab_chat:
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for m in st.session_state.messages:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
                if m.get("sources"):
                    with st.expander("Fuentes recuperadas"):
                        for s in m["sources"]:
                            st.code(s, language=None)

        prompt = st.chat_input("Escribe tu pregunta…")
        if prompt:
            from agent import crear_agente

            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                sources: list[str] = []
                if modo.startswith("RAG"):
                    try:
                        gen, docs = consultar_streaming(prompt, k=4)
                        text = st.write_stream(gen)
                        sources = _format_sources(docs)
                    except Exception as e:
                        text = f"Error en la cadena RAG: {e}"
                else:
                    with st.spinner("Ejecutando agente…"):
                        try:
                            ex = crear_agente(verbose=False)
                            out = ex.invoke({"input": prompt})
                            text = str(out.get("output", ""))
                        except Exception as e:
                            text = f"Error en el agente: {e}"

                st.markdown(text or "_(sin respuesta)_")
                if sources:
                    with st.expander("Fuentes recuperadas"):
                        for s in sources:
                            st.code(s, language=None)

            st.session_state.messages.append(
                {"role": "assistant", "content": text, "sources": sources}
            )

    with tab_informes:
        st.markdown("Genera un **informe estructurado** a partir de tus documentos indexados.")
        tema_informe = st.text_input(
            "Tema del informe",
            placeholder="Ej.: Resumen de los procedimientos de vacaciones",
            key="tema_informe",
        )
        if st.button("Generar informe", type="primary", key="btn_informe"):
            if not tema_informe.strip():
                st.warning("Escribe un tema para el informe.")
            else:
                with st.spinner("Generando informe…"):
                    try:
                        r = generar_informe(tema_informe.strip(), k=8)
                        st.session_state.ultimo_informe = r["answer"]
                        st.session_state.fuentes_informe = _format_sources(
                            r.get("source_documents")
                        )
                    except Exception as e:
                        st.error(f"Error: {e}")
        if "ultimo_informe" in st.session_state and st.session_state.ultimo_informe:
            st.markdown(st.session_state.ultimo_informe)
            st.download_button(
                "Descargar informe (.md)",
                data=st.session_state.ultimo_informe,
                file_name="informe.md",
                mime="text/markdown",
                key="dl_informe",
            )
            if st.session_state.get("fuentes_informe"):
                with st.expander("Fuentes"):
                    for s in st.session_state.fuentes_informe:
                        st.caption(s)

    with tab_presentaciones:
        st.markdown("Genera el **contenido para una presentación** (diapositivas) a partir de tus documentos.")
        tema_pres = st.text_input(
            "Tema de la presentación",
            placeholder="Ej.: Manual de acceso al sistema",
            key="tema_pres",
        )
        num_slides = st.slider("Número de diapositivas", 3, 20, 8, key="num_slides")
        if st.button("Generar presentación", type="primary", key="btn_pres"):
            if not tema_pres.strip():
                st.warning("Escribe un tema para la presentación.")
            else:
                with st.spinner("Generando presentación…"):
                    try:
                        r = generar_presentacion(
                            tema_pres.strip(), num_slides=num_slides, k=8
                        )
                        st.session_state.ultima_presentacion = r["answer"]
                        st.session_state.fuentes_presentacion = _format_sources(
                            r.get("source_documents")
                        )
                    except Exception as e:
                        st.error(f"Error: {e}")
        if (
            "ultima_presentacion" in st.session_state
            and st.session_state.ultima_presentacion
        ):
            st.markdown(st.session_state.ultima_presentacion)
            st.download_button(
                "Descargar presentación (.md)",
                data=st.session_state.ultima_presentacion,
                file_name="presentacion.md",
                mime="text/markdown",
                key="dl_pres",
            )
            if st.session_state.get("fuentes_presentacion"):
                with st.expander("Fuentes"):
                    for s in st.session_state.fuentes_presentacion:
                        st.caption(s)
            st.caption(
                "Copia el contenido en Google Slides, PowerPoint o una herramienta de presentaciones."
            )

    with tab_cuestionario:
        st.markdown(
            "Genera un **cuestionario de tipo test** (respuesta múltiple, una correcta) "
            "a partir del documento que selecciones. Si fallas, se muestra la respuesta correcta y la explicación."
        )
        fuentes = listar_fuentes_indexadas()
        if not fuentes:
            st.warning("No hay documentos indexados. Sube e indexa al menos un PDF en la barra lateral.")
        else:
            opciones_fuente = ["(Todos los documentos)"] + [Path(f).name for f in fuentes]
            fuente_idx = st.selectbox(
                "Documento base del cuestionario",
                range(len(opciones_fuente)),
                format_func=lambda i: opciones_fuente[i],
                key="cuestionario_fuente",
            )
            source_filter = None if fuente_idx == 0 else fuentes[fuente_idx - 1]
            num_preguntas = st.slider(
                "Número de preguntas",
                10,
                100,
                100,
                step=10,
                key="cuestionario_num",
            )
            if st.button("Generar cuestionario", type="primary", key="btn_cuestionario"):
                with st.spinner("Generando preguntas (puede tardar varios minutos)…"):
                    try:
                        r = generar_cuestionario(
                            num_preguntas=num_preguntas,
                            k=50,
                            source_filter=source_filter,
                        )
                        raw = r.get("answer", "").strip()
                        # Extraer JSON si viene envuelto en ```json ... ```
                        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
                        if m:
                            raw = m.group(1).strip()
                        preguntas = json.loads(raw)
                        if isinstance(preguntas, list) and all(
                            isinstance(p, dict) and "pregunta" in p and "opciones" in p
                            for p in preguntas
                        ):
                            st.session_state.cuestionario_preguntas = preguntas
                            st.session_state.cuestionario_respuestas = {}
                        else:
                            st.error("El modelo no devolvió una lista de preguntas válida.")
                    except json.JSONDecodeError as e:
                        st.error(f"Error al parsear el JSON: {e}. Prueba con menos preguntas o otro modelo.")
                    except Exception as e:
                        st.error(f"Error: {e}")

        if "cuestionario_preguntas" in st.session_state and st.session_state.cuestionario_preguntas:
            preguntas = st.session_state.cuestionario_preguntas
            respuestas = st.session_state.setdefault("cuestionario_respuestas", {})
            for i, p in enumerate(preguntas):
                q = p.get("pregunta", "?")
                opciones = p.get("opciones", [])
                correcta = p.get("correcta", 0)
                explicacion = p.get("explicacion", "")
                if len(opciones) < 2:
                    continue
                key = f"quiz_{i}"
                ya_respondida = key in respuestas
                elegida = st.radio(
                    f"**{i+1}. {q}**",
                    range(len(opciones)),
                    format_func=lambda j, o=opciones: o[j],
                    key=key,
                    disabled=ya_respondida,
                )
                if not ya_respondida and elegida is not None:
                    es_correcta = elegida == correcta
                    respuestas[key] = (elegida, es_correcta)
                if key in respuestas:
                    _, es_correcta = respuestas[key]
                    if not es_correcta:
                        st.error(
                            f"❌ Incorrecto. La respuesta correcta es: **{opciones[correcta]}**. "
                            f"*{explicacion}*"
                        )
                    else:
                        st.success("✓ Correcto")
            st.caption(f"Respondidas: {len(respuestas)} / {len(preguntas)}")


if __name__ == "__main__":
    main()
