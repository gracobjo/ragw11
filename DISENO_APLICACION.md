# Diseño de la Aplicación RAG Local

**Versión:** 1.0  
**Plataformas:** Windows 11, Ubuntu  
**Público:** Desarrolladores y usuarios finales

---

## 1. Arquitectura general

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INTERFAZ (Streamlit)                         │
│  app.py ─────────────────────────────────────────────────────────── │
│  • Barra lateral (LLM, documentos)                                   │
│  • Pestañas: Chat | Informes | Presentaciones | Cuestionario         │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  ingest.py    │    │   rag_chain.py   │    │    agent.py      │
│  Carga e      │    │   Cadena RAG,    │    │  Agente ReAct    │
│  indexación   │    │   generación     │    │  con tools       │
└───────┬───────┘    └────────┬─────────┘    └────────┬─────────┘
        │                     │                       │
        │             ┌───────┴───────┐               │
        │             │ llm_provider  │               │
        │             │ Ollama / LM   │◄──────────────┘
        │             │ Studio / GGUF │
        │             └───────────────┘
        │                     │
        ▼                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ChromaDB (chroma_db/)     │  Documentos (docs/, docs/uploads/)      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Componentes del backend

| Módulo | Función |
|--------|---------|
| **config.py** | Rutas, variables de entorno, parámetros RAG (chunk size, k, temperatura). |
| **ingest.py** | Carga PDF/TXT/DOCX, fragmenta en chunks, genera embeddings e indexa en ChromaDB. |
| **rag_chain.py** | Vectorstore, retriever, cadena RAG (RetrievalQA), streaming, generación de informes, presentaciones y cuestionarios. |
| **llm_provider.py** | Crea la instancia del LLM según el backend configurado (Ollama, LM Studio, llama-cpp). |
| **ollama_utils.py** | Lista los modelos Ollama disponibles vía API. |
| **agent.py** | Agente ReAct con herramientas: consultar documentos, fecha actual, estadística del índice. |
| **api.py** | API REST FastAPI: consultas, indexación, informes, presentaciones, cuestionarios. Documentación Swagger en `/docs`. |
| **prompts_ejemplos.py** | Base de conocimiento de prompts de ejemplo por categoría (resúmenes, preguntas concretas, extracción, análisis, etc.). Se muestra en el Chat como expander para que el usuario copie o use plantillas. |

### 2.1 Componentes técnicos: PyMuPDF, MMR y parámetros del retriever

| Componente | Para qué sirve |
|------------|----------------|
| **PyMuPDF** (`pymupdf` en `requirements.txt`) | Librería para extraer el **texto completo** de los PDF al indexar. Sustituye a `pypdf` como loader principal porque obtiene mejor el cuerpo del documento (párrafos, listas) y no solo metadatos o encabezados. Sin una buena extracción, el RAG respondería con información limitada. |
| **MMR** (Maximal Marginal Relevance) | Algoritmo de recuperación que combina **relevancia** (chunks similares a la pregunta) con **diversidad** (chunks de distintos documentos). Sin MMR, los k chunks más similares pueden venir todos del mismo documento; con MMR se favorece incluir varios documentos en cada respuesta. Configurable con `RETRIEVER_USE_MMR`, `RETRIEVER_K` y `RETRIEVER_FETCH_K` en `.env`. |
| **RETRIEVER_K** (por defecto 8) | Número de chunks que se recuperan por consulta. Mayor k = más contexto para el LLM y más probabilidad de abarcar varios documentos. |
| **RETRIEVER_FETCH_K** | Tamaño del pool de candidatos antes de aplicar MMR. Debe ser mayor que k para que MMR pueda elegir chunks diversos. |

---

## 3. API REST (Swagger)

La API permite que otras aplicaciones consuman las funcionalidades RAG sin usar la interfaz Streamlit.

| Recurso | Descripción |
|---------|-------------|
| **Arranque** | `uvicorn api:app --reload --host 0.0.0.0 --port 8000` o `run_api.bat` / `run_api.sh` |
| **Swagger UI** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **OpenAPI JSON** | http://localhost:8000/openapi.json |

### Endpoints principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | /health | Comprueba que la API está operativa |
| GET | /api/sources | Lista documentos indexados |
| POST | /api/query | Consulta RAG (pregunta, k, source_filter) |
| POST | /api/index/folder | Indexa carpeta por ruta |
| POST | /api/index/upload | Sube e indexa archivos |
| POST | /api/index/docs | Reindexa docs/ |
| POST | /api/informe | Genera informe |
| POST | /api/presentacion | Genera presentación |
| POST | /api/cuestionario | Genera cuestionario |
| GET | /api/models | Lista modelos Ollama |
| POST | /api/models/select | Selecciona modelo Ollama |

---

## 4. Componentes del frontend

La interfaz está organizada en una **barra lateral** y **cuatro pestañas** principales.

---

### 4.1 Barra lateral

#### 3.1.1 Conexión LLM

| Elemento | Para desarrolladores | Para usuarios |
|----------|----------------------|---------------|
| **Modelo Ollama** (selectbox) | Muestra los modelos devueltos por `listar_modelos_ollama()` y llama a `set_ollama_model()`. | Elige qué modelo de Ollama quieres usar para todas las respuestas. Debe estar Ollama en ejecución. |
| **Modo llamacpp / LM Studio** | Muestra la ruta del GGUF o el modelo LM Studio resuelto. | Solo si has configurado `LLM_BACKEND` en `.env`; indica qué backend está activo. |
| **URL / caption** | Muestra `OLLAMA_BASE_URL` u otra URL del backend. | Indica a qué servidor se conecta la aplicación. |

**Qué hacer (usuario):** Asegúrate de tener Ollama ejecutándose. Si tienes modelos GGUF de LM Studio, crea un Modelfile por modelo y ejecuta `ollama create nombre -f Modelfile`. Selecciona el modelo con el que quieres trabajar.

---

#### 4.1.2 Modo de respuesta

| Elemento | Para desarrolladores | Para usuarios |
|----------|----------------------|---------------|
| **RAG directo (recomendado)** | Usa `consultar_streaming()`: recupera chunks, construye contexto y genera respuesta con streaming. | Responde siempre usando solo el contenido de tus documentos. |
| **Agente ReAct + tools** | Usa `crear_agente()`: el agente decide cuándo consultar documentos, obtener la fecha o estadísticas. | El asistente puede consultar documentos, decir la fecha o cuántos chunks hay indexados, según la pregunta. |

**Qué hacer (usuario):** Usa “RAG directo” para preguntas sobre tus documentos; “Agente ReAct” si quieres que también use fecha o estadísticas.

---

#### 3.1.3 Documentos

| Elemento | Para desarrolladores | Para usuarios |
|----------|----------------------|---------------|
| **Examinar archivos** (file_uploader) | Sube archivos a `UPLOADS_DIR`, los carga con `load_file()` y los indexa con `index_documents_safe()`. | Selecciona PDF, TXT o DOCX desde tu ordenador. |
| **Indexar los archivos seleccionados** (botón) | Dispara la indexación de los archivos subidos. | Después de elegir archivos, pulsa este botón para añadirlos a la base de conocimiento. |
| **Indexar una carpeta por ruta** (expander) | Usa `ingest_folder()` con la ruta introducida. `Path.expanduser().resolve()` hace la ruta multiplataforma. | Si ejecutas la app en tu PC, escribe la ruta completa de una carpeta (p. ej. `C:\Users\...` en Windows o `/home/usuario/...` en Ubuntu) y pulsa el botón para indexar todo su contenido. |
| **Reindexar solo docs/** (botón) | Ejecuta `ingest_folder(DOCS_DIR)`. | Reindexa la carpeta `docs/` del proyecto (archivos que hayas copiado ahí manualmente). |

**Qué hacer (usuario):**  
1. Sube archivos o indica una carpeta.  
2. Pulsa el botón correspondiente para indexar.  
3. Espera el mensaje de éxito antes de hacer preguntas.

---

### 4.2 Pestaña Chat

| Elemento | Para desarrolladores | Para usuarios |
|----------|----------------------|---------------|
| **Base de conocimiento: Ejemplos de prompts** (expander) | Muestra `EJEMPLOS_PROMPTS` de `prompts_ejemplos.py` por categoría. Cada ejemplo incluye botón «Usar este prompt» que precarga el texto antes de enviar. | Ayuda a formular preguntas efectivas al RAG (resúmenes, preguntas concretas, extracción, análisis, prompts a evitar, etc.). |
| **Historial de mensajes** | `st.session_state.messages` guarda `{role, content, sources}`. Se renderiza con `st.chat_message`. | Muestra la conversación que mantienes con el asistente. |
| **Chat input** | Al enviar, según el modo llama a `consultar_streaming()` o `crear_agente().invoke()`. | Escribe tu pregunta y pulsa Enter. |
| **Fuentes recuperadas** (expander) | Lista las rutas de `source_documents` formateadas con `_format_sources()`. Con MMR, suelen provenir de varios documentos distintos. | Permite ver de qué documentos se ha extraído la información usada en la respuesta. |

**Qué hacer (usuario):** Escribe preguntas sobre tus documentos. Revisa “Fuentes recuperadas” si quieres saber de dónde sale la información.

---

### 3.3 Pestaña Informes

| Elemento | Para desarrolladores | Para usuarios |
|----------|----------------------|---------------|
| **Tema del informe** (text_input) | Se pasa a `generar_informe(tema, k=8)`. | Define el tema sobre el que quieres el informe. |
| **Generar informe** (botón) | Ejecuta la cadena RAG con el prompt de informe y guarda el resultado en `st.session_state.ultimo_informe`. | Pulsa para generar el informe. |
| **Contenido del informe** | Se muestra en Markdown con `st.markdown()`. | Lee el informe generado. |
| **Descargar informe (.md)** | `st.download_button` con el texto del informe. | Descarga el informe en formato Markdown. |
| **Fuentes** (expander) | Muestra las fuentes usadas para el informe. | Indica qué documentos se han usado. |

**Qué hacer (usuario):** Escribe un tema, pulsa “Generar informe”, revisa el resultado y descárgalo si lo necesitas.

---

### 4.4 Pestaña Presentaciones

| Elemento | Para desarrolladores | Para usuarios |
|----------|----------------------|---------------|
| **Tema de la presentación** (text_input) | Se pasa a `generar_presentacion(tema, num_slides, k=8)`. | Indica el tema de la presentación. |
| **Número de diapositivas** (slider) | Controla `num_slides` (3–20). | Elige cuántas diapositivas quieres. |
| **Generar presentación** (botón) | Genera el contenido en formato “Slide N” y lo guarda en sesión. | Pulsa para generar el contenido. |
| **Contenido / Descargar** | Igual que en Informes. | Copia el contenido a Google Slides, PowerPoint, etc., o descárgalo. |

**Qué hacer (usuario):** Define tema y número de diapositivas, genera la presentación y copia o descarga el resultado.

---

### 3.5 Pestaña Cuestionario

| Elemento | Para desarrolladores | Para usuarios |
|----------|----------------------|---------------|
| **Documento base** (selectbox) | Lista `listar_fuentes_indexadas()`. Si eliges uno, se usa `source_filter` en `generar_cuestionario()`. | Permite generar el test solo de un documento o de todos. |
| **Número de preguntas** (slider) | Valor 10–100 (múltiplos de 10) pasado a `generar_cuestionario()`. | Elige cuántas preguntas quieres. |
| **Generar cuestionario** (botón) | Llama a `generar_cuestionario()`, parsea el JSON de la respuesta y guarda en `cuestionario_preguntas`. | Pulsa para generar el test. Espera: puede tardar varios minutos. |
| **Preguntas** (radio por pregunta) | Cada pregunta tiene `pregunta`, `opciones`, `correcta` (índice), `explicacion`. Al responder se guarda en `cuestionario_respuestas`. | Responde eligiendo una opción. |
| **Feedback (Correcto / Incorrecto)** | Si `elegida != correcta`, se muestra la respuesta correcta y la explicación. | Si fallas, ves la respuesta correcta y por qué es correcta. |
| **Respondidas: X / Y** | Cuenta las entradas en `cuestionario_respuestas`. | Indica cuántas preguntas llevas respondidas. |

**Qué hacer (usuario):**  
1. Selecciona el documento (o “Todos”).  
2. Elige el número de preguntas.  
3. Genera el cuestionario.  
4. Responde cada pregunta; en las que falles, lee la respuesta correcta y la explicación.

---

## 5. Flujo de trabajo recomendado (usuarios)

Para una guía detallada del usuario (para qué indexamos y procedimiento paso a paso), véase **[docs/MANUAL_USUARIO_RAG.md](docs/MANUAL_USUARIO_RAG.md)**.

1. **Configuración inicial**
   - Instalar Python, dependencias (`pip install -r requirements.txt`) y Ollama.
   - Ejecutar Ollama. Para usar modelos GGUF de LM Studio: crear **un Modelfile por modelo** en la raíz del proyecto y ejecutar `ollama create nombre -f Modelfile` (véase `Modelfile` y `Modelfile.qwen3vl` de ejemplo).
   - Arrancar la aplicación: `streamlit run app.py` (o `./run.sh` en Linux, `run.bat` en Windows).

2. **Indexar documentos**
   - Subir archivos con “Examinar archivos” y pulsar “Indexar los archivos seleccionados”,  
   - O indicar una ruta de carpeta en el expander y pulsar el botón de indexar,  
   - O copiar archivos en `docs/` y pulsar “Reindexar solo docs/”.

3. **Usar las funciones**
   - **Chat:** Escribir preguntas sobre los documentos.
   - **Informes:** Tema → Generar informe → Revisar y descargar.
   - **Presentaciones:** Tema y número de diapositivas → Generar presentación → Copiar o descargar.
   - **Cuestionario:** Documento y número de preguntas → Generar cuestionario → Responder y revisar feedback.

---

## 6. Archivos de configuración

| Archivo | Uso |
|---------|-----|
| **.env** | `LLM_BACKEND`, `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `RETRIEVER_K`, `RETRIEVER_USE_MMR`, `RETRIEVER_FETCH_K`, etc. |
| **requirements.txt** | Dependencias principales. Incluye `pymupdf` para extracción de texto de PDF. |
| **requirements-llamacpp.txt** | Dependencias para modo GGUF/llama-cpp. |
| **run.sh** | Script de arranque en Ubuntu/Linux. |
| **run.bat** | Script de arranque en Windows. |
| **Modelfile**, **Modelfile.xxx** | Configuración de Ollama para importar modelos GGUF. **Se requiere un Modelfile distinto por cada modelo** que se quiera importar desde LM Studio u otra fuente. Cada Modelfile define: `FROM` (ruta al `.gguf`), `TEMPLATE` (formato de chat) y `PARAMETER`. Los modelos visión-lenguaje (VL) con archivo `mmproj` incluyen una segunda línea `FROM` con la ruta al proyector. |

---

## 5.1 Modelos locales: embeddings y LLM

En este proyecto, **«modelos locales»** significa que el modelo **se ejecuta en tu máquina** y sus pesos están **almacenados en tu disco** (descargados o descargables). Hay dos tipos:

### Modelo de embeddings

| Campo | Descripción |
|-------|-------------|
| **Variable** | `EMBEDDING_MODEL` (por defecto: `sentence-transformers/all-MiniLM-L6-v2`) |
| **Función** | Convierte el texto en vectores para la búsqueda semántica en ChromaDB. |
| **Qué significa «local»** | La primera vez que ejecutas la app, `sentence-transformers` descarga el modelo desde Hugging Face (~80 MB) y lo guarda en caché (p. ej. `~/.cache/huggingface/`). A partir de ahí se ejecuta todo en tu PC; no se envían datos a servidores externos. |
| **Qué hacer** | No hace falta nada especial. Si quieres usar otro modelo de embeddings, cámbialo en `.env`. |

### Modelos LLM (generación de respuestas)

Aquí «local» implica que **los pesos del modelo están ya descargados** en tu equipo (o se descargan al usarlo).

| Backend | Cómo se «localizan» los modelos | Qué debe hacer el usuario |
|---------|--------------------------------|---------------------------|
| **Ollama** | Con `ollama pull nombre` o `ollama create nombre -f Modelfile`. Ollama descarga y almacena los modelos. | Descargar o crear modelos con esos comandos. Para GGUF de LM Studio: crear un Modelfile por modelo y ejecutar `ollama create nombre -f Modelfile`. |
| **LM Studio** | Se descargan desde la interfaz de LM Studio; se guardan en `~/.lmstudio/models/` (o similar). | Descargar el modelo en LM Studio y arrancar el servidor local. |
| **llamacpp** | Archivo `.gguf` en disco (descargado con LM Studio, desde Hugging Face, etc.). | Tener el `.gguf` y definir `GGUF_MODEL_PATH` en `.env` con la ruta completa. |

**Resumen:** «Modelos locales» = modelos cuyos pesos están en tu máquina. El de embeddings se descarga automáticamente la primera vez; el LLM lo descargas tú (Ollama, LM Studio) o usas un archivo `.gguf` que ya tengas.

### Uso de GPU (Ubuntu con NVIDIA)

| Componente | Variable | Valor para GPU |
|------------|----------|----------------|
| Embeddings | `EMBEDDING_DEVICE` | `cuda` |
| llamacpp   | `LLAMA_N_GPU_LAYERS` | `-1` (todas las capas en GPU) |
| Ollama     | — | Suele usar la GPU automáticamente si está disponible |

Con `EMBEDDING_DEVICE=cuda` en `.env`, los embeddings se ejecutan en la GPU. Ollama detecta la GPU por sí mismo.

---

## 7. Rutas del proyecto

| Ruta | Contenido |
|------|-----------|
| `docs/` | Documentos base del proyecto. |
| `docs/uploads/` | Archivos subidos desde la interfaz. |
| `chroma_db/` | Base vectorial ChromaDB (persistida). |

---

## 8. Referencias

- Casos de uso y diagramas UML: `CASOS_DE_USO_UML.md`.
- Procedimiento de pruebas: `PROCEDIMIENTO_PRUEBAS.md`.
