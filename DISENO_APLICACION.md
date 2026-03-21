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

---

## 3. Componentes del frontend

La interfaz está organizada en una **barra lateral** y **cuatro pestañas** principales.

---

### 3.1 Barra lateral

#### 3.1.1 Conexión LLM

| Elemento | Para desarrolladores | Para usuarios |
|----------|----------------------|---------------|
| **Modelo Ollama** (selectbox) | Muestra los modelos devueltos por `listar_modelos_ollama()` y llama a `set_ollama_model()`. | Elige qué modelo de Ollama quieres usar para todas las respuestas. Debe estar Ollama en ejecución. |
| **Modo llamacpp / LM Studio** | Muestra la ruta del GGUF o el modelo LM Studio resuelto. | Solo si has configurado `LLM_BACKEND` en `.env`; indica qué backend está activo. |
| **URL / caption** | Muestra `OLLAMA_BASE_URL` u otra URL del backend. | Indica a qué servidor se conecta la aplicación. |

**Qué hacer (usuario):** Asegúrate de tener Ollama ejecutándose. Si tienes modelos GGUF de LM Studio, crea un Modelfile por modelo y ejecuta `ollama create nombre -f Modelfile`. Selecciona el modelo con el que quieres trabajar.

---

#### 3.1.2 Modo de respuesta

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

### 3.2 Pestaña Chat

| Elemento | Para desarrolladores | Para usuarios |
|----------|----------------------|---------------|
| **Historial de mensajes** | `st.session_state.messages` guarda `{role, content, sources}`. Se renderiza con `st.chat_message`. | Muestra la conversación que mantienes con el asistente. |
| **Chat input** | Al enviar, según el modo llama a `consultar_streaming()` o `crear_agente().invoke()`. | Escribe tu pregunta y pulsa Enter. |
| **Fuentes recuperadas** (expander) | Lista las rutas de `source_documents` formateadas con `_format_sources()`. | Permite ver de qué documentos se ha extraído la información usada en la respuesta. |

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

### 3.4 Pestaña Presentaciones

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

## 4. Flujo de trabajo recomendado (usuarios)

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

## 5. Archivos de configuración

| Archivo | Uso |
|---------|-----|
| **.env** | `LLM_BACKEND`, `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, etc. |
| **requirements.txt** | Dependencias principales. |
| **requirements-llamacpp.txt** | Dependencias para modo GGUF/llama-cpp. |
| **run.sh** | Script de arranque en Ubuntu/Linux. |
| **run.bat** | Script de arranque en Windows. |
| **Modelfile**, **Modelfile.xxx** | Configuración de Ollama para importar modelos GGUF. **Se requiere un Modelfile distinto por cada modelo** que se quiera importar desde LM Studio u otra fuente. Cada Modelfile define: `FROM` (ruta al `.gguf`), `TEMPLATE` (formato de chat) y `PARAMETER`. Los modelos visión-lenguaje (VL) con archivo `mmproj` incluyen una segunda línea `FROM` con la ruta al proyector. |

---

## 6. Rutas del proyecto

| Ruta | Contenido |
|------|-----------|
| `docs/` | Documentos base del proyecto. |
| `docs/uploads/` | Archivos subidos desde la interfaz. |
| `chroma_db/` | Base vectorial ChromaDB (persistida). |

---

## 7. Referencias

- Casos de uso y diagramas UML: `CASOS_DE_USO_UML.md`.
