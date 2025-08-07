#!/usr/bin/env python3
"""
API Views pour l'agent IA de coaching
Endpoints Django REST pour remplacer/compléter FastAPI
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from django.http import JsonResponse, StreamingHttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.conf import settings
from django.db.models import Count, Sum, Avg
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import uuid
import time

from activities.models import Activity
from accounts.models import User
from .models import CoachingSession

log = logging.getLogger(__name__)

# Import de l'agent IA depuis E3
try:
    import sys
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    sys.path.append(str(project_root))
    
    from E3_model_IA.scripts.advanced_agent import get_coaching_graph
    from langchain_core.messages import HumanMessage
    AGENT_IA_AVAILABLE = True
except ImportError as e:
    log.warning(f"Agent IA non disponible: {e}")
    AGENT_IA_AVAILABLE = False

# Cache pour l'agent IA
_coaching_agent = None

async def get_agent_ia():
    """Récupérer l'instance de l'agent IA (cache)"""
    global _coaching_agent
    if _coaching_agent is None and AGENT_IA_AVAILABLE:
        try:
            _coaching_agent = await get_coaching_graph()
        except Exception as e:
            log.error(f"Erreur chargement agent IA: {e}")
    return _coaching_agent

# ===== ENDPOINTS API AGENT IA =====

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_with_coach(request):
    """
    Chat avec l'agent IA de coaching
    Endpoint Django REST équivalent à FastAPI
    """
    try:
        data = request.data
        message = data.get('message', '')
        thread_id = data.get('thread_id')
        
        if not message:
            return Response({
                'error': 'Message requis'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        # Récupérer le contexte utilisateur
        user_context = get_user_context(user)
        
        # Construire le message avec contexte
        context_info = f"""
        Utilisateur: {user.first_name} {user.last_name} ({user.email})
        Statistiques: {user_context.get('stats', {})}
        """
        
        full_input = f"Contexte utilisateur: {context_info}\n\nMessage: {message}"
        thread_id = thread_id or f"user-thread-{user.id}"
        
        # Appel synchrone à l'agent IA
        if not AGENT_IA_AVAILABLE:
            return Response({
                'response': 'Agent IA temporairement indisponible. Configuration en cours.',
                'thread_id': thread_id,
                'user_id': user.id
            })
        
        # Pour Django, on fait un appel simplifié
        try:
            agent = asyncio.run(get_agent_ia())
            if not agent:
                return Response({
                    'response': 'Agent IA non initialisé.',
                    'thread_id': thread_id,
                    'user_id': user.id
                })
            
            config = {"configurable": {"thread_id": thread_id}}
            mode = "streamlit"  # Mode par défaut pour Django
            
            # Récupération synchrone de la réponse
            response_parts = []
            result = asyncio.run(agent.astream({
                "messages": [HumanMessage(content=full_input)], 
                "mode": mode
            }, config=config))
            
            async def collect_response():
                parts = []
                async for event in result:
                    for step in event.values():
                        message_obj = step["messages"][-1]
                        if hasattr(message_obj, 'content') and message_obj.content:
                            parts.append(message_obj.content)
                return ''.join(parts)
            
            ai_response = asyncio.run(collect_response())
            
            # Sauvegarder la session
            session_data = {
                'user_message': message,
                'ai_response': ai_response,
                'context_data': user_context,
                'thread_id': thread_id
            }
            
            CoachingSession.objects.create(
                user=user,
                session_id=str(uuid.uuid4()),
                title=message[:100],
                user_message=message,
                ai_response=ai_response,
                context_data=user_context,
                thread_id=thread_id
            )
            
            return Response({
                'response': ai_response,
                'thread_id': thread_id,
                'user_id': user.id,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            log.error(f"Erreur agent IA: {e}")
            return Response({
                'error': f'Erreur agent IA: {str(e)}',
                'fallback_response': 'Je rencontre des difficultés techniques. Pouvez-vous reformuler votre question ?'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        log.error(f"Erreur chat coaching: {e}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_training_plan(request):
    """
    Génération de plan d'entraînement via agent IA
    Endpoint Django équivalent à FastAPI
    """
    try:
        data = request.data
        user = request.user
        
        # Validation des données requises
        required_fields = ['running_goal', 'training_preferences', 'personal_info']
        for field in required_fields:
            if field not in data:
                return Response({
                    'error': f'Champ requis manquant: {field}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Construction du prompt
        personal_info = data['personal_info']
        running_goal = data['running_goal']
        training_preferences = data['training_preferences']
        
        # Récupérer activités récentes
        recent_activities = get_recent_activities(user)
        user_context = get_user_context(user)
        
        prompt = f"""
        GÉNÉRATION DE PLAN D'ENTRAÎNEMENT PERSONNALISÉ
        
        UTILISATEUR:
        - ID: {user.id}
        - Email: {user.email}
        - Âge: {personal_info.get('age')} ans
        - Poids: {personal_info.get('weight')} kg
        - Niveau: {personal_info.get('experience_level')}
        
        OBJECTIF RUNNING:
        - Type: {running_goal.get('race_type')}
        - Date cible: {running_goal.get('target_date', 'Non définie')}
        - Temps objectif: {running_goal.get('target_time', 'Non défini')}
        
        PRÉFÉRENCES D'ENTRAÎNEMENT:
        - Séances par semaine: {training_preferences.get('sessions_per_week')}
        - Jours disponibles: {', '.join(training_preferences.get('available_days', []))}
        
        HISTORIQUE RÉCENT:
        {json.dumps(recent_activities, indent=2)}
        
        TÂCHE:
        Génère un plan d'entraînement personnalisé au format JSON avec:
        1. Un nom accrocheur pour le plan
        2. Une description motivante (2-3 phrases)
        3. Durée en semaines (8-16 semaines recommandées)
        4. Liste détaillée des séances avec nom, description, type, durée
        5. Liste de 3-5 recommandations personnalisées
        
        RÉPONDS UNIQUEMENT EN JSON VALIDE, sans texte additionnel.
        """
        
        if not AGENT_IA_AVAILABLE:
            # Plan de fallback
            return Response({
                'name': f"Plan {running_goal.get('race_type', 'Running').title()}",
                'description': "Plan d'entraînement personnalisé généré par Django",
                'duration_weeks': 12,
                'sessions': [
                    {
                        'name': 'Course facile',
                        'description': 'Course à allure conversationnelle',
                        'type': 'easy_run',
                        'duration_minutes': 30,
                        'distance_km': 5
                    }
                ],
                'recommendations': [
                    "Augmentez progressivement votre kilométrage",
                    "Respectez vos zones de fréquence cardiaque",
                    "N'oubliez pas les séances de récupération"
                ],
                'generated_by': 'Django (Agent IA indisponible)'
            })
        
        # Génération via agent IA
        try:
            agent = asyncio.run(get_agent_ia())
            if not agent:
                return Response({
                    'error': 'Agent IA non initialisé'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            thread_id = f"plan-generation-{user.id}-{int(time.time())}"
            config = {"configurable": {"thread_id": thread_id}}
            
            # Collecte de la réponse
            async def generate_plan():
                ai_response_parts = []
                async for event in agent.astream({
                    "messages": [HumanMessage(content=prompt)]
                }, config=config):
                    for step in event.values():
                        message_obj = step["messages"][-1]
                        if hasattr(message_obj, 'content') and message_obj.content:
                            ai_response_parts.append(message_obj.content)
                return ''.join(ai_response_parts)
            
            ai_response = asyncio.run(generate_plan())
            
            # Parsing JSON de la réponse
            try:
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                
                if json_start == -1 or json_end == 0:
                    raise ValueError("Aucun JSON trouvé dans la réponse")
                
                json_response = ai_response[json_start:json_end]
                plan_data = json.loads(json_response)
                
                # Validation et valeurs par défaut
                plan_data.setdefault('name', f"Plan {running_goal.get('race_type', 'Running').title()}")
                plan_data.setdefault('description', "Plan d'entraînement personnalisé généré par IA")
                plan_data.setdefault('duration_weeks', 12)
                plan_data.setdefault('sessions', [])
                plan_data.setdefault('recommendations', [])
                plan_data['generated_by'] = 'Django + Agent IA'
                
                return Response(plan_data)
                
            except (json.JSONDecodeError, ValueError) as e:
                log.error(f"Erreur parsing JSON IA: {e}")
                # Fallback plan
                return Response({
                    'name': f"Plan {running_goal.get('race_type', 'Running').title()}",
                    'description': "Plan d'entraînement personnalisé (fallback)",
                    'duration_weeks': 12,
                    'sessions': [],
                    'recommendations': [
                        "Augmentez progressivement votre kilométrage",
                        "Respectez vos zones de fréquence cardiaque"
                    ],
                    'generated_by': 'Django (Fallback)',
                    'note': 'Plan générique - Agent IA en cours de calibration'
                })
                
        except Exception as e:
            log.error(f"Erreur génération plan: {e}")
            return Response({
                'error': f'Erreur génération plan: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        log.error(f"Erreur endpoint génération plan: {e}")
        return Response({
            'error': 'Erreur interne du serveur'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_coaching_context(request):
    """
    Récupérer le contexte utilisateur pour le coaching
    """
    try:
        user = request.user
        context = get_user_context(user)
        return Response(context)
        
    except Exception as e:
        log.error(f"Erreur contexte utilisateur: {e}")
        return Response({
            'error': 'Erreur récupération contexte'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def coaching_sessions_history(request):
    """
    Historique des sessions de coaching
    """
    try:
        user = request.user
        limit = request.GET.get('limit', 20)
        
        sessions = CoachingSession.objects.filter(
            user=user
        ).order_by('-created_at')[:int(limit)]
        
        sessions_data = []
        for session in sessions:
            sessions_data.append({
                'session_id': session.session_id,
                'title': session.title,
                'user_message': session.user_message,
                'ai_response': session.ai_response,
                'created_at': session.created_at.isoformat(),
                'thread_id': session.thread_id
            })
        
        return Response({
            'user_id': user.id,
            'total_sessions': len(sessions_data),
            'sessions': sessions_data
        })
        
    except Exception as e:
        log.error(f"Erreur historique sessions: {e}")
        return Response({
            'error': 'Erreur récupération historique'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ===== UTILITAIRES =====

def get_user_context(user: User) -> Dict[str, Any]:
    """Construire le contexte utilisateur pour l'IA"""
    try:
        # Statistiques des activités
        activities = Activity.objects.filter(user=user)
        
        if not activities.exists():
            return {
                'stats': {
                    'total_activities': 0,
                    'message': 'Aucune activité trouvée'
                }
            }
        
        stats = activities.aggregate(
            total_count=Count('id'),
            total_distance=Sum('distance_meters'),
            total_duration=Sum('duration_seconds'),
            avg_hr=Avg('average_hr')
        )
        
        # Activités récentes (30 derniers jours)
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_activities = activities.filter(
            start_time__gte=recent_cutoff
        ).count()
        
        # Dernière activité
        last_activity = activities.order_by('-start_time').first()
        
        context = {
            'stats': {
                'total_activities': stats['total_count'] or 0,
                'total_distance_km': round((stats['total_distance'] or 0) / 1000, 2),
                'total_duration_hours': round((stats['total_duration'] or 0) / 3600, 1),
                'avg_heart_rate': round(stats['avg_hr']) if stats['avg_hr'] else None,
                'recent_activities_30d': recent_activities,
                'last_activity_date': last_activity.start_time.isoformat() if last_activity else None
            },
            'user_info': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }
        
        return context
        
    except Exception as e:
        log.error(f"Erreur construction contexte: {e}")
        return {'error': str(e)}

def get_recent_activities(user: User, days: int = 90) -> Dict[str, Any]:
    """Récupérer les activités récentes pour le contexte"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        activities = Activity.objects.filter(
            user=user,
            start_time__gte=cutoff_date
        ).order_by('-start_time')[:10]  # Limite à 10 activités récentes
        
        activities_data = []
        for activity in activities:
            activities_data.append({
                'id': activity.id,
                'name': activity.activity_name,
                'type': activity.activity_type,
                'start_time': activity.start_time.isoformat(),
                'duration_minutes': round(activity.duration_seconds / 60) if activity.duration_seconds else 0,
                'distance_km': round(activity.distance_meters / 1000, 2) if activity.distance_meters else 0,
                'average_hr': activity.average_hr,
                'calories': activity.calories
            })
        
        return {
            'period_days': days,
            'total_activities': len(activities_data),
            'activities': activities_data
        }
        
    except Exception as e:
        log.error(f"Erreur récupération activités récentes: {e}")
        return {'error': str(e)}