"""
Apartado C: agente ReAct con tools (RAG + fecha + estadística del índice).
"""
from __future__ import annotations

from datetime import datetime

from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate
try:
    from langchain import hub
except ImportError:
    hub = None  # type: ignore

from config import AGENT_MAX_ITERATIONS, CHROMA_DIR, ensure_dirs
from ingest import get_embeddings
from langchain_chroma import Chroma
from llm_provider import get_chat_llm
from rag_chain import consultar


@tool
def consultar_documentos(pregunta: str) -> str:
    """Consulta la base de conocimiento interna (documentos indexados) para responder con contexto recuperado."""
    resultado = consultar(pregunta)
    return str(resultado.get("answer", ""))


@tool
def obtener_fecha_actual(dummy: str = "") -> str:
    """Devuelve la fecha y hora actual del sistema."""
    return datetime.now().strftime("%A, %d de %B de %Y – %H:%M")


@tool
def estadistica_indice(dummy: str = "") -> str:
    """Indica cuántos chunks hay almacenados en ChromaDB (base vectorial local)."""
    ensure_dirs()
    try:
        emb = get_embeddings()
        db = Chroma(
            persist_directory=str(CHROMA_DIR),
            embedding_function=emb,
        )
        col = db._collection
        n = col.count()
        return f"Chunks indexados en la base local: {n}"
    except Exception as e:
        return f"No se pudo leer el índice: {e}"


REACT_PROMPT_FALLBACK = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""


def _load_react_prompt():
    if hub is not None:
        try:
            return hub.pull("hwchase17/react")
        except Exception:
            pass
    return PromptTemplate.from_template(REACT_PROMPT_FALLBACK)


def crear_agente(verbose: bool = False) -> AgentExecutor:
    llm = get_chat_llm()
    tools = [consultar_documentos, obtener_fecha_actual, estadistica_indice]
    prompt = _load_react_prompt()
    agente = create_react_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agente,
        tools=tools,
        verbose=verbose,
        max_iterations=AGENT_MAX_ITERATIONS,
        handle_parsing_errors=True,
    )


if __name__ == "__main__":
    executor = crear_agente(verbose=True)
    print("Escribe 'salir' o 'exit' para terminar.\n")
    while True:
        pregunta = input("\nTú: ").strip()
        if pregunta.lower() in ("salir", "exit", ""):
            break
        respuesta = executor.invoke({"input": pregunta})
        print(f"\nAsistente: {respuesta['output']}")
