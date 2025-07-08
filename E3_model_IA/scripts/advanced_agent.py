import sys
import os
import json
from pathlib import Path
from rich import print as rprint
from typing import Annotated, List, Any

# sys.path.append(str(Path(__file__).resolve().parent.parent))

import operator
from typing_extensions import TypedDict

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage, AnyMessage
from langchain_core.messages.ai import AIMessage

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter

import sqlalchemy as sa
import sqlite3

from E1_gestion_donnees.db_manager import create_db_engine
from src.config import DATABASE_URL, OLLAMA_BASE_URL


# DÉFINIT LA PERSONNALITÉ ET LES RÈGLES DE L'AGENT
SYSTEM_PROMPT = """
Tu es un coach sportif expert, prudent et encourageant, basé sur les données. Ton nom est "Coach AI".

Ta mission est de créer des plans d'entraînement hebdomadaires personnalisés.

**Ton processus DOIT suivre ces étapes :**
1.  **Analyse des données :** Commence TOUJOURS par utiliser l'outil `get_user_metrics_from_db` pour comprendre le profil de l'utilisateur.
2.  **Recherche de connaissances :** Une fois que tu as les métriques (VMA, charge, etc.), utilise l'outil `get_training_knowledge` pour rechercher les principes d'entraînement pertinents dans la base de connaissances. Pose des questions comme "principes d'entraînement pour une VMA de 14 km/h" ou "comment structurer une semaine pour un objectif 10k en 50 minutes".
3.  **Météo (Optionnel) :** Si l'utilisateur le demande, tu peux utiliser l'outil `get_weather_forecast` pour adapter une séance (ex: remplacer une sortie longue sous la pluie par du tapis).
4.  **Synthèse et Plan :** Fais la synthèse de toutes ces informations (données utilisateur, connaissances expertes, météo) pour construire une réponse.

**Format de sortie :**
Quand tu présentes un plan d'entraînement, utilise TOUJOURS le format Markdown suivant :

### Plan d'entraînement pour la semaine du [Date]

| Jour      | Séance                                   | Intensité | Durée Estimée | Objectifs de la séance                       |
|-----------|------------------------------------------|-----------|---------------|----------------------------------------------|
| Lundi     | Repos                                    | -         | -             | Assimilation, prévention des blessures      |
| Mardi     | Footing léger                            | Faible    | 45 min        | Endurance fondamentale                       |
| Mercredi  | VMA : 2x (8x 30/30) à 100% VMA             | Élevée    | 50 min        | Amélioration de la VO2max et de la vitesse |
| Jeudi     | Repos                                    | -         | -             |                                              |
| Vendredi  | Séance de seuil : 3x8 min à 85-90% FCM   | Modérée   | 1h            | Amélioration de l'endurance spécifique      |
| Samedi    | Repos                                    | -         | -             |                                              |
| Dimanche  | Sortie Longue en endurance fondamentale | Faible    | 1h30          | Amélioration de la capacité aérobie         |

**Important :** Sois toujours positif et prudent. Ajoute toujours une note pour rappeler à l'utilisateur d'écouter son corps et de consulter un médecin.
"""


# --- Initialisation des Outils et Services ---

try:
    loader = DirectoryLoader("knowledge_base/", glob="**/*.md", show_progress=True)
    documents = loader.load()
    if not documents:
        rprint("[bold red]AVERTISSEMENT : Le dossier 'knowledge_base' est vide ou introuvable. L'outil de RAG ne fonctionnera pas.[/bold red]")
        knowledge_retriever = None
    else:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)
        vectorstore = FAISS.from_documents(documents=splits, embedding=OllamaEmbeddings(model="llama3", base_url=OLLAMA_BASE_URL))
        knowledge_retriever = vectorstore.as_retriever()
        rprint("[bold green]✅ Base de connaissances RAG initialisée avec succès.[/bold green]")
except Exception as e:
    rprint(f"[bold red]Erreur lors de l'initialisation du RAG : {e}[/bold red]")
    knowledge_retriever = None



@tool
def dummy_weather_tool(location: str) -> str:
    """Renvoie la météo simulée pour un lieu donné."""
    weather_data = {
        "Paris": "☁️ 12°C, nuageux, vent modéré",
        "Lille": "🌤️ 15°C, ensoleillé, vent léger",
        "Marseille": "☀️ 20°C, grand soleil, pas de vent"
    }
    return weather_data.get(location, f"Météo inconnue pour {location}")

# --- Initialisation de la base de connaissances (RAG) ---
# Ceci ne devrait être fait qu'une seule fois au démarrage de l'application
def get_training_knowledge(query: str) -> str:
    """
    Recherche dans la base de connaissances sportives des informations pertinentes
    pour répondre à une question sur les principes d'entraînement.
    Utilise-le pour trouver comment construire un plan basé sur les métriques d'un utilisateur.
    """
    if knowledge_retriever is None:
        return "Erreur : La base de connaissances n'est pas disponible."
    
    docs = knowledge_retriever.invoke(query)
    return "\n\n".join([doc.page_content for doc in docs])

def get_user_metrics_from_db(user_id: int) -> str:
    """
    Récupère les métriques de performance les plus récentes pour un utilisateur donné.
    Retourne les données au format JSON.
    """
    try:
        engine = create_db_engine()
        metadata = sa.MetaData()
        metrics_table = sa.Table("metrics", metadata, autoload_with=engine)
        with engine.connect() as conn:
            stmt = sa.select(metrics_table).where(metrics_table.c.user_id == user_id).order_by(sa.desc(metrics_table.c.date_calcul))
            result = conn.execute(stmt).mappings().first()

        if not result:
            return json.dumps({"error": f"Aucune métrique trouvée pour l'utilisateur {user_id}."})
    except Exception as e:
        rprint(f"[bold red]Erreur dans l'outil get_user_metrics_from_db : {e}[/bold red]")
        return json.dumps({"error": f"Erreur de base de données lors de la récupération des métriques pour l'utilisateur {user_id}."})

    return json.dumps(dict(result), default=str)


# === Enregistrement des outils ===
tools = [get_user_metrics_from_db, get_training_knowledge]

llm = ChatOllama(model="llama3", base_url=OLLAMA_BASE_URL)

# llm_with_tools = llm.bind_tools(tools)


# === Structure d'état du graphe ===
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


# === Fonctions du graphe ===
def call_llm(state: AgentState) -> AgentState:
    # CORRECTION : On utilise le vrai SYSTEM_PROMPT que nous avons défini
    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    
    full_history = [system_msg] + state["messages"]
    
    response = llm.invoke(full_history, tools=tools)

    return {"messages": [response]}


def needs_tool(state: AgentState) -> str:
    if state["messages"][-1].tool_calls:
        return "action"
    return END

def use_tool(state: AgentState) -> AgentState:
    tool_calls = state["messages"][-1].tool_calls
    results = []
    for call in tool_calls:
        tool_to_use = {t.name: t for t in tools}[call["name"]]
        rprint(f"[bold cyan]🔧 Utilisation de l'outil : {tool_to_use.name}({call['args']})[/bold cyan]")
        output = tool_to_use.invoke(call["args"])
        results.append(ToolMessage(tool_call_id=call["id"], name=call["name"], content=str(output)))
    return {"messages": results}

def get_coaching_graph():
    """
    Construit et compile le graphe LangGraph de l'agent coach.
    Retourne l'objet graphe prêt à l'emploi.
    """

    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("llm", call_llm)
    graph_builder.add_node("action", use_tool)
    graph_builder.add_conditional_edges("llm", needs_tool, {"action": "action", END: END})
    graph_builder.add_edge("action", "llm")
    graph_builder.set_entry_point("llm")

    try:
        conn = sqlite3.connect("data/agent_memory.sqlite", check_same_thread=False)
        memory = SqliteSaver(conn=conn)
    except Exception as e:
        rprint(f"[bold red]ERREUR CRITIQUE : Impossible de se connecter à la BDD pour la mémoire de l'agent : {e}[/bold red]")
        raise

    graph = graph_builder.compile(checkpointer=memory)
    rprint("[bold green]✅ Graphe de coaching IA compilé.[/bold green]")
    return graph


# === Boucle de test CLI améliorée ===
if __name__ == "__main__":
    rprint("[bold yellow]🎽 Assistant sportif intelligent prêt ! (Tape 'quit' pour sortir)[/bold yellow]")
    
    graph = get_coaching_graph()
    CURRENT_USER_ID = 1
    rprint(f"[yellow]Utilisateur actuel : ID {CURRENT_USER_ID}[/yellow]")
  
    while True:
        user_input = input("🧠 Votre question : ")
        if user_input.lower() in ("quit", "exit", "q"):
            rprint("[bold green]À bientôt ![/bold green]")
            break

        full_input = f"Je suis l'utilisateur {CURRENT_USER_ID}. {user_input}"

        for event in graph.stream(
            {"messages": [HumanMessage(content=full_input)]},
            config={"configurable": {"thread_id": f"cli-thread-user-{CURRENT_USER_ID}"}}
        ):
            for step in event.values():
                message = step["messages"][-1]
                if isinstance(message, AIMessage) and message.content:
                    rprint(f"\n🤖 [green]{message.content}[/green]")
