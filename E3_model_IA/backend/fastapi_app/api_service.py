
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from rich import print as rprint
from starlette.responses import StreamingResponse
from datetime import datetime
import uuid
import time
from prometheus_client import generate_latest

import sys
import os

# Add project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from E1_gestion_donnees.db_manager import create_db_engine, create_tables
from E3_model_IA.scripts.advanced_agent import get_coaching_graph
from fastapi_auth_middleware import auth_middleware, get_current_user, get_user_context
from django_auth_service import UserInfo
from metrics_config import start_metrics_server, training_plans_generated
from langchain_core.messages import HumanMessage
import json
import pandas as pd

try:
    from src.config import API_HOST, API_PORT, API_DEBUG, DATABASE_URL
except ImportError:
    # Fallback to environment variables if config file not available
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    API_DEBUG = os.getenv('API_DEBUG', 'False').lower() == 'true'
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/garmin_data.db')

@asynccontextmanager
async def lifespan(app: FastAPI):

    rprint("[yellow]Démarrage de l'application et des services...[/yellow]")

    # Démarrage serveur métriques Prometheus
    start_metrics_server(8080)
    rprint("[green]✅ Serveur métriques Prometheus démarré sur le port 8080[/green]")

    app.state.db_engine = create_db_engine()
    app.state.db_tables = create_tables(app.state.db_engine)
    rprint("[green]✅ Moteur de base de données pour les données d'activité initialisé.[/green]")

    coaching_agent = await get_coaching_graph()
    app.state.coaching_agent = coaching_agent
    
    # Le service analytics utilise le même moteur que l'app principale
    app.state.analytics_engine = app.state.db_engine
    app.state.analytics_tables = app.state.db_tables
    rprint("[green]✅ Service Analytics SQLAlchemy E1 prêt (moteur partagé).[/green]")

    rprint("[bold green]✅ Application démarrée. L'agent et analytics sont prêts.[/bold green]")

    yield

    rprint("[yellow]Arrêt de l'application...[/yellow]")



# On récupère la clé API attendue depuis les variables d'environnement
app = FastAPI(
    title="Coach running AI API",
    description="API pour accéder aux données Garmin et interagir avec l'assistant de coaching IA.",
    version="2.0.0",
    lifespan=lifespan
)

EXPECTED_API_KEY = os.getenv("API_KEY", "default_key")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)



async def get_api_key(key: str = Security(api_key_header)):
    """Vérifie la clé API fournie dans les en-têtes."""
    if key == EXPECTED_API_KEY:
        return key
    else:
        raise HTTPException(status_code=403, detail="Clé API invalide ou manquante.")
    

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None # Pour suivre une conversation existante
    user_id: Optional[int] = None # ID utilisateur pour personnalisation

# ==========================================
# MODÈLES DE DONNÉES SUPPRIMÉS (Architecture E1/E3)
# → Les données sont gérées par Django REST API
# → FastAPI se concentre uniquement sur l'IA
# =========================================


@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API Coach AI Garmin Data"}


@app.get("/metrics")
def metrics():
    """Endpoint Prometheus pour les métriques"""
    try:
        return Response(generate_latest(), media_type="text/plain")
    except Exception as e:
        # Fallback si prometheus_client n'est pas disponible
        return Response("# Prometheus metrics endpoint\n# Service is running but metrics are not yet configured\n", media_type="text/plain")


# ==========================================
# ENDPOINTS /activities/ SUPPRIMÉS
# → Utiliser Django REST API /api/v1/activities/ 
# ==========================================
# Cette API se concentre uniquement sur l'IA (E3)
# Les données sont gérées par Django REST (E1)

# \== Endpoint d'IA (Bloc E3) ==

@app.post("/v1/coaching/chat", tags=["Coaching IA"])
async def chat_with_coach(
    chat_request: ChatRequest,
    fastapi_request: Request,
    current_user: UserInfo = get_current_user,
    user_context: Dict[str, Any] = get_user_context
):
    """Chat avec le coach IA (authentification Django JWT)"""
    
    start_time = time.time()
    session_id = str(uuid.uuid4())
    
    coaching_agent = fastapi_request.app.state.coaching_agent
    
    # Construire le message avec contexte utilisateur
    context_info = f"""
    Utilisateur: {current_user.first_name} {current_user.last_name} ({current_user.email})
    Activité préférée: {current_user.preferred_activity}
    Objectif principal: {current_user.main_goal}
    Statut: {'Premium' if current_user.is_premium else 'Standard'}
    Statistiques: {user_context.get('stats', {})}
    """
    
    full_input = f"Contexte utilisateur: {context_info}\n\nMessage: {chat_request.message}"
    thread_id = chat_request.thread_id or f"user-thread-{current_user.id}"
    config = {"configurable": {"thread_id": thread_id}}

    # Stocker la session de coaching
    session_data = {
        'session_id': session_id,
        'title': chat_request.message[:100],  # Titre basé sur le message
        'user_message': chat_request.message,
        'ai_response': '',  # Sera mis à jour
        'context_data': user_context,
        'response_time': None  # Sera calculé
    }

    async def stream_response():
        ai_response_parts = []
        
        # Déterminer le mode basé sur le thread_id
        mode = "plan_generator" if "plan-generation" in thread_id else "streamlit"
        
        async for event in coaching_agent.astream({
            "messages": [HumanMessage(content=full_input)], 
            "mode": mode
        }, config=config):
            for step in event.values():
                message = step["messages"][-1]
                if hasattr(message, 'content') and message.content:
                    ai_response_parts.append(message.content)
                    yield json.dumps({"type": "content", "data": message.content}) + "\n"
        
        # Finaliser la session
        end_time = time.time()
        session_data['ai_response'] = ''.join(ai_response_parts)
        session_data['response_time'] = end_time - start_time
        
        # Enregistrer dans Django
        auth_middleware.create_coaching_session(current_user.id, session_data)
        
        yield json.dumps({"type": "end", "data": "Stream finished."}) + "\n"

    return StreamingResponse(stream_response(), media_type="application/x-ndjson")


@app.post("/v1/coaching/chat-legacy", tags=["Coaching IA"])
async def chat_with_coach_legacy(
    chat_request: ChatRequest,
    fastapi_request: Request,
    api_key: str = Depends(get_api_key)
):
    """Chat avec le coach IA (méthode legacy avec clé API)"""
    
    coaching_agent = fastapi_request.app.state.coaching_agent
    # Utiliser le user_id passé par Django, ou 1 par défaut pour compatibilité
    user_id = chat_request.user_id or 1
    full_input = f"Je suis l'utilisateur {user_id}. {chat_request.message}"
    thread_id = chat_request.thread_id or f"user-thread-{user_id}"
    config = {"configurable": {"thread_id": thread_id}}

    async def stream_response():
        # Déterminer le mode basé sur le thread_id
        mode = "plan_generator" if "plan-generation" in thread_id else "streamlit"
        print(f"🔍 DEBUG: thread_id={thread_id}, mode détecté={mode}")
        
        async for event in coaching_agent.astream({
            "messages": [HumanMessage(content=full_input)], 
            "mode": mode
        }, config=config):
            for step in event.values():
                message = step["messages"][-1]
                if hasattr(message, 'content') and message.content:
                    yield json.dumps({"type": "content", "data": message.content}) + "\n"
        yield json.dumps({"type": "end", "data": "Stream finished."}) + "\n"

    return StreamingResponse(stream_response(), media_type="application/x-ndjson")


# ===== GÉNÉRATION DE PLANS D'ENTRAÎNEMENT =====

class TrainingPlanRequest(BaseModel):
    """Modèle pour la demande de génération de plan d'entraînement"""
    user_id: int
    user_email: str
    personal_info: Dict[str, Any]
    running_goal: Dict[str, Any]
    training_preferences: Dict[str, Any]
    recent_activities: Optional[Dict[str, Any]] = None
    user_context: Optional[Dict[str, Any]] = None


class TrainingPlanResponse(BaseModel):
    """Modèle pour la réponse de plan d'entraînement généré"""
    name: str
    description: str
    duration_weeks: int
    sessions: List[Dict[str, Any]]
    recommendations: List[str]
    generation_time: float


@app.post("/v1/coaching/generate-training-plan", response_model=TrainingPlanResponse, tags=["Coaching IA"])
async def generate_training_plan(
    plan_request: TrainingPlanRequest,
    fastapi_request: Request,
    current_user: UserInfo = Depends(get_current_user)
):
    """Génération automatique d'un plan d'entraînement personnalisé"""
    
    start_time = time.time()
    
    coaching_agent = fastapi_request.app.state.coaching_agent
    
    # Construire le prompt pour l'agent IA
    prompt = f"""
    GÉNÉRATION DE PLAN D'ENTRAÎNEMENT PERSONNALISÉ
    
    UTILISATEUR:
    - ID: {plan_request.user_id}
    - Email: {plan_request.user_email}
    - Âge: {plan_request.personal_info.get('age')} ans
    - Poids: {plan_request.personal_info.get('weight')} kg
    - Taille: {plan_request.personal_info.get('height')} cm
    - Sexe: {plan_request.personal_info.get('gender')}
    - Niveau: {plan_request.personal_info.get('experience_level')}
    - Km hebdomadaires actuels: {plan_request.personal_info.get('current_weekly_km', 0)} km
    
    OBJECTIF RUNNING:
    - Type: {plan_request.running_goal.get('race_type')}
    - Date cible: {plan_request.running_goal.get('target_date', 'Non définie')}
    - Temps objectif: {plan_request.running_goal.get('target_time', 'Non défini')}
    - Meilleur temps actuel: {plan_request.running_goal.get('current_best_time', 'Non défini')}
    - Priorité: {plan_request.running_goal.get('priority')}
    - Motivation: {plan_request.running_goal.get('motivation', '')}
    
    PRÉFÉRENCES D'ENTRAÎNEMENT:
    - Séances par semaine: {plan_request.training_preferences.get('sessions_per_week')}
    - Jours disponibles: {', '.join(plan_request.training_preferences.get('available_days', []))}
    - Durée préférée: {plan_request.training_preferences.get('preferred_duration')}
    - Environnement: {', '.join(plan_request.training_preferences.get('training_environment', []))}
    - Niveau actuel: {plan_request.training_preferences.get('current_level')}
    - Antécédents blessures: {'Oui' if plan_request.training_preferences.get('injury_history') else 'Non'}
    - Détails blessures: {plan_request.training_preferences.get('injury_details', 'Aucun détail')}
    - Activités complémentaires: {', '.join(plan_request.training_preferences.get('cross_training', []))}
    
    HISTORIQUE RÉCENT:
    {json.dumps(plan_request.recent_activities, indent=2) if plan_request.recent_activities else 'Aucun historique disponible'}
    
    MÉTRIQUES DE PERFORMANCE (si disponibles):
    - Dernière VMA: {plan_request.user_context.get('latest_metrics', {}).get('vma', 'Non mesurée') if plan_request.user_context else 'Non mesurée'} km/h
    - VO2 Max estimé: {plan_request.user_context.get('latest_metrics', {}).get('vo2_max', 'Non mesuré') if plan_request.user_context else 'Non mesuré'} ml/kg/min
    - Zone FC 1 (50-60%): {plan_request.user_context.get('hr_zones', {}).get('zone_1', 'Non définie') if plan_request.user_context else 'Non définie'} bpm
    - Zone FC 2 (60-70%): {plan_request.user_context.get('hr_zones', {}).get('zone_2', 'Non définie') if plan_request.user_context else 'Non définie'} bpm
    - Zone FC 3 (70-80%): {plan_request.user_context.get('hr_zones', {}).get('zone_3', 'Non définie') if plan_request.user_context else 'Non définie'} bpm
    - Zone FC 4 (80-90%): {plan_request.user_context.get('hr_zones', {}).get('zone_4', 'Non définie') if plan_request.user_context else 'Non définie'} bpm
    - Zone FC 5 (90-100%): {plan_request.user_context.get('hr_zones', {}).get('zone_5', 'Non définie') if plan_request.user_context else 'Non définie'} bpm
    
    RECOMMANDATIONS SÉCURITÉ:
    - Blessures connues: {"Oui - " + plan_request.training_preferences.get('injury_details', '') if plan_request.training_preferences.get('injury_history') else 'Aucune'}
    - Activités complémentaires pratiquées: {', '.join(plan_request.training_preferences.get('cross_training', [])) or 'Aucune'}
    - Points d'attention: {"Adaptation progressive nécessaire" if plan_request.personal_info.get('experience_level') == 'beginner' else "Progression standard possible"}
    
    TÂCHE:
    Génère un plan d'entraînement personnalisé au format JSON avec:
    1. Un nom accrocheur pour le plan
    2. Une description motivante (2-3 phrases)
    3. Durée en semaines (8-16 semaines recommandées)
    4. Liste détaillée des séances sur les 4 premières semaines avec:
       - name: nom de la séance
       - description: description détaillée 
       - type: type de séance (easy_run, tempo_run, interval_training, etc.)
       - day_offset: jour relatif (0=aujourd'hui, 1=demain, etc.)
       - duration_minutes: durée en minutes
       - distance_km: distance en km (optionnel)
       - hr_zone: zone de FC recommandée (1-5, optionnel)
    5. Liste de 3-5 recommandations personnalisées
    
    RÉPONDS UNIQUEMENT EN JSON VALIDE, sans texte additionnel.
    """
    
    # Générer le plan via l'agent IA
    thread_id = f"plan-generation-{plan_request.user_id}-{int(start_time)}"
    config = {"configurable": {"thread_id": thread_id}}
    
    ai_response_parts = []
    
    async for event in coaching_agent.astream({"messages": [HumanMessage(content=prompt)]}, config=config):
        for step in event.values():
            message = step["messages"][-1]
            if hasattr(message, 'content') and message.content:
                ai_response_parts.append(message.content)
    
    ai_response = ''.join(ai_response_parts)
    
    try:
        # Extraire le JSON de la réponse IA
        # L'IA peut retourner du texte avec du JSON, on extrait juste la partie JSON
        json_start = ai_response.find('{')
        json_end = ai_response.rfind('}') + 1
        
        if json_start == -1 or json_end == 0:
            raise ValueError("Aucun JSON trouvé dans la réponse")
        
        json_response = ai_response[json_start:json_end]
        plan_data = json.loads(json_response)
        
        # Validation et valeurs par défaut
        plan_data.setdefault('name', f"Plan {plan_request.running_goal.get('race_type', 'Running').title()}")
        plan_data.setdefault('description', 'Plan d\'entraînement personnalisé généré par IA')
        plan_data.setdefault('duration_weeks', 12)
        plan_data.setdefault('sessions', [])
        plan_data.setdefault('recommendations', [])
        
        generation_time = time.time() - start_time
        
        # Incrémenter la métrique Prometheus
        training_plans_generated.inc()
        
        return TrainingPlanResponse(
            name=plan_data['name'],
            description=plan_data['description'],
            duration_weeks=plan_data['duration_weeks'],
            sessions=plan_data['sessions'],
            recommendations=plan_data['recommendations'],
            generation_time=generation_time
        )
        
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        # Fallback : plan de base si l'IA ne répond pas correctement
        rprint(f"[red]Erreur parsing JSON IA: {str(e)}[/red]")
        rprint(f"[yellow]Réponse IA brute: {ai_response}[/yellow]")
        
        # Plan de base selon l'objectif
        race_type = plan_request.running_goal.get('race_type', 'general_fitness')
        sessions_per_week = plan_request.training_preferences.get('sessions_per_week', 3)
        
        fallback_sessions = []
        for week in range(4):  # 4 premières semaines
            for session in range(sessions_per_week):
                day_offset = week * 7 + (session * 2)  # Espacement des séances
                
                if session == 0:  # Séance facile
                    fallback_sessions.append({
                        'name': f'Course facile - Semaine {week + 1}',
                        'description': 'Course à allure conversationnelle',
                        'type': 'easy_run',
                        'day_offset': day_offset,
                        'duration_minutes': 30 + week * 5,
                        'distance_km': 5 + week,
                        'hr_zone': 2
                    })
                elif session == 1:  # Séance tempo
                    fallback_sessions.append({
                        'name': f'Tempo run - Semaine {week + 1}',
                        'description': 'Course à allure soutenue',
                        'type': 'tempo_run',
                        'day_offset': day_offset,
                        'duration_minutes': 25 + week * 5,
                        'distance_km': 4 + week * 0.5,
                        'hr_zone': 4
                    })
                else:  # Séance longue
                    fallback_sessions.append({
                        'name': f'Sortie longue - Semaine {week + 1}',
                        'description': 'Course longue en endurance fondamentale',
                        'type': 'long_run',
                        'day_offset': day_offset,
                        'duration_minutes': 45 + week * 10,
                        'distance_km': 8 + week * 2,
                        'hr_zone': 2
                    })
        
        generation_time = time.time() - start_time
        
        return TrainingPlanResponse(
            name=f"Plan {race_type.replace('_', ' ').title()}",
            description=f"Plan d'entraînement personnalisé pour votre objectif {race_type}",
            duration_weeks=12,
            sessions=fallback_sessions,
            recommendations=[
                "Augmentez progressivement votre kilométrage",
                "Respectez vos zones de fréquence cardiaque",
                "N'oubliez pas les séances de récupération",
                "Hydratez-vous régulièrement"
            ],
            generation_time=generation_time
        )


# ===== ENDPOINTS ANALYTICS AVANCÉS (SQLAlchemy E1) =====

def get_performance_trends_data(engine, user_id: int, period_weeks: int = 12):
    """Analyse des tendances de performance avec moyennes mobiles"""
    from sqlalchemy import text
    
    query = text("""
    SELECT 
        start_time,
        distance_meters/1000.0 as distance_km,
        duration_seconds/60.0 as duration_min,
        CASE 
            WHEN duration_seconds > 0 THEN (distance_meters/duration_seconds) * 3.6 
            ELSE 0 
        END as pace_kmh,
        average_hr,
        COALESCE(training_load, 0) as training_load
    FROM activities 
    WHERE user_id = :user_id 
      AND start_time >= datetime('now', '-' || :weeks || ' days')
      AND duration_seconds > 600  -- Au moins 10 minutes
    ORDER BY start_time DESC
    LIMIT 50
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {'user_id': user_id, 'weeks': period_weeks * 7})
        trends = [dict(row._mapping) for row in result]
    
    return {
        'user_id': user_id,
        'period_weeks': period_weeks,
        'trends_count': len(trends),
        'trends': trends
    }

def get_zones_analysis_data(engine, user_id: int):
    """Analyse des zones d'entraînement basée sur la FC"""
    from sqlalchemy import text
    
    # D'abord, récupérer la FC max
    max_hr_query = text("""
    SELECT MAX(max_hr) as max_hr_recorded,
           COUNT(*) as activities_with_hr
    FROM activities 
    WHERE user_id = :user_id AND max_hr IS NOT NULL
    """)
    
    zones_query = text("""
    SELECT 
        CASE 
            WHEN average_hr <= (SELECT MAX(max_hr) * 0.7 FROM activities WHERE user_id = :user_id AND max_hr IS NOT NULL) 
                THEN 'Zone 1-2 - Endurance'
            WHEN average_hr <= (SELECT MAX(max_hr) * 0.85 FROM activities WHERE user_id = :user_id AND max_hr IS NOT NULL) 
                THEN 'Zone 3-4 - Tempo/Seuil'
            ELSE 'Zone 5 - VO2max'
        END as hr_zone,
        COUNT(*) as activities_count,
        ROUND(AVG(duration_seconds)/60.0, 1) as avg_duration_min,
        ROUND(AVG(average_hr), 0) as avg_hr
    FROM activities 
    WHERE user_id = :user_id 
      AND average_hr IS NOT NULL 
      AND duration_seconds > 300
    GROUP BY 1
    ORDER BY avg_hr
    """)
    
    with engine.connect() as conn:
        max_hr_result = conn.execute(max_hr_query, {'user_id': user_id}).fetchone()
        zones_result = conn.execute(zones_query, {'user_id': user_id})
        zones = [dict(row._mapping) for row in zones_result]
    
    max_hr_info = dict(max_hr_result._mapping) if max_hr_result else {}
    
    return {
        'user_id': user_id,
        'max_hr_info': max_hr_info,
        'zones_analysis': zones
    }

@app.get("/v1/analytics/trends/{user_id}", tags=["Analytics E1"])
async def get_performance_trends(
    user_id: int,
    fastapi_request: Request,
    period_weeks: int = 12,
    api_key: str = Depends(get_api_key)
):
    """Analyse des tendances de performance (SQLAlchemy E1)"""
    
    engine = fastapi_request.app.state.analytics_engine
    if not engine:
        raise HTTPException(status_code=503, detail="Moteur analytics non disponible")
    
    try:
        trends = get_performance_trends_data(engine, user_id, period_weeks)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analytics trends: {str(e)}")

@app.get("/v1/analytics/zones/{user_id}", tags=["Analytics E1"])
async def get_training_zones_analysis(
    user_id: int,
    fastapi_request: Request,
    api_key: str = Depends(get_api_key)
):
    """Analyse des zones d'entraînement FC (SQLAlchemy E1)"""
    
    engine = fastapi_request.app.state.analytics_engine
    if not engine:
        raise HTTPException(status_code=503, detail="Moteur analytics non disponible")
    
    try:
        zones_analysis = get_zones_analysis_data(engine, user_id)
        return zones_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analytics zones: {str(e)}")

@app.get("/v1/analytics/dashboard/{user_id}", tags=["Analytics E1"])
async def get_analytics_dashboard(
    user_id: int,
    fastapi_request: Request,
    period_weeks: int = 12,
    api_key: str = Depends(get_api_key)
):
    """Dashboard complet analytics (SQLAlchemy E1)"""
    
    engine = fastapi_request.app.state.analytics_engine
    if not engine:
        raise HTTPException(status_code=503, detail="Moteur analytics non disponible")
    
    try:
        dashboard_data = {
            'user_id': user_id,
            'period_weeks': period_weeks,
            'generated_at': datetime.now().isoformat(),
        }
        
        # Récupérer les analyses
        try:
            dashboard_data['trends'] = get_performance_trends_data(engine, user_id, period_weeks)
        except Exception as e:
            dashboard_data['trends'] = {'error': str(e)}
            
        try:
            dashboard_data['zones'] = get_zones_analysis_data(engine, user_id)
        except Exception as e:
            dashboard_data['zones'] = {'error': str(e)}
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur dashboard analytics: {str(e)}")


def start_api():
    """Démarrer le serveur API"""
    uvicorn.run(app, host=API_HOST, port=API_PORT)

if __name__ == "__main__":
    start_api()