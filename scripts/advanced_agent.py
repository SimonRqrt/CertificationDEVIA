import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import operator
import sqlite3
from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver

from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage, AnyMessage
from langchain_core.messages.ai import AIMessage

from langchain_community.chat_models import ChatOllama
from langchain_core.tools import tool
from rich import print as rprint

from src.db_manager import create_db_engine, create_tables


@tool
def dummy_weather_tool(location: str) -> str:
    """Renvoie la météo simulée pour un lieu donné."""
    weather_data = {
        "Paris": "☁️ 12°C, nuageux, vent modéré",
        "Lille": "🌤️ 15°C, ensoleillé, vent léger",
        "Marseille": "☀️ 20°C, grand soleil, pas de vent"
    }
    return weather_data.get(location, f"Météo inconnue pour {location}")


@tool
def get_user_metrics_from_db(user_id: int = 1) -> str:
    """Récupère les métriques de l'utilisateur depuis la base SQLite."""
    engine = create_db_engine()
    tables = create_tables(engine)

    with engine.connect() as conn:
        stmt = tables["metrics"].select().where(tables["metrics"].c.user_id == user_id)
        result = conn.execute(stmt).fetchone()

        if not result:
            return "Aucune métrique trouvée pour cet utilisateur."

        metrics = dict(result)
        readable = "\n".join([
            f"- VMA : {metrics.get('vma_kmh')} km/h",
            f"- VO2max estimé : {metrics.get('vo2max_estime')}",
            f"- Charge (7j) : {metrics.get('charge_7j')}",
            f"- Charge (28j) : {metrics.get('charge_28j')}",
            f"- Fatigue : {metrics.get('fatigue')}",
            f"- Forme : {metrics.get('forme')}",
            f"- Ratio endurance : {metrics.get('ratio_endurance')}",
            f"- Prédiction 10k : {metrics.get('prediction_10k_min')} minutes"
        ])

        return f"Métriques de l'utilisateur {user_id} :\n{readable}"

# === Enregistrement des outils ===
tools = [dummy_weather_tool, get_user_metrics_from_db]

# === Structure d’état du graphe ===
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

# === LangChain Model ===
llm = ChatOllama(model="llama3")
conn = sqlite3.connect(":memory:", check_same_thread=False)  # ou "data/agent_memory.sqlite" si tu veux persister
memory = SqliteSaver(conn)

# === Fonctions du graphe ===
def call_llm(state: AgentState) -> AgentState:
    system_msg = SystemMessage(content="Tu es un assistant sportif intelligent. Utilise les outils si besoin (données utilisateur, météo, etc).")
    full_history = [system_msg] + state["messages"]
    message = llm.invoke(full_history)
    return {"messages": [message]}

def needs_tool(state: AgentState) -> bool:
    return len(state["messages"][-1].tool_calls) > 0

def use_tool(state: AgentState) -> AgentState:
    tool_calls = state["messages"][-1].tool_calls
    results = []

    for call in tool_calls:
        tool = next((t for t in tools if t.name == call["name"]), None)
        if tool:
            rprint(f"[bold cyan]🔧 Utilisation de l'outil : {tool.name}[/bold cyan]")
            tool_result = tool.invoke(call["args"])
            results.append(
                ToolMessage(
                    tool_call_id=call["id"],
                    name=call["name"],
                    content=str(tool_result)
                )
            )
    return {"messages": results}

# === Construction du graphe LangGraph ===
graph_builder = StateGraph(AgentState)
graph_builder.add_node("llm", call_llm)
graph_builder.add_node("action", use_tool)
graph_builder.add_conditional_edges("llm", needs_tool, {True: "action", False: END})
graph_builder.add_edge("action", "llm")
graph_builder.set_entry_point("llm")
graph = graph_builder.compile(checkpointer=memory)

# === Boucle interactive CLI ===
if __name__ == "__main__":
    rprint("[bold yellow]🎽 Assistant sportif intelligent prêt ! (Tape 'quit' pour sortir)[/bold yellow]")
    while True:
        user_input = input("🧠 Question : ")
        if user_input.lower() in ("quit", "exit", "q"):
            rprint("[bold green]À bientôt ![/bold green]")
            break

        for event in graph.stream(
            {"messages": [HumanMessage(content=user_input)]},
            {"configurable": {"thread_id": "user-thread-001"}}
        ):
            for step in event.values():
                message = step["messages"][-1]
                if isinstance(message, AIMessage):
                    rprint(f"\n🤖 [green]{message.content}[/green]")
