import sys
import os
import json
import time
from pathlib import Path
from rich import print as rprint
from typing import Annotated, List, Any
from dotenv import load_dotenv


import operator
import openai
from typing_extensions import TypedDict, NotRequired

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

try:
    from E1_gestion_donnees.db_manager import create_db_engine
except ImportError:
    print("Impossible d'importer db_manager - mode sans base de données")
    create_db_engine = None

try:
    from src.config import DATABASE_URL, OPENAI_API_KEY
except ImportError:
    import os
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/garmin_data.db')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

load_dotenv()
api_key = OPENAI_API_KEY

# Allow running without API key in test environments
if not api_key and not os.getenv("PYTEST_CURRENT_TEST"):
    raise ValueError("Clé API OpenAI manquante. Assurez-vous que OPENAI_API_KEY est bien définie dans le fichier .env.")

STREAMLIT_SYSTEM_PROMPT = """
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

DJANGO_PLAN_GENERATOR_PROMPT = """
Tu es Coach Michael, un expert en planification d'entraînement de course à pied. Tu génères des plans d'entraînement structurés et personnalisés SUR PLUSIEURS SEMAINES.

**Ton processus OBLIGATOIRE :**
1. **Analyse des données :** Utilise TOUJOURS l'outil `get_user_metrics_from_db` pour analyser le profil utilisateur.
    - Si les données utilisateur sont incomplètes ou absentes, adapte le plan en fonction de profils génériques (débutant, intermédiaire, avancé).

2. **Durée obligatoire :** Génère TOUJOURS un plan qui couvre la durée demandée (exemple : 8 semaines = 8 semaines complètes de programme).

**FORMAT OBLIGATOIRE - TABLEAU MULTI-SEMAINES :**

## Semaine 1
| Jour | Type Séance | Durée | Description | Intensité |
|------|-------------|-------|-------------|-----------|
| Lundi | Repos | - | Récupération complète | Repos |
| Mardi | Endurance | 45min | Footing léger en endurance fondamentale | Faible |
| Mercredi | Fractionné | 60min | 2x(8x30/30) à 100% VMA + échauffement | Élevée |
| Jeudi | Repos | - | Récupération active ou étirements | Repos |
| Vendredi | Seuil | 60min | 3x8min à 85-90% FCM + échauffement | Modérée |
| Samedi | Repos | - | Préparation sortie longue | Repos |
| Dimanche | Sortie longue | 90min | Endurance fondamentale continue | Faible |

## Semaine 2  
| Jour | Type Séance | Durée | Description | Intensité |
|------|-------------|-------|-------------|-----------|
| Lundi | Repos | - | Récupération complète | Repos |
| Mardi | Endurance | 50min | Footing léger en endurance fondamentale | Faible |
| Mercredi | Fractionné | 65min | 3x(8x30/30) à 100% VMA + échauffement | Élevée |
| Jeudi | Repos | - | Récupération active ou étirements | Repos |
| Vendredi | Seuil | 65min | 4x8min à 85-90% FCM + échauffement | Modérée |
| Samedi | Repos | - | Préparation sortie longue | Repos |
| Dimanche | Sortie longue | 100min | Endurance fondamentale continue | Faible |

[Continue pour toutes les semaines demandées avec progression...]

**Objectif estimé :**
[Type d'objectif réaliste à atteindre dans la durée demandée]

**Conseils personnalisés :**
    - Si une erreur d’outil survient, continue avec les éléments disponibles et précise qu’une mise à jour sera nécessaire.
2. **Recherche expertise :** Utilise l'outil `get_training_knowledge` pour adapter le plan aux principes scientifiques.
    - Lorsque tu utilises `get_training_knowledge`, cite la source ou le concept clé utilisé (ex : "Principe de surcharge progressive").
3. **Génération directe :** Produis IMMÉDIATEMENT un plan structuré en tableau.

**ATTENTION : Ne fais AUCUNE SUPPOSITION :** Utilise uniquement les résultats des outils fournis.  
**ATTENTION : Ne change JAMAIS la structure du tableau hebdomadaire ni l'ordre des sections.**  
**INTERDIT : NE POSE JAMAIS DE QUESTIONS.**

**Format OBLIGATOIRE - Génère TOUJOURS cette structure exacte :**

### Plan d'entraînement personnalisé

**Analyse de votre profil :**
[Résumé des métriques utilisateur en 2-3 lignes]

**Programme hebdomadaire :**
- Le volume hebdomadaire (nombre de jours et durée totale) doit s’adapter à la disponibilité et au niveau de l’utilisateur.

| Jour | Type Séance | Durée | Description | Intensité |
|------|-------------|-------|-------------|-----------|
| Lundi | Repos | - | Récupération active ou repos complet | Repos |
| Mardi | Endurance | 45min | Footing en aisance respiratoire | Faible |
| Mercredi | Fractionné | 50min | 2x(8x30/30) à 95-100% VMA | Élevée |
| Jeudi | Repos | - | Étirements ou marche active | Repos |
| Vendredi | Seuil | 60min | 3x8min à 85-90% FCM + échauffement | Modérée |
| Samedi | Repos | - | Préparation sortie longue | Repos |
| Dimanche | Sortie longue | 90min | Endurance fondamentale continue | Faible |

**Objectif estimé (optionnel) :**
[Type d’objectif réaliste à atteindre dans 6 à 8 semaines (ex : courir 10 km en moins de 55 minutes)]

**Conseils personnalisés :**
[2-3 conseils spécifiques basés sur les données utilisateur]
- Les conseils doivent être basés sur les métriques individuelles (ex : fréquence cardiaque élevée, manque de récupération, faible régularité).

**Recommandations importantes :**
- Écoutez votre corps et adaptez l'intensité si nécessaire
- Hydratez-vous régulièrement pendant les séances
- En cas de douleur, consultez un professionnel de santé
"""


# Mode par défaut (Streamlit)
SYSTEM_PROMPT = STREAMLIT_SYSTEM_PROMPT

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, api_key=api_key)
embedding = OpenAIEmbeddings(api_key=api_key)

try:
    possible_paths = [
        "knowledge_base/",
        "/app/knowledge_base/", 
        "../../../knowledge_base/",
        "../../knowledge_base/"
    ]
    
    knowledge_base_path = None
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            knowledge_base_path = path
            break
    
    if not knowledge_base_path:
        raise FileNotFoundError("Directory not found: 'knowledge_base/'")
        
    loader = DirectoryLoader(knowledge_base_path, glob="**/*.md", show_progress=True)
    documents = loader.load()
    if not documents:
        rprint("[bold red]Dossier 'knowledge_base' vide ou manquant. L'outil RAG ne fonctionnera pas.[/bold red]")
        knowledge_retriever = None
    else:
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)
        vectorstore = FAISS.from_documents(documents=splits, embedding=embedding)
        knowledge_retriever = vectorstore.as_retriever()
        rprint("[bold green]Base de connaissances initialisée avec succès.[/bold green]")
except Exception as e:
    rprint(f"[bold red]Erreur lors de l'initialisation du RAG : {e}[/bold red]")
    knowledge_retriever = None


@tool
def get_weather_forecast(location: str) -> str:
    """Renvoie la météo simulée pour un lieu donné."""
    weather_data = {
        "Paris": "12°C, nuageux, vent modéré",
        "Lille": "15°C, ensoleillé, vent léger",
        "Marseille": "20°C, grand soleil, pas de vent"
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


def get_db_engine_with_fallback():
    """
    Crée une connexion à la base de données avec fallback Django SQLite si PostgreSQL échoue.
    """
    # FORCER LE SQLITE POUR CORRIGER LE PROBLÈME TEMPORAIREMENT
    docker_env = os.getenv('DOCKER_ENV')
    print(f"DEBUG: DOCKER_ENV={docker_env}, type={type(docker_env)}")
    
    if docker_env == 'true':
        print("Mode Docker - utilisation directe SQLite Django...")
        rprint("[yellow]Mode Docker - utilisation directe SQLite Django...[/yellow]")
    else:
        print(f"Mode local (DOCKER_ENV={docker_env}) - tentative PostgreSQL d'abord...")
        try:
            # Essayer d'abord la configuration par défaut (PostgreSQL/SQL Server)
            engine = create_db_engine()
            # Test rapide de connexion
            with engine.connect() as conn:
                conn.execute(sa.text("SELECT 1"))
            rprint("[green]Connexion DB principale réussie[/green]")
            return engine
        except Exception as e:
            rprint(f"[yellow]DB principale inaccessible: {e}[/yellow]")
            rprint("[yellow]Basculement vers SQLite Django...[/yellow]")
        
    # Fallback vers la base SQLite Django  
    django_db_path = "/app/data/django_garmin_data.db"
    if not os.path.exists(django_db_path):
        # En développement local
        django_db_path = "data/django_garmin_data.db"
    
    if os.path.exists(django_db_path):
        sqlite_url = f"sqlite:///{django_db_path}"
        engine = sa.create_engine(sqlite_url, connect_args={'check_same_thread': False})
        rprint(f"[green]SQLite activé: {django_db_path}[/green]")
        
        # Test de connexion et vérification des tables
        try:
            with engine.connect() as conn:
                result = conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table' AND name='activities_activity'"))
                table_exists = result.fetchone()
                if table_exists:
                    rprint(f"[green]Table activities_activity trouvée[/green]")
                else:
                    rprint(f"[red]Table activities_activity manquante[/red]")
                    # Afficher toutes les tables disponibles
                    result = conn.execute(sa.text("SELECT name FROM sqlite_master WHERE type='table'"))
                    tables = [row[0] for row in result.fetchall()]
                    rprint(f"[yellow]Tables disponibles: {tables}[/yellow]")
        except Exception as e:
            rprint(f"[red]Erreur test connexion SQLite: {e}[/red]")
        
        return engine
    else:
        raise Exception(f"Aucune base de données accessible (ni principale ni SQLite)")

@tool
def get_user_metrics_from_db(user_id: int) -> str:
    """
    Récupère les métriques de performance les plus récentes pour un utilisateur donné.
    Retourne les données au format JSON.
    """
    try:
        engine = get_db_engine_with_fallback()
        rprint(f"[cyan]DEBUG get_user_metrics_from_db: engine={engine.url}[/cyan]")
        with engine.connect() as conn:
            # Essayer d'abord avec la table metrics FastAPI
            try:
                metadata = sa.MetaData()
                metrics_table = sa.Table("metrics", metadata, autoload_with=engine)
                stmt = sa.select(metrics_table).where(
                    metrics_table.c.user_id == user_id
                ).order_by(sa.desc(metrics_table.c.date_calcul))
                result = conn.execute(stmt).mappings().first()
                
                if result:
                    return json.dumps(dict(result), default=str)
            except:
                pass
            
            # Déterminer le type de base pour adapter la requête
            if 'sqlite' in str(engine.url):
                date_filter = "date('now', '-90 days')"
            else:
                date_filter = "CURRENT_DATE - INTERVAL '90 days'"
            
            result = conn.execute(sa.text(f"""
                SELECT 
                    COUNT(*) as total_activities,
                    AVG(distance_meters/1000.0) as avg_distance_km,
                    AVG(duration_seconds/60.0) as avg_duration_min,
                    AVG(average_hr) as avg_heart_rate,
                    MAX(start_time) as last_activity_date,
                    AVG(average_speed) as avg_speed_kmh,
                    SUM(distance_meters/1000.0) as total_distance_km,
                    SUM(duration_seconds/3600.0) as total_duration_hours
                FROM activities_activity 
                WHERE user_id = :user_id
                    AND start_time >= {date_filter}
            """), {"user_id": user_id}).fetchone()

        if not result or result[0] == 0:
            return json.dumps({"error": f"Aucune métrique trouvée pour l'utilisateur {user_id}."})
        
        # Convertir en dictionnaire avec noms explicites
        metrics = {
            "user_id": user_id,
            "total_activities": result[0],
            "avg_distance_km": round(result[1] or 0, 2),
            "avg_duration_min": round(result[2] or 0, 1),
            "avg_heart_rate": round(result[3] or 0, 0) if result[3] else None,
            "last_activity_date": result[4],
            "avg_speed_kmh": round(result[5] or 0, 2),
            "total_distance_km": round(result[6] or 0, 1),
            "total_duration_hours": round(result[7] or 0, 1),
            "period": "90 derniers jours"
        }
        
        return json.dumps(metrics, default=str)
    
    except Exception as e:
        rprint(f"[bold red]Erreur dans l'outil get_user_metrics_from_db : {e}[/bold red]")
        return json.dumps({"error": f"Erreur de base de données lors de la récupération des métriques pour l'utilisateur {user_id}."})


def call_openai_agent(messages):
    """Appel OpenAI avec métriques Prometheus"""
    # openai_requests_total.inc()  # Temporairement désactivé
    start_time = time.time()
    try:
        # API OpenAI moderne
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        duration = time.time() - start_time
        # openai_response_time.observe(duration)  # Temporairement désactivé
        return response
    except Exception as e:
        # openai_errors_total.inc()  # Temporairement désactivé
        rprint(f"[bold red]Erreur OpenAI: {e}[/bold red]")
        raise

# === Enregistrement des outils ===
tools = [get_user_metrics_from_db, get_training_knowledge, get_weather_forecast]

# Réinitialisation du LLM avec les outils
llm_with_tools = llm.bind_tools(tools)


# === Structure d'état du graphe ===
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    mode: NotRequired[str]  # "streamlit" ou "plan_generator"


# === Fonctions du graphe ===
def call_llm(state: AgentState) -> AgentState:
    # Déterminer le mode basé sur le contexte ou utiliser le mode par défaut
    mode = state.get("mode", "streamlit")
    if mode == "plan_generator":
        system_prompt = DJANGO_PLAN_GENERATOR_PROMPT
    else:
        system_prompt = STREAMLIT_SYSTEM_PROMPT
    
    system_msg = SystemMessage(content=system_prompt)
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
            rprint(f"[bold cyan]Utilisation de l'outil : {tool_to_use.name}({call['args']})[/bold cyan]")
            
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
    rprint("[bold green]Graphe de coaching IA compilé.[/bold green]")
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
    rprint("[bold yellow]Assistant sportif intelligent prêt ! (Tape 'quit' pour sortir)[/bold yellow]")
    
    try:
        graph = await get_coaching_graph()
        CURRENT_USER_ID = 1
        rprint(f"[yellow]Utilisateur actuel : ID {CURRENT_USER_ID}[/yellow]")
    except Exception as e:
        rprint(f"[bold red]Erreur lors de l'initialisation du graphe : {e}[/bold red]")
        return
  
    while True:
        try:
            user_input = input("Votre question : ")
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
                            rprint(f"\nCoach IA : [green]{message.content}[/green]")
                            
        except KeyboardInterrupt:
            rprint("\n[bold yellow]Interruption par l'utilisateur.[/bold yellow]")
            break
        except Exception as e:
            rprint(f"[bold red]Erreur inattendue : {e}[/bold red]")
            continue


if __name__ == "__main__":
    asyncio.run(main())