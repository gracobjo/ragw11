# Manual del usuario — Aplicación RAG Local

**Destinatarios:** Usuarios finales que consultan documentos, generan informes, presentaciones o cuestionarios.

---

## 1. ¿Para qué indexamos documentos?

Indexar documentos es **el paso previo obligatorio** para poder usar el chat, los informes, las presentaciones y los cuestionarios.

Al indexar:

1. El sistema lee el **texto completo** de tus PDF, TXT y DOCX (no solo títulos ni metadatos).
2. Divide cada documento en fragmentos (chunks) y genera representaciones numéricas (embeddings).
3. Guarda todo en una base vectorial (ChromaDB) en la carpeta `chroma_db/` del proyecto.

Esa base vectorial es la **base de conocimiento** sobre la que el sistema responde. Sin documentos indexados, el RAG no tiene contenido del que extraer información.

| Si indexas…              | El sistema podrá…                                                       |
|--------------------------|-------------------------------------------------------------------------|
| Manuales, apuntes, PDFs  | Responder preguntas, resumir, extraer procedimientos y conceptos        |
| Documentación técnica    | Generar guías rápidas, FAQ, glosarios                                   |
| Varios documentos        | Comparar información, generar informes y presentaciones transversales   |

**Importante:** Si modificas o sustituyes documentos, debes **reindexar** para que los cambios se reflejen en las respuestas.

**Fuentes recuperadas:** En cada respuesta se muestran los documentos de los que se extrajo información. El sistema usa MMR (Maximum Marginal Relevance) para incluir chunks de distintos documentos cuando tiene sentido, no solo los más similares a la pregunta.

---

## 2. Procedimiento para usar la aplicación

### Paso 0 — Requisitos previos

- Python y dependencias instaladas (`pip install -r requirements.txt`).
- Ollama ejecutándose (o LM Studio / modo llamacpp, según tu configuración).
- Aplicación arrancada: `streamlit run app.py` o doble clic en `run.bat` / `run.sh`.

---

### Paso 1 — Indexar documentos

Tienes **tres formas** de añadir documentos a la base de conocimiento:

| Método                         | Pasos                                                                 |
|--------------------------------|-----------------------------------------------------------------------|
| **Subir archivos**             | 1. Barra lateral → «Examinar archivos». 2. Selecciona PDF, TXT o DOCX. 3. Pulsa «Indexar los archivos seleccionados arriba». |
| **Indexar carpeta**            | 1. Barra lateral → Expander «Indexar una carpeta por ruta». 2. Escribe la ruta absoluta (ej. `C:\Users\tu_usuario\Documentos\MisPDFs`). 3. Pulsa «Indexar todo el contenido de esa carpeta». |
| **Reindexar docs/**            | 1. Copia tus archivos en la carpeta `docs/` del proyecto. 2. Barra lateral → Pulsa «Reindexar solo la carpeta docs/ del proyecto». |

Espera el mensaje de éxito antes de hacer preguntas. Si cambias o añades documentos, repite el proceso de indexación que corresponda.

---

### Paso 2 — Usar las funciones

| Pestaña           | Qué hacer                                                                 |
|-------------------|---------------------------------------------------------------------------|
| **Chat**          | Escribe preguntas sobre tus documentos. Usa la base de conocimiento de prompts si necesitas ideas. Revisa «Fuentes recuperadas» para ver de qué documentos sale la respuesta. |
| **Informes**      | Indica un tema → Pulsa «Generar informe» → Revisa y descarga el informe en Markdown. |
| **Presentaciones**| Indica tema y número de diapositivas → Pulsa «Generar presentación» → Copia el contenido a Google Slides o PowerPoint. |
| **Cuestionario**  | Opcionalmente selecciona un documento concreto (o «Todos»). Elige número de preguntas → Pulsa «Generar cuestionario» → Responde y revisa el feedback. |

---

### Paso 3 — Modo de respuesta (opcional)

En la barra lateral puedes elegir:

- **RAG directo (recomendado):** Siempre responde usando solo el contenido de tus documentos.
- **Agente ReAct + tools:** Puede además consultar la fecha actual o estadísticas del índice.

---

## 3. Resumen rápido

```
1. Arrancar Ollama (o tu backend LLM)
2. Arrancar la app (streamlit run app.py)
3. Indexar documentos (subir, carpeta o reindexar docs/)
4. Usar Chat, Informes, Presentaciones o Cuestionario
```

---

## 4. Documentación adicional

- **Configuración y requisitos técnicos:** `README.md`, `.env.example`
- **Diseño de la aplicación:** `DISENO_APLICACION.md`
- **Casos de uso y diagramas:** `CASOS_DE_USO_UML.md`
