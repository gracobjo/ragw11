# Procedimiento de Pruebas

**Versión:** 1.0  
**Objetivo:** Validar el funcionamiento de la aplicación sin modificar código salvo que se detecten defectos.

---

## 1. Alcance

Este documento describe el procedimiento de pruebas para el sistema RAG local, tanto **pruebas manuales** (interfaz Streamlit) como **pruebas de API** (endpoints REST). Las pruebas se ejecutan sobre el código existente para verificar que cumple los requisitos.

---

## 2. Precondiciones

Antes de ejecutar las pruebas:

1. **Entorno:** Python 3.10+, dependencias instaladas (`pip install -r requirements.txt`).
2. **Ollama:** Instalado y en ejecución. Al menos un modelo disponible (`ollama list`).
3. **Documentos de prueba:** Al menos un PDF, TXT o DOCX en `docs/` o disponible para subir.
4. **API (opcional):** Si se prueban endpoints REST, arrancar la API con `uvicorn api:app --reload` o `python -m uvicorn api:app`.

---

## 3. Pruebas manuales (Streamlit)

### 3.1 Arranque de la aplicación

| ID | Acción | Resultado esperado |
|----|--------|--------------------|
| P-M-01 | Ejecutar `streamlit run app.py` | La app arranca y abre en el navegador (puerto 8501). |
| P-M-02 | Verificar título "RAG local (Ollama)" | El título se muestra correctamente. |
| P-M-03 | Verificar barra lateral | Aparecen secciones: Conexión LLM, Modo de respuesta, Documentos. |

### 3.2 Conexión LLM

| ID | Acción | Resultado esperado |
|----|--------|--------------------|
| P-M-04 | Con Ollama en ejecución, revisar selector de modelo | Se listan los modelos instalados (p. ej. qwen2.5:7b). |
| P-M-05 | Sin Ollama, revisar selector | Se muestra el modelo por defecto de .env o mensaje de advertencia. |
| P-M-06 | Cambiar modelo en el selector | El modelo seleccionado se refleja en el caption/mensaje de éxito. |

### 3.3 Indexación de documentos

| ID | Acción | Resultado esperado |
|----|--------|--------------------|
| P-M-07 | Subir un PDF con "Examinar archivos" y pulsar "Indexar los archivos seleccionados" | Mensaje de éxito "Indexados 1 archivo(s): nombre.pdf". |
| P-M-08 | Sin seleccionar archivos, pulsar "Indexar los archivos seleccionados" | Mensaje de advertencia. |
| P-M-09 | En el expander, introducir ruta de carpeta con PDFs y pulsar "Indexar todo el contenido" | Mensaje de éxito con la ruta. |
| P-M-10 | Introducir ruta inexistente | Mensaje de error indicando que la carpeta no se encuentra. |
| P-M-11 | Pulsar "Reindexar solo la carpeta docs/" | Mensaje de éxito "Carpeta docs/ del proyecto indexada.". |

### 3.4 Chat (modo RAG directo)

| ID | Acción | Resultado esperado |
|----|--------|--------------------|
| P-M-12 | Seleccionar "RAG directo" y escribir una pregunta sobre el contenido indexado | La respuesta se muestra en streaming y es coherente con los documentos. |
| P-M-13 | Expandir "Fuentes recuperadas" | Se listan rutas de archivos usados como contexto. |
| P-M-14 | Escribir una pregunta totalmente fuera del contexto (ej. "¿Cuál es la capital de Marte?") | La respuesta indica que no tiene información sobre eso. |
| P-M-15 | Sin documentos indexados, escribir una pregunta | Error o mensaje indicando ausencia de contexto. |

### 3.5 Chat (modo Agente ReAct)

| ID | Acción | Resultado esperado |
|----|--------|--------------------|
| P-M-16 | Seleccionar "Agente ReAct + tools" y preguntar "¿Qué fecha es hoy?" | El agente usa la herramienta de fecha y responde con la fecha actual. |
| P-M-17 | Preguntar "¿Cuántos chunks hay indexados?" | El agente devuelve un número coherente. |
| P-M-18 | Preguntar sobre el contenido de los documentos | El agente usa consultar_documentos y responde con contexto. |

### 3.6 Informes

| ID | Acción | Resultado esperado |
|----|--------|--------------------|
| P-M-19 | Ir a pestaña Informes, escribir un tema y pulsar "Generar informe" | Se genera un informe en Markdown con estructura (título, introducción, desarrollo, conclusiones). |
| P-M-20 | Sin escribir tema, pulsar "Generar informe" | Mensaje de advertencia. |
| P-M-21 | Tras generar, pulsar "Descargar informe (.md)" | Se descarga un archivo informe.md. |

### 3.7 Presentaciones

| ID | Acción | Resultado esperado |
|----|--------|--------------------|
| P-M-22 | Ir a pestaña Presentaciones, escribir tema, ajustar diapositivas y pulsar "Generar presentación" | Se genera contenido con formato "Slide N" y puntos. |
| P-M-23 | Descargar presentación | Se descarga presentacion.md. |

### 3.8 Cuestionario

| ID | Acción | Resultado esperado |
|----|--------|--------------------|
| P-M-24 | Ir a pestaña Cuestionario, seleccionar documento, 10 preguntas y pulsar "Generar cuestionario" | Se generan preguntas tipo test con 4 opciones. |
| P-M-25 | Responder correctamente una pregunta | Se muestra "✓ Correcto". |
| P-M-26 | Responder incorrectamente una pregunta | Se muestra la respuesta correcta y la explicación. |
| P-M-27 | Sin documentos indexados, intentar generar cuestionario | Mensaje de advertencia. |

---

## 4. Pruebas de API (REST)

Base URL por defecto: `http://localhost:8000`. Documentación Swagger: `http://localhost:8000/docs`.

### 4.1 Health check

| ID | Método | Endpoint | Resultado esperado |
|----|--------|----------|--------------------|
| P-A-01 | GET | /health | 200, `{"status": "ok"}` |

### 4.2 Fuentes indexadas

| ID | Método | Endpoint | Resultado esperado |
|----|--------|----------|--------------------|
| P-A-02 | GET | /api/sources | 200, lista de rutas de documentos indexados (o lista vacía). |

### 4.3 Consulta (query)

| ID | Método | Endpoint | Body | Resultado esperado |
|----|--------|----------|------|--------------------|
| P-A-03 | POST | /api/query | `{"pregunta": "¿Qué dice el documento?"}` | 200, `answer` y `sources`. |
| P-A-04 | POST | /api/query | `{"pregunta": "test", "k": 2}` | 200, respuesta con hasta 2 fuentes. |

### 4.4 Indexación

| ID | Método | Endpoint | Acción | Resultado esperado |
|----|--------|----------|--------|--------------------|
| P-A-05 | POST | /api/index/folder | `{"path": "ruta/absoluta/docs"}` | 200, `chunks_indexados`. |
| P-A-06 | POST | /api/index/upload | multipart/form-data con archivo PDF | 200, `chunks_indexados`. |

### 4.5 Informe

| ID | Método | Endpoint | Body | Resultado esperado |
|----|--------|----------|------|--------------------|
| P-A-07 | POST | /api/informe | `{"tema": "Resumen del documento"}` | 200, `answer` (Markdown) y `sources`. |

### 4.6 Presentación

| ID | Método | Endpoint | Body | Resultado esperado |
|----|--------|----------|------|--------------------|
| P-A-08 | POST | /api/presentacion | `{"tema": "Tema", "num_slides": 5}` | 200, `answer` (Markdown) y `sources`. |

### 4.7 Cuestionario

| ID | Método | Endpoint | Body | Resultado esperado |
|----|--------|----------|------|--------------------|
| P-A-09 | POST | /api/cuestionario | `{"num_preguntas": 5, "source_filter": null}` | 200, `preguntas` (lista JSON). |

---

## 5. Pruebas automatizadas (pytest)

Para ejecutar pruebas unitarias/integración sin tocar la lógica de negocio:

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

Los tests en `tests/` validan módulos como `config`, `ingest` (carga de documentos) y la API (endpoints). Ver `tests/README.md` para el alcance.

---

## 6. Criterios de aceptación

- **Aprobado:** Todas las pruebas críticas (P-M-01 a P-M-11, P-M-12 a P-M-15, P-A-01 a P-A-04) pasan.
- **Parcial:** Fallos en pruebas secundarias (informes, presentaciones, cuestionario) se documentan como incidencias.
- **No aprobado:** Fallos en arranque, indexación o consulta básica impiden la aceptación.

---

## 7. Registro de incidencias

| Fecha | ID prueba | Descripción del fallo | Severidad |
|-------|-----------|------------------------|-----------|
|       |           |                        |           |

---

## 8. Referencias

- Especificación de requisitos: `ESPECIFICACION_REQUISITOS.md`
- Casos de uso: `CASOS_DE_USO_UML.md`
- API Swagger: `http://localhost:8000/docs` (con la API en ejecución)
