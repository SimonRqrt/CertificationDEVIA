import sys
import os
import json
from pathlib import Path
from rich import print as rprint
from typing import Annotated, List, Any
from dotenv import load_dotenv

import operator
from typing_extensions import TypedDict

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage, AnyMessage
from langchain_core.messages.ai import AIMessage

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import DirectoryLoader
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter

import sqlalchemy as sa
import sqlite3
import asyncio
import aiosqlite

from E1_gestion_donnees.db_manager import create_db_engine
from src.config import DATABASE_URL, OPENAI_API_KEY

# Chargement des variables d'environnement
load_dotenv()
api_key = OPENAI_API_KEY

if not api_key:
    raise ValueError("❌ Clé API OpenAI manquante. Assurez-vous que OPENAI_API_KEY est bien définie dans le fichier .env.")

# DÉFINIT LA PERSONNALITÉ ET LES RÈGLES DE L'AGENT
SYSTEM_PROMPT = """
Tu es un coach sportif expert, prudent et encourageant, basé sur les données. Ton nom est "Coach Michael", mais tu précises quand tu te présentes que tu es un coach IA. Tu dois demander à l'utilisateur s'il préfère que tu sois un coach plutôt aggressif, doux, motivant, pour que tu adoptes ta personnalité en fonction de ses réponses.

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

# Initialisation du LLM et des embeddings
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)
embedding = OpenAIEmbeddings(api_key=api_key)

# Chargement des documents et initialisation de la base de connaissances
try:
    loader = DirectoryLoader("knowledge_base/", glob="**/*.md", show_progress=True)
    documents = loader.load()
    if not documents:
        rprint("[bold red]⚠️ Dossier 'knowledge_base' vide ou manquant. L'outil RAG ne fonctionnera pas.[/bold red]")
        knowledge_retriever = None
    else:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)
        vectorstore = FAISS.from_documents(documents=splits, embedding=embedding)
        knowledge_retriever = vectorstore.as_retriever()
        rprint("[bold green]✅ Base de connaissances initialisée avec succès.[/bold green]")
except Exception as e:
    rprint(f"[bold red]Erreur lors de l'initialisation du RAG : {e}[/bold red]")
    knowledge_retriever = None


@tool
def get_weather_forecast(location: str) -> str:
    """Renvoie la météo simulée pour un lieu donné."""
    weather_data = {
        "Paris": "☁️ 12°C, nuageux, vent modéré",
        "Lille": "🌤️ 15°C, ensoleillé, vent léger",
        "Marseille": "☀️ 20°C, grand soleil, pas de vent"
    }
    return weather_data.get(location, f"Météo inconnue pour {location}")


@tool
def get_training_knowledge(query: str) -> str:
    """
    Recherche dans la base de connaissances sportives des informations pertinentes
    pour répondre à une question sur les principes d'entraînement.
    Utilise-le pour trouver comment construire un plan basé sur les métriques d'un utilisateur.
    """
    if knowledge_retriever is None:
        return "Erreur : La base de connaissances n'est pas disponible."
    
    try:
        docs = knowledge_retriever.invoke(query)
        return "\n\n".join([doc.page_content for doc in docs])
    except Exception as e:
        rprint(f"[bold red]Erreur lors de la recherche dans la base de connaissances : {e}[/bold red]")
        return f"Erreur lors de la recherche : {str(e)}"


@tool
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
            stmt = sa.select(metrics_table).where(
                metrics_table.c.user_id == user_id
            ).order_by(sa.desc(metrics_table.c.date_calcul))
            result = conn.execute(stmt).mappings().first()

        if not result:
            return json.dumps({"error": f"Aucune métrique trouvée pour l'utilisateur {user_id}."})
        
        return json.dumps(dict(result), default=str)
    
    except Exception as e:
        rprint(f"[bold red]Erreur dans l'outil get_user_metrics_from_db : {e}[/bold red]")
        return json.dumps({"error": f"Erreur de base de données lors de la récupération des métriques pour l'utilisateur {user_id}."})


# === Enregistrement des outils ===
tools = [get_user_metrics_from_db, get_training_knowledge, get_weather_forecast]

# Réinitialisation du LLM avec les outils
llm_with_tools = llm.bind_tools(tools)


# === Structure d'état du graphe ===
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


# === Fonctions du graphe ===
def call_llm(state: AgentState) -> AgentState:
    system_msg = SystemMessage(content=SYSTEM_PROMPT)
    full_history = [system_msg] + state["messages"]
    
    try:
        response = llm_with_tools.invoke(full_history)
        return {"messages": [response]}
    except Exception as e:
        rprint(f"[bold red]Erreur lors de l'appel au LLM : {e}[/bold red]")
        error_msg = AIMessage(content=f"Désolé, une erreur s'est produite : {str(e)}")
        return {"messages": [error_msg]}


def needs_tool(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "action"
    return END


def use_tool(state: AgentState) -> AgentState:
    tool_calls = state["messages"][-1].tool_calls
    results = []
    
    # Création du dictionnaire des outils disponibles
    available_tools = {t.name: t for t in tools}
    
    for call in tool_calls:
        tool_name = call["name"]
        if tool_name in available_tools:
            tool_to_use = available_tools[tool_name]
            rprint(f"[bold cyan]🔧 Utilisation de l'outil : {tool_to_use.name}({call['args']})[/bold cyan]")
            
            try:
                output = tool_to_use.invoke(call["args"])
                results.append(ToolMessage(
                    tool_call_id=call["id"], 
                    name=call["name"], 
                    content=str(output)
                ))
            except Exception as e:
                rprint(f"[bold red]Erreur lors de l'exécution de l'outil {tool_name} : {e}[/bold red]")
                results.append(ToolMessage(
                    tool_call_id=call["id"], 
                    name=call["name"], 
                    content=f"Erreur lors de l'exécution de l'outil : {str(e)}"
                ))
        else:
            rprint(f"[bold red]Outil inconnu : {tool_name}[/bold red]")
            results.append(ToolMessage(
                tool_call_id=call["id"], 
                name=call["name"], 
                content=f"Outil inconnu : {tool_name}"
            ))
    
    return {"messages": results}


async def create_async_checkpointer():
    """
    Crée un checkpointer AsyncSqliteSaver de manière asynchrone.
    """
    try:
        # Créer le répertoire data s'il n'existe pas
        os.makedirs("data", exist_ok=True)
        
        # Créer le checkpointer avec AsyncSqliteSaver
        checkpointer = AsyncSqliteSaver.from_conn_string("data/agent_memory.sqlite")
        
        # Initialiser les tables de façon asynchrone
        await checkpointer.setup()
        
        return checkpointer
    except Exception as e:
        rprint(f"[bold red]Erreur lors de la création du checkpointer : {e}[/bold red]")
        return None


async def get_coaching_graph():
    """
    Construit et compile le graphe LangGraph de l'agent coach de façon asynchrone.
    Retourne l'objet graphe prêt à l'emploi.
    """
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("llm", call_llm)
    graph_builder.add_node("action", use_tool)
    graph_builder.add_conditional_edges("llm", needs_tool, {"action": "action", END: END})
    graph_builder.add_edge("action", "llm")
    graph_builder.set_entry_point("llm")

    # Créer le checkpointer de façon asynchrone
    checkpointer = await create_async_checkpointer()
    
    if checkpointer is None:
        rprint("[bold yellow]Attention : L'agent fonctionnera sans mémoire persistante.[/bold yellow]")

    graph = graph_builder.compile(checkpointer=checkpointer)
    rprint("[bold green]✅ Graphe de coaching IA compilé.[/bold green]")
    return graph


# Version synchrone pour la compatibilité
def get_coaching_graph_sync():
    """
    Version synchrone de get_coaching_graph pour la compatibilité.
    """
    return asyncio.run(get_coaching_graph())


# === Boucle de test CLI améliorée ===
async def main():
    """Fonction principale asynchrone pour les tests CLI."""
    rprint("[bold yellow]🎽 Assistant sportif intelligent prêt ! (Tape 'quit' pour sortir)[/bold yellow]")
    
    try:
        graph = await get_coaching_graph()
        CURRENT_USER_ID = 1
        rprint(f"[yellow]Utilisateur actuel : ID {CURRENT_USER_ID}[/yellow]")
    except Exception as e:
        rprint(f"[bold red]Erreur lors de l'initialisation du graphe : {e}[/bold red]")
        return
  
    while True:
        try:
            user_input = input("🧠 Votre question : ")
            if user_input.lower() in ("quit", "exit", "q"):
                rprint("[bold green]À bientôt ![/bold green]")
                break

            full_input = f"Je suis l'utilisateur {CURRENT_USER_ID}. {user_input}"

            async for event in graph.astream(
                {"messages": [HumanMessage(content=full_input)]},
                config={"configurable": {"thread_id": f"cli-thread-user-{CURRENT_USER_ID}"}}
            ):
                for step in event.values():
                    if "messages" in step and step["messages"]:
                        message = step["messages"][-1]
                        if isinstance(message, AIMessage) and message.content:
                            rprint(f"\n🤖 [green]{message.content}[/green]")
                            
        except KeyboardInterrupt:
            rprint("\n[bold yellow]Interruption par l'utilisateur.[/bold yellow]")
            break
        except Exception as e:
            rprint(f"[bold red]Erreur inattendue : {e}[/bold red]")
            continue


if __name__ == "__main__":
    asyncio.run(main())