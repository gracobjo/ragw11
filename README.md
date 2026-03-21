# RAG local con LM Studio, LangChain y ChromaDB

Proyecto alineado con la práctica *Sistema RAG Local con LM Studio y LangChain*: ingesta (PDF/TXT/DOCX), embeddings locales (`all-MiniLM-L6-v2`), vectorstore persistente en `./chroma_db`, cadena RAG, agente ReAct con tools y **interfaz Streamlit** para chat, informes, presentaciones y cuestionarios.

**Plataformas soportadas:** Windows 11, Ubuntu (y otras distribuciones Linux compatibles).

## Documentación

- **[ESPECIFICACION_REQUISITOS.md](ESPECIFICACION_REQUISITOS.md)** — Especificación de requisitos funcionales y no funcionales.
- **[DISENO_APLICACION.md](DISENO_APLICACION.md)** — Diseño de la aplicación: componentes del frontend (para desarrolladores y usuarios) y flujo de trabajo.
- **[CASOS_DE_USO_UML.md](CASOS_DE_USO_UML.md)** — Casos de uso detallados y diagramas UML (Mermaid): secuencia, componentes, clases, actividad, estados.

## Requisitos

- Python 3.10+
- **Opción A — Ollama (por defecto):** [Ollama](https://ollama.com) en `localhost:11434`. Ejecuta `ollama run qwen2.5:7b` (o `qwen3.5:9b`, etc.) y deja el servidor activo.
- **Opción B — llama-cpp (GGUF directo):** `LLM_BACKEND=llamacpp`, `GGUF_MODEL_PATH`, y `pip install -r requirements-llamacpp.txt`.
- **Opción C — LM Studio:** `LLM_BACKEND=lmstudio` y servidor en puerto 1234.

## Instalación

Se recomienda un entorno virtual para evitar conflictos con otros paquetes del sistema.

### Windows 11

```powershell
cd ruta\al\proyecto\rag
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Ubuntu / Linux

```bash
cd /ruta/al/proyecto/rag
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Si en Windows aparece un error de **archivo en uso** (`WinError 32`) al instalar `torch` u otros paquetes, cierra procesos que puedan estar bloqueando la carpeta del entorno (otras terminales con `pip`, indexadores, etc.) y vuelve a ejecutar `pip install -r requirements.txt`.

Opcional: crea un archivo `.env` y ajusta variables (`LLM_BACKEND`, `OLLAMA_MODEL`, `LM_STUDIO_BASE_URL`, `GGUF_MODEL_PATH`, etc.).

## Orden de uso

1. **Si usas Ollama:** instálalo, ejecuta `ollama run qwen2.5:7b` y deja el servidor activo. **Si usas llamacpp:** configura `GGUF_MODEL_PATH` en `.env`.
2. Coloca documentos en `docs/` (o súbelos desde la app) y ejecuta la indexación:
   - Línea de comandos: `python ingest.py`
   - O desde Streamlit: **Indexar archivos subidos** / **Reindexar toda la carpeta docs/**
3. Lanza la interfaz:

   - **Windows:** `streamlit run app.py` o doble clic en `run.bat`
   - **Ubuntu/Linux:** `streamlit run app.py` o `./run.sh`

4. (Opcional) Chat solo por terminal con el agente: `python agent.py`

## Scripts

| Archivo       | Descripción |
|---------------|-------------|
| `app.py`      | Streamlit: Chat, Informes, Presentaciones, Cuestionario. |
| `ingest.py`   | Carga documentos, trocea texto e indexa en ChromaDB. |
| `rag_chain.py`| Cadena RAG, streaming, generación de informes, presentaciones y cuestionarios. |
| `llm_provider.py` | Ollama, LM Studio o GGUF local (`llama-cpp`). |
| `agent.py`    | Agente ReAct: consulta RAG, fecha/hora y estadística del índice. |
| `ollama_utils.py` | Lista modelos Ollama disponibles. |
| `run.sh`      | Arranque en Ubuntu/Linux. |
| `run.bat`     | Arranque en Windows. |

## Ejemplos de preguntas (sobre los TXT de ejemplo)

- ¿Con cuántos días de antelación se deben solicitar las vacaciones?
- ¿Qué prioridad debe usarse para incidencias críticas?
- Pregunta esperada fuera del manual: *¿Cuál es la política de seguridad física en instalaciones externas?* → el sistema debe indicar que **no** está en los documentos (según el manual de ejemplo).

## Notas

- **Qwen3-VL** es un modelo multimodal; para RAG solo texto basta con usar el chat de texto. Si el servidor expone un id concreto, puedes fijarlo con `LM_STUDIO_MODEL`.
- Los embeddings se calculan en local con `sentence-transformers` (primera ejecución puede descargar el modelo).
