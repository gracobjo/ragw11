# Especificación de Requisitos del Sistema RAG Local

**Versión:** 1.0  
**Plataformas soportadas:** Windows 11, Ubuntu (Linux)  
**Fecha:** Marzo 2025

---

## 1. Introducción

### 1.1 Propósito

Este documento describe los requisitos funcionales y no funcionales del sistema **RAG local** (Retrieval-Augmented Generation). La aplicación permite consultar documentos (PDF, TXT, DOCX) mediante un modelo de lenguaje grande ejecutado en local, combinando búsqueda semántica en una base vectorial con generación de texto.

### 1.2 Alcance

- Indexación de documentos en una base vectorial (ChromaDB).
- Consulta conversacional con contexto recuperado de los documentos.
- Generación de informes, presentaciones y cuestionarios tipo test.
- Interfaz web mediante Streamlit.
- Soporte para múltiples backends de LLM: Ollama, LM Studio, llama-cpp (GGUF).

---

## 2. Requisitos Funcionales

### 2.1 Gestión de documentos


| ID    | Requisito                   | Descripción                                                                                                      |
| ----- | --------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| RF-01 | Carga de archivos           | El sistema debe permitir cargar archivos PDF, TXT y DOCX desde el explorador de archivos nativo del sistema.     |
| RF-02 | Indexación por carpeta      | El sistema debe permitir indexar todos los PDF, TXT y DOCX de una carpeta indicando su ruta absoluta.            |
| RF-03 | Reindexación de docs/       | El sistema debe permitir reindexar la carpeta `docs/` del proyecto con un solo clic.                             |
| RF-04 | Reindexación sin duplicados | Al indexar documentos ya presentes, el sistema debe reemplazar los chunks existentes en lugar de duplicarlos.    |
| RF-05 | Chunking configurable       | El tamaño de chunk (CHUNK_SIZE) y solapamiento (CHUNK_OVERLAP) deben ser configurables vía variables de entorno. |


### 2.2 Chat y consultas


| ID    | Requisito               | Descripción                                                                                                                                        |
| ----- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| RF-06 | Modo RAG directo        | El sistema debe responder preguntas recuperando contexto relevante de la base vectorial y generando respuestas basadas únicamente en ese contexto. |
| RF-07 | Modo agente ReAct       | El sistema debe ofrecer un modo agente con herramientas: consulta RAG, fecha actual y estadística del índice.                                      |
| RF-08 | Streaming de respuestas | En modo RAG directo, las respuestas deben mostrarse en streaming (token a token).                                                                  |
| RF-09 | Fuentes recuperadas     | Cada respuesta debe poder mostrar las fuentes (documentos) de las que se recuperó el contexto.                                                     |
| RF-10 | Contexto limitado       | Si la respuesta no está en el contexto recuperado, el sistema debe indicar explícitamente que no tiene información.                                |


### 2.3 Generación de contenidos


| ID    | Requisito                | Descripción                                                                                                                                    |
| ----- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| RF-11 | Informes estructurados   | El sistema debe generar informes en Markdown con introducción, desarrollo y conclusiones a partir de un tema indicado.                         |
| RF-12 | Presentaciones           | El sistema debe generar el contenido para diapositivas (3–20) con formato Markdown, copiable a Google Slides o PowerPoint.                     |
| RF-13 | Cuestionarios tipo test  | El sistema debe generar cuestionarios de 10–100 preguntas de respuesta múltiple (4 opciones, 1 correcta) basados en un documento seleccionado. |
| RF-14 | Feedback en cuestionario | En cada pregunta fallida, el sistema debe mostrar la respuesta correcta y una explicación.                                                     |
| RF-15 | Filtro por documento     | Informes, presentaciones y cuestionarios deben poder restringirse a un documento concreto o usar todos los indexados.                          |


### 2.4 Configuración de LLM


| ID    | Requisito              | Descripción                                                                                 |
| ----- | ---------------------- | ------------------------------------------------------------------------------------------- |
| RF-16 | Backend Ollama         | El sistema debe poder usar Ollama como proveedor de LLM (por defecto).                      |
| RF-17 | Backend LM Studio      | El sistema debe poder usar LM Studio como proveedor de LLM.                                 |
| RF-18 | Backend llama-cpp      | El sistema debe poder usar un modelo GGUF vía llama-cpp-python.                             |
| RF-19 | Selector de modelo     | En modo Ollama, la interfaz debe mostrar un selector con los modelos instalados localmente. |
| RF-20 | Configuración por .env | URL, modelo por defecto, timeout y temperatura deben ser configurables vía archivo `.env`.  |
| RF-21 | Modelfile por modelo   | Para importar modelos GGUF (p. ej. de LM Studio) a Ollama se requiere **un Modelfile distinto por cada modelo**. Cada Modelfile define la ruta al `.gguf`, la plantilla de chat y los parámetros. Los modelos visión-lenguaje (VL) que incluyen archivo `mmproj` requieren una línea `FROM` adicional en el mismo Modelfile. |
| RF-22 | Ejecución con GPU      | El sistema debe permitir ejecutar los embeddings en GPU (NVIDIA CUDA) mediante la variable `EMBEDDING_DEVICE=cuda`. En modo llamacpp, `LLAMA_N_GPU_LAYERS=-1` permite cargar todas las capas en GPU. Ollama usa la GPU automáticamente si está disponible. |


### 2.5 Interfaz de usuario


| ID    | Requisito                             | Descripción                                                                                        |
| ----- | ------------------------------------- | -------------------------------------------------------------------------------------------------- |
| RF-23 | Interfaz web Streamlit                | La aplicación debe exponer una interfaz web mediante Streamlit.                                    |
| RF-24 | Pestañas                              | La interfaz debe organizar el contenido en pestañas: Chat, Informes, Presentaciones, Cuestionario. |
| RF-25 | Barra lateral                         | La barra lateral debe contener: conexión LLM, modo de respuesta, gestión de documentos.            |
| RF-26 | Descarga de informes y presentaciones | Los informes y presentaciones generados deben poder descargarse en formato Markdown (.md).         |


---

## 3. Requisitos No Funcionales

### 3.1 Plataforma


| ID     | Requisito        | Descripción                                                                            |
| ------ | ---------------- | -------------------------------------------------------------------------------------- |
| RNF-01 | Multiplataforma  | La aplicación debe ejecutarse en Windows 11 y Ubuntu (y compatibles).                  |
| RNF-02 | Rutas portables  | Las rutas de archivos deben manejarse de forma portable (Path, separadores correctos). |
| RNF-03 | Diálogos nativos | El selector de archivos debe usar el diálogo nativo del sistema operativo.             |


### 3.2 Rendimiento


| ID     | Requisito            | Descripción                                                                       |
| ------ | -------------------- | --------------------------------------------------------------------------------- |
| RNF-04 | Caché de vectorstore | El vectorstore debe mantenerse en caché para evitar recargas innecesarias.        |
| RNF-05 | Timeout configurable | Las llamadas a Ollama deben respetar un timeout configurable (por defecto 300 s). |


### 3.3 Seguridad y privacidad


| ID     | Requisito           | Descripción                                                                                                                |
| ------ | ------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| RNF-06 | Ejecución local     | Todo el procesamiento (embeddings, LLM, vectorstore) debe poder ejecutarse en local sin enviar datos a servicios externos. |
| RNF-07 | API keys opcionales | Las API keys (p. ej. OpenAI para LM Studio) deben configurarse en `.env` y no estar hardcodeadas.                          |


### 3.4 Mantenibilidad


| ID     | Requisito                  | Descripción                                                                          |
| ------ | -------------------------- | ------------------------------------------------------------------------------------ |
| RNF-08 | Configuración centralizada | La configuración debe estar centralizada en `config.py` y `.env`.                    |
| RNF-09 | Dependencias versionadas   | Las dependencias deben estar declaradas en `requirements.txt` con versiones mínimas. |


---

## 4. Requisitos del Sistema

### 4.1 Software

- **Python:** 3.10 o superior.
- **Sistema operativo:** Windows 11 o Ubuntu 22.04+ (u otra distro Linux compatible).
- **Ollama** (recomendado): instalado y en ejecución para el backend por defecto.
- **Opcional:** LM Studio o modelo GGUF para alternativas de LLM.

### 4.2 Hardware recomendado

- **RAM:** mínimo 8 GB; recomendado 16 GB o más para modelos grandes.
- **Almacenamiento:** espacio suficiente para el modelo de embeddings (~100 MB) y el modelo LLM (varios GB según el modelo).
- **GPU:** opcional; acelera embeddings y LLM si se configura. En Ubuntu con NVIDIA: `EMBEDDING_DEVICE=cuda` en `.env` para embeddings; Ollama usa la GPU automáticamente; para llamacpp, `LLAMA_N_GPU_LAYERS=-1`. Ver documentación de ejecución con GPU en `README.md` y `DISENO_APLICACION.md`.

### 4.3 Dependencias principales

- LangChain (langchain, langchain-classic, langchain-community, langchain-chroma, langchain-openai).
- ChromaDB para la base vectorial.
- Sentence-transformers para embeddings locales.
- Streamlit para la interfaz web.
- PyPDF, python-docx, docx2txt para carga de documentos.

---

## 5. Glosario


| Término     | Definición                                                                                     |
| ----------- | ---------------------------------------------------------------------------------------------- |
| RAG         | Retrieval-Augmented Generation: combina recuperación de documentos con generación de lenguaje. |
| Modelfile   | Archivo de configuración de Ollama que define un modelo: ruta al GGUF, plantilla de chat y parámetros. Se requiere **uno por cada modelo** a importar. |
| EMBEDDING_DEVICE | Variable de entorno que indica dónde ejecutar los embeddings: `cpu` (por defecto) o `cuda` (GPU NVIDIA). En Ubuntu con GPU, configurar `EMBEDDING_DEVICE=cuda` en `.env` para acelerar la indexación y las consultas. |
| Chunk       | Fragmento de texto en el que se divide un documento para la indexación.                        |
| Embedding   | Representación vectorial de un texto usada para búsqueda semántica.                            |
| Vectorstore | Almacén de vectores (ChromaDB) que permite búsqueda por similitud.                             |
| Retriever   | Componente que recupera los chunks más relevantes para una consulta.                           |
| LLM         | Large Language Model: modelo de lenguaje grande (Ollama, LM Studio, etc.).                     |
| ReAct       | Patrón de agente que alterna razonamiento (Thought) y acciones (Action).                       |


---

## 6. Referencias

- Código fuente: `app.py`, `config.py`, `ingest.py`, `rag_chain.py`, `agent.py`, `llm_provider.py`, `ollama_utils.py`.
- Configuración: `.env`, `requirements.txt`, `requirements-llamacpp.txt`.
- Documentación de diseño: `DISENO_APLICACION.md`.
- Casos de uso y diagramas UML: `CASOS_DE_USO_UML.md`.

