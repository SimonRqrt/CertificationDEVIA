"""
Router pour les endpoints de coaching IA
"""

import json
import time
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
# SOLUTION DIRECTE: Métriques sans CallbackHandler 
from prometheus_client import Counter
from direct_metrics import collect_openai_metrics

# Métrique pour les plans générés
training_plans_generated = Counter('training_plans_generated_total', 'Nombre total de plans d entrainement generes')

from models.schemas import ChatRequest, SimpleTrainingPlanRequest, TrainingPlanRequest, TrainingPlanResponse
from services.ai_service import AIService
from config.security import get_api_key
from config.settings import RATE_LIMIT_COACHING, RATE_LIMIT_LEGACY
from middleware.rate_limit import limiter, RATE_LIMITING_AVAILABLE

router = APIRouter(prefix="/v1/coaching", tags=["Coaching IA"])

@router.post("/chat")
async def chat_with_coach(
    chat_request: ChatRequest,
    request: Request
):
    """Chat avec le coach IA (authentification Django JWT)"""
    
    coaching_agent = request.app.state.coaching_agent
    ai_service = AIService(coaching_agent)
    
    async def stream_response():
        async for chunk in ai_service.chat_stream(chat_request):
            yield chunk
    
    return StreamingResponse(stream_response(), media_type="application/x-ndjson")

@router.post("/chat-legacy")
async def chat_with_coach_legacy(
    chat_request: ChatRequest,
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """Chat avec le coach IA (méthode legacy avec clé API)"""
    
    coaching_agent = request.app.state.coaching_agent
    ai_service = AIService(coaching_agent)
    
    async def stream_response():
        async for chunk in ai_service.chat_legacy_stream(chat_request):
            yield chunk
    
    return StreamingResponse(stream_response(), media_type="application/x-ndjson")

@router.post("/generate-training-plan")
async def generate_training_plan_simple(
    plan_request: SimpleTrainingPlanRequest,
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """Génération simplifiée de plan pour Django"""
    
    try:
        coaching_agent = request.app.state.coaching_agent
        ai_service = AIService(coaching_agent)
        
        result = await ai_service.generate_training_plan(plan_request)
        
        # Incrémenter métriques (les métriques OpenAI sont automatiquement gérées par advanced_agent)
        training_plans_generated.inc()
        # Les vrais appels OpenAI génèrent automatiquement AI_REQUESTS_TOTAL, AI_COST_USD_TOTAL etc.
        
        return result
        
    except Exception as e:
        print(f"Exception dans génération plan: {str(e)}")
        return {"error": f"Erreur génération plan: {str(e)}"}

@router.post("/generate-training-plan-advanced", response_model=TrainingPlanResponse)
async def generate_training_plan_advanced(
    plan_request: TrainingPlanRequest,
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """Génération automatique d'un plan d'entraînement personnalisé"""
    
    start_time = time.time()
    
    coaching_agent = request.app.state.coaching_agent
    
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
    
    from langchain_core.messages import HumanMessage
    
    # Générer le plan via l'agent IA avec métriques Prometheus
    thread_id = f"plan-generation-{plan_request.user_id}-{int(start_time)}"
    
    # Configuration standard sans CallbackHandler
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
        
        # Incrémenter la métrique de plans générés + collecter métriques OpenAI
        training_plans_generated.inc()
        
        # SOLUTION DIRECTE: Collecter métriques OpenAI après génération
        collect_openai_metrics(
            endpoint="/api/plan-generation",
            duration=generation_time,
            status="200"
        )
        
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
        from rich import print as rprint
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