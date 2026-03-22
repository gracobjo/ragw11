"""
Base de conocimiento: ejemplos de prompts para el RAG.
Cada categoría contiene (objetivo, prompt) para guiar al usuario.
"""
from __future__ import annotations

EJEMPLOS_PROMPTS: dict[str, list[tuple[str, str]]] = {
    "Resúmenes": [
        (
            "Resumen general por documento",
            "Usando solo el contenido de los documentos indexados, haz un resumen de cada documento en máximo 100 líneas. Indica el nombre del documento y luego su resumen.",
        ),
        (
            "Resumen breve",
            "Resume en 10-15 líneas el contenido del documento sobre el tema principal.",
        ),
        (
            "Ideas principales por tema",
            "Extrae las ideas principales de los documentos indexados y organízalas por temas o secciones.",
        ),
    ],
    "Preguntas concretas": [
        (
            "Definiciones",
            "Según los documentos, ¿qué es [término o concepto]? Explica con las palabras del texto.",
        ),
        (
            "Procedimientos",
            "¿Qué pasos se describen para [tarea] en los documentos indexados?",
        ),
        (
            "Parámetros y valores",
            "¿Qué valores se recomiendan para [parámetro] según la documentación?",
        ),
        (
            "Comparaciones",
            "¿Cuáles son las diferencias entre [A] y [B] según los documentos?",
        ),
    ],
    "Extracción de información": [
        (
            "Lista de requisitos",
            "Lista todos los requisitos o dependencias mencionados en los documentos indexados.",
        ),
        (
            "Tabla de parámetros",
            "Extrae en formato tabla los parámetros de configuración (nombre, valor, descripción) que aparecen en los documentos.",
        ),
        (
            "Fragmentos de código",
            "¿Qué fragmentos de código o ejemplos se incluyen en los documentos? Cítalos.",
        ),
    ],
    "Análisis": [
        (
            "Análisis técnico",
            "Analiza la arquitectura descrita en los documentos: componentes, flujo de datos y tecnologías usadas.",
        ),
        (
            "Ventajas y limitaciones",
            "¿Qué ventajas y limitaciones se mencionan de [tecnología o enfoque] en la documentación?",
        ),
        (
            "Relaciones entre conceptos",
            "¿Cómo se relacionan [concepto A], [concepto B] y [concepto C] según los documentos?",
        ),
    ],
    "Creación de contenidos": [
        (
            "Guía rápida",
            "Redacta una guía rápida de [tema] basada exclusivamente en los documentos indexados.",
        ),
        (
            "Preguntas frecuentes",
            "Genera 5 preguntas frecuentes con sus respuestas a partir del contenido de los documentos.",
        ),
        (
            "Glosario",
            "Extrae los términos técnicos definidos en los documentos y crea un glosario breve (término: definición).",
        ),
    ],
    "Fórmula general": [
        (
            "Plantilla recomendada",
            "[Instrucción] + [ámbito: documentos indexados] + [formato si aplica]\n\n"
            "Ejemplo: Según los documentos indexados, explica en 3 párrafos cómo funciona [concepto]. "
            "Usa únicamente la información del contexto.",
        ),
    ],
    "Prompts a evitar": [
        (
            "Evitar: genérico",
            "❌ Resumen esto\n"
            "✅ Según el contenido de los documentos indexados, resume las ideas principales en un máximo de 20 líneas.",
        ),
        (
            "Evitar: sin contexto",
            "❌ ¿Qué es NotebookLM?\n"
            "✅ En los documentos indexados, ¿se menciona NotebookLM u otras herramientas similares? Si es así, resume lo que dicen.",
        ),
        (
            "Evitar: preguntas vagas",
            "❌ Cuéntame más\n"
            "✅ De los documentos indexados, extrae la información sobre [tema específico] y organízala por secciones.",
        ),
        (
            "Evitar: mezclar fuentes",
            "❌ Haz un resumen general de IA\n"
            "✅ Usando solo los documentos indexados, resume el contenido relacionado con la inteligencia artificial.",
        ),
    ],
}


def obtener_categorias() -> list[str]:
    """Devuelve las categorías disponibles."""
    return list(EJEMPLOS_PROMPTS.keys())
