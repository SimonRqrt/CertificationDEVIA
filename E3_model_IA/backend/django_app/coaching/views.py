from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView, ListView, DetailView
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta
import json
import requests
import os
from django.conf import settings

from .models import TrainingPlan, WorkoutSession, Goal, PerformanceMetrics, CoachingSession
from .forms import (
    RunningGoalWizardForm, PersonalInfoForm, TrainingPreferencesForm,
    PlanGenerationForm, QuickGoalForm
)
from .simple_forms import SimplePlanGenerationForm
from activities.models import Activity
import re

# ===== UTILITAIRES PARSING AGENT IA =====

def parse_training_schedule(agent_response_text):
    """
    Parse la réponse de l'agent IA pour extraire le planning d'entraînement sous forme de tableau structuré.
    Retourne un dictionnaire avec les données du planning.
    """
    # Rechercher les tableaux dans le texte
    lines = agent_response_text.split('\n')
    schedule_data = []
    
    # Patterns pour détecter les lignes de tableau
    table_patterns = [
        r'\|.*\|',  # Format Markdown table
        r'(Jour|Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi|Dimanche).*:',  # Format texte
        r'Semaine \d+',  # Indicateur de semaine
    ]
    
    current_week = 1
    current_day = ""
    
    for line in lines:
        line = line.strip()
        
        # Détecter une nouvelle semaine
        week_match = re.search(r'Semaine (\d+)', line, re.IGNORECASE)
        if week_match:
            current_week = int(week_match.group(1))
            continue
            
        # Détecter une ligne de tableau Markdown
        if '|' in line and line.count('|') >= 3:
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if len(cells) >= 3 and not all('-' in cell for cell in cells):  # Ignorer les séparateurs
                # Parser selon le nombre de colonnes
                if len(cells) >= 4:
                    schedule_data.append({
                        'week': current_week,
                        'day': cells[0],
                        'type': cells[1],
                        'duration': cells[2],
                        'description': cells[3] if len(cells) > 3 else '',
                        'intensity': cells[4] if len(cells) > 4 else ''
                    })
        
        # Détecter format texte (ex: "Lundi: Endurance - 45 min")
        elif ':' in line:
            day_match = re.match(r'(Lundi|Mardi|Mercredi|Jeudi|Vendredi|Samedi|Dimanche|Jour \d+)\s*:\s*(.+)', line, re.IGNORECASE)
            if day_match:
                day = day_match.group(1)
                content = day_match.group(2)
                
                # Extraire type et durée
                duration_match = re.search(r'(\d+)\s*(min|h|km)', content, re.IGNORECASE)
                duration = duration_match.group(0) if duration_match else ''
                
                # Extraire type d'entraînement
                training_types = ['endurance', 'fractionné', 'interval', 'récupération', 'repos', 'sortie longue', 'tempo']
                training_type = ''
                for t_type in training_types:
                    if t_type.lower() in content.lower():
                        training_type = t_type.title()
                        break
                
                schedule_data.append({
                    'week': current_week,
                    'day': day,
                    'type': training_type,
                    'duration': duration,
                    'description': content,
                    'intensity': ''
                })
    
    # Calculer les statistiques correctement
    weeks = set(s['week'] for s in schedule_data)
    active_sessions = [s for s in schedule_data if s['type'] and s['type'].lower() not in ['repos', '-', '']]
    
    return {
        'schedule': schedule_data,
        'total_weeks': len(weeks) if weeks else 1,
        'total_sessions': len(active_sessions),
        'sessions_per_week': len(active_sessions) // max(len(weeks), 1) if weeks else len(active_sessions)
    }

# ===== INTERFACE SIMPLIFIÉE GÉNÉRATION PLAN =====

def simple_plan_generator(request):
    """Vue simplifiée pour générer un plan d'entraînement avec l'IA"""
    
    # Pour le moment, créer un utilisateur fictif pour les tests
    if not request.user.is_authenticated:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            request.user = User.objects.get(id=1)
        except User.DoesNotExist:
            request.user = User.objects.create_user(
                username='demo', 
                email='demo@example.com', 
                password='demo123'
            )
    
    if request.method == 'POST':
        form = SimplePlanGenerationForm(request.POST)
        if form.is_valid():
            # Récupérer les données du formulaire
            form_data = form.cleaned_data
            
            try:
                # Analyser automatiquement les données existantes de l'utilisateur
                user_data = analyze_user_activities(request.user)
                
                # Générer le plan directement avec l'agent avancé (sans FastAPI pour éviter les problèmes de dépendances)
                plan_response = generate_fallback_plan_with_agent(request.user, form_data, user_data)
                
                if plan_response.get('success'):
                    # Sauvegarder automatiquement le plan généré
                    saved_plan = save_generated_plan(request.user, form_data, plan_response['plan'], user_data)
                    
                    messages.success(request, 'Plan d\'entraînement généré et sauvegardé avec succès !')
                    return render(request, 'coaching/simple_plan_result.html', {
                        'plan': plan_response['plan'],
                        'form_data': form_data,
                        'user_data': user_data,
                        'saved_plan': saved_plan  # Passer l'objet sauvegardé pour affichage
                    })
                else:
                    messages.error(request, f'Erreur lors de la génération : {plan_response.get("error", "Erreur inconnue")}')
                    
            except Exception as e:
                messages.error(request, f'Erreur technique : {str(e)}')
                
    else:
        form = SimplePlanGenerationForm()
    
    # Récupérer les statistiques utilisateur pour affichage
    user_stats = get_user_quick_stats(request.user)
    
    return render(request, 'coaching/simple_plan_generator.html', {
        'form': form,
        'user_stats': user_stats
    })


def analyze_user_activities(user):
    """Analyse automatique des activités utilisateur"""
    from django.db import connection
    
    try:
        # Analyser les données depuis la table Django/Supabase activities_activity
        with connection.cursor() as cursor:
            # Statistiques générales
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_activities,
                    AVG(CAST(distance_meters AS FLOAT)) as avg_distance_meters,
                    AVG(CAST(duration_seconds AS FLOAT)) as avg_duration_seconds,
                    MAX(CAST(distance_meters AS FLOAT)) as max_distance_meters,
                    AVG(CASE WHEN average_hr IS NOT NULL THEN CAST(average_hr AS FLOAT) END) as avg_hr
                FROM activities_activity 
                WHERE user_id = %s
                AND (activity_type IN ('running', 'treadmill_running') 
                   OR activity_type LIKE '%%running%%' 
                   OR activity_type LIKE '%%course%%')
            """, [user.id])
            stats = cursor.fetchone()
            
            # Activités récentes (3 derniers mois)
            cursor.execute("""
                SELECT 
                    activity_name, distance_meters, duration_seconds, start_time
                FROM activities_activity 
                WHERE user_id = %s
                AND (activity_type IN ('running', 'treadmill_running') 
                       OR activity_type LIKE '%%running%%' 
                       OR activity_type LIKE '%%course%%')
                AND start_time >= datetime('now', '-3 months')
                ORDER BY start_time DESC
                LIMIT 10
            """, [user.id])
            recent_activities = cursor.fetchall()
            
        return {
            'total_activities': int(stats[0]) if stats[0] else 0,
            'avg_distance_km': round(float(stats[1]) / 1000, 1) if stats[1] else 0,
            'avg_duration_min': round(float(stats[2]) / 60, 1) if stats[2] else 0,
            'max_distance_km': round(float(stats[3]) / 1000, 1) if stats[3] else 0,
            'avg_heart_rate': round(float(stats[4]), 0) if stats[4] else None,
            'recent_activities': [
                {
                    'name': act[0],
                    'distance': round(float(act[1]) / 1000, 1) if act[1] else 0,
                    'duration_min': round(float(act[2]) / 60, 1) if act[2] else 0,
                    'date': act[3].strftime('%Y-%m-%d') if act[3] else ''
                }
                for act in recent_activities
            ] if recent_activities else []
        }
        
    except Exception as e:
        return {
            'total_activities': 0,
            'avg_distance_km': 0,
            'avg_duration_min': 0,
            'max_distance_km': 0,
            'avg_heart_rate': None,
            'recent_activities': [],
            'error': f'Erreur d\'analyse : {str(e)}'
        }


def generate_simple_plan_with_ai(user, form_data, user_data):
    """Génère un plan d'entraînement simple avec l'IA utilisant advanced_agent.py"""
    
    try:
        # URL de l'API FastAPI
        fastapi_url = getattr(settings, 'FASTAPI_URL', 'http://fastapi:8000')
        
        # Préparer le payload simplifié compatible avec advanced_agent.py
        payload = {
            'user_email': user.email,
            'user_id': user.id,
            'goal': form_data['goal'],
            'level': form_data['level'],
            'sessions_per_week': int(form_data['sessions_per_week']),
            'target_date': form_data['target_date'].isoformat() if form_data.get('target_date') else None,
            'additional_notes': form_data.get('additional_notes', ''),
            'user_activities_analysis': user_data,
            'use_advanced_agent': True  # Flag pour utiliser advanced_agent.py
        }
        
        # Appel à l'API FastAPI
        response = requests.post(
            f'{fastapi_url}/v1/coaching/generate-simple-plan',
            json=payload,
            timeout=60  # Augmenté pour l'agent avancé
        )
        
        if response.status_code == 200:
            return {
                'success': True,
                'plan': response.json()
            }
        else:
            return {
                'success': False,
                'error': f'API Error: {response.status_code}'
            }
            
    except requests.RequestException as e:
        # Fallback : génération locale avec advanced_agent.py
        return generate_fallback_plan_with_agent(user, form_data, user_data)
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def generate_fallback_plan_with_agent(user, form_data, user_data):
    """Plan d'entraînement avec Agent IA avancé (même que Streamlit)"""
    
    try:
        # Utiliser le véritable agent conversationnel comme Streamlit
        return generate_plan_with_advanced_agent(user, form_data, user_data)
    except Exception as e:
        # Si l'agent avancé échoue, fallback vers la logique simplifiée
        return generate_plan_with_simple_logic(user, form_data, user_data)


def generate_plan_with_advanced_agent(user, form_data, user_data):
    """Génère un plan avec l'agent conversationnel avancé (comme Streamlit)"""
    
    # Construire un prompt sophistiqué pour l'agent (comme Coach Michael)
    goal = form_data['goal']
    level = form_data['level']
    sessions = int(form_data['sessions_per_week'])
    target_date = form_data.get('target_date')
    additional_notes = form_data.get('additional_notes', '')
    
    # Données contextuelles enrichies
    total_activities = user_data.get('total_activities', 0)
    avg_distance = user_data.get('avg_distance_km', 0)
    avg_duration = user_data.get('avg_duration_min', 0)
    avg_hr = user_data.get('avg_heart_rate', 0)
    recent_activities = user_data.get('recent_activities', [])
    
    # Construire un prompt contextualisé comme l'agent avancé
    agent_prompt = f"""
Bonjour Coach Michael ! J'ai besoin de ton expertise pour créer un plan d'entraînement personnalisé.

**MON PROFIL :**
- Utilisateur : {user.first_name} {user.last_name} ({user.email})
- Objectif : {goal}
- Niveau déclaré : {level}
- Séances souhaitées par semaine : {sessions}
- Date cible : {target_date.strftime('%d/%m/%Y') if target_date else 'Pas de date limite fixe'}
- Notes supplémentaires : {additional_notes if additional_notes else 'Aucune'}

**MON HISTORIQUE D'ENTRAÎNEMENT :**
- Nombre total d'activités de course : {total_activities}
- Distance moyenne par sortie : {avg_distance:.1f} km
- Durée moyenne par sortie : {avg_duration:.0f} minutes
- Fréquence cardiaque moyenne : {avg_hr:.0f} bpm (si disponible)

**MES 5 DERNIÈRES ACTIVITÉS :**
{chr(10).join([f"- {act['date']}: {act['distance']:.1f}km en {act['duration_min']:.0f}min" 
               for act in recent_activities[:5]]) if recent_activities else "Aucune activité récente enregistrée"}

**MA DEMANDE :**
Peux-tu analyser mes données et me créer un plan d'entraînement personnalisé ? 
J'aimerais que tu commences par analyser mes métriques avec tes outils, puis que tu recherches les principes d'entraînement adaptés à mon profil.

Utilise ton format de tableau habituel pour me présenter le plan hebdomadaire, et n'hésite pas à me donner tes conseils d'expert !

Merci Coach ! 🏃‍♂️
"""
    
    # Appeler l'endpoint FastAPI avec l'agent conversationnel
    fastapi_url = getattr(settings, 'FASTAPI_URL', 'http://fastapi:8000')
    
    payload = {
        'message': agent_prompt,
        'thread_id': f'django-user-{user.id}-plan-generation',
        'user_id': user.id  # Passer le vrai user_id à FastAPI
    }
    
    try:
        # Appel avec clé API (même méthode que Streamlit)
        api_key = os.getenv('API_KEY', 'default_key')
        headers = {'X-API-Key': api_key, 'Content-Type': 'application/json'}
        
        response = requests.post(
            f'{fastapi_url}/v1/coaching/chat-legacy',
            json=payload,
            headers=headers,
            timeout=120  # 2 minutes pour laisser le temps à l'agent IA
        )
        
        if response.status_code == 200:
            # Traiter la réponse streaming (format ndjson)
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("type") == "content":
                            full_response += data.get("data", "")
                    except:
                        continue
            
            # Parser le planning d'entraînement depuis la réponse
            parsed_schedule = parse_training_schedule(full_response)
            
            return {
                'success': True,
                'plan': {
                    'title': f'Plan {goal} - Analyse Coach IA',
                    'description': full_response,  # Réponse complète de l'agent
                    'weekly_sessions': sessions,
                    'generated_by': 'Coach Michael (Agent IA Avancé)',
                    'user_analysis': user_data,
                    'training_schedule': parsed_schedule,  # Nouveau: planning structuré
                    'recommendations': [
                        "Plan généré par l'agent IA avancé avec analyse de vos données",
                        "Utilise la base de connaissances sportive et vos métriques personnelles",
                        "Ajusté automatiquement selon votre profil et historique"
                    ]
                }
            }
        else:
            raise Exception(f'Erreur API {response.status_code}: {response.text}')
            
    except Exception as e:
        raise Exception(f'Erreur lors de l\'appel à l\'agent avancé: {str(e)}')


def generate_plan_with_simple_logic(user, form_data, user_data):
    """Plan d'entraînement avec logique simplifiée (fallback)"""
    
    # Analyser les données utilisateur pour créer un plan personnalisé
    goal = form_data['goal']
    level = form_data['level']
    sessions = int(form_data['sessions_per_week'])
    
    # Données contextuelles de l'utilisateur
    total_activities = user_data.get('total_activities', 0)
    avg_distance = user_data.get('avg_distance_km', 0)
    avg_duration = user_data.get('avg_duration_min', 0)
    avg_hr = user_data.get('avg_heart_rate', 0)
    
    # Logique IA simplifiée basée sur les données
    try:
        # Déterminer le niveau réel basé sur les données
        actual_level = determine_actual_level(total_activities, avg_distance, avg_duration)
        
        # Générer un plan adaptatif basé sur l'analyse
        plan_content = generate_adaptive_plan(goal, actual_level, sessions, user_data)
        
        # Ajouter des recommandations personnalisées
        recommendations = generate_personalized_recommendations(user_data, goal, level)
        
        return {
            'success': True,
            'plan': {
                'title': f'Plan {goal} - Niveau {actual_level} (Logique simplifiée)',
                'description': plan_content,
                'weekly_sessions': sessions,
                'recommendations': recommendations,
                'generated_by': 'Logique Coach IA simplifiée (fallback)',
                'user_analysis': user_data,
                'adaptations': [
                    f"Niveau ajusté de '{level}' à '{actual_level}' basé sur vos {total_activities} activités",
                    f"Plan adapté pour distance moyenne de {avg_distance}km en {avg_duration}min",
                    f"Zones cardiaques estimées basées sur FC moyenne de {avg_hr}bpm" if avg_hr else "Ajoutez un capteur cardiaque pour optimiser les zones"
                ]
            }
        }
        
    except Exception as e:
        # Fallback ultime avec plan basique
        return generate_fallback_plan(form_data, user_data)


def determine_actual_level(total_activities, avg_distance, avg_duration):
    """Détermine le niveau réel basé sur l'historique"""
    if total_activities == 0:
        return 'débutant'
    elif total_activities < 10:
        return 'débutant'
    elif avg_distance < 3:
        return 'débutant'
    elif avg_distance < 7 and avg_duration < 45:
        return 'intermédiaire'
    elif avg_distance >= 7 or avg_duration >= 45:
        return 'avancé'
    else:
        return 'intermédiaire'


def generate_adaptive_plan(goal, level, sessions, user_data):
    """Génère un plan adaptatif basé sur l'analyse des données"""
    avg_distance = user_data.get('avg_distance_km', 0)
    
    plan_templates = {
        ('5k', 'débutant'): f"""
## Plan 5K Débutant - {sessions} séances/semaine

**Semaine 1-2: Base aérobie**
- Lundi: Repos ou marche active 30min
- Mercredi: Course/marche alternée 20min (1min course / 1min marche)
- Vendredi: Course continue 15min allure facile
- Dimanche: Sortie longue 25min marche/course

**Semaine 3-4: Progression**
- Augmentation progressive à 2min course / 1min marche
- Course continue jusqu'à 20min
- Sortie longue jusqu'à 30min

**Objectif**: Courir 5km en continu en 8 semaines
""",
        ('5k', 'intermédiaire'): f"""
## Plan 5K Intermédiaire - {sessions} séances/semaine

**Base actuelle analysée**: {avg_distance:.1f}km moyenne, capacité confirmée

**Semaine 1-2: Consolidation**
- Mardi: Course facile 25-30min (allure conversationnelle)
- Jeudi: Fractionné court 6x(1min rapide / 1min récup)
- Samedi: Sortie longue 35-40min allure facile

**Semaine 3-4: Spécifique 5K**
- Fractionné 5x(3min allure 5K / 90s récup)
- Course tempo 15min allure légèrement soutenue

**Objectif**: Améliorer votre temps 5K de 30-60 secondes
""",
        ('10k', 'intermédiaire'): f"""
## Plan 10K Intermédiaire - {sessions} séances/semaine

**Analyse**: Progression de {avg_distance:.1f}km vers 10km

**Phase 1 (Semaines 1-3): Extension endurance**
- Course facile progressive: 30min → 45min
- 1 séance tempo par semaine (20min allure soutenue)
- Sortie longue: 40min → 60min

**Phase 2 (Semaines 4-6): Spécifique 10K**
- Fractionné long: 4x(5min allure 10K / 2min récup)
- Course tempo 25-30min
- Sortie longue avec accélérations

**Objectif**: Courir 10km confortablement en 6-8 semaines
""",
        ('fitness', 'débutant'): f"""
## Plan Forme Générale - {sessions} séances/semaine

**Approche progressive et durable**

**Semaines 1-2: Mise en route**
- 20-25min de course facile ou course/marche
- Focus sur la régularité plutôt que l'intensité
- 1 jour de repos entre chaque séance

**Semaines 3-4: Consolidation**
- 25-30min de course continue
- Introduction d'1 séance légèrement plus soutenue par semaine
- Attention aux signaux du corps

**Objectif**: Établir une routine durable et plaisante
"""
    }
    
    key = (goal, level)
    return plan_templates.get(key, f"""
## Plan {goal.title()} Personnalisé - {sessions} séances/semaine

**Basé sur votre profil**: {user_data.get('total_activities', 0)} activités, {avg_distance:.1f}km moyenne

**Approche adaptative**:
- Progression graduelle adaptée à votre historique
- {sessions} séances par semaine avec récupération intégrée
- Ajustements basés sur vos capacités actuelles

**Structure recommandée**:
- 70% endurance fondamentale (allure conversationnelle)
- 20% allure modérée (légèrement soutenue)
- 10% travail intensif (selon progression)

Votre coach IA s'adapte automatiquement à vos performances !
    """)


def generate_personalized_recommendations(user_data, goal, level):
    """Génère des recommandations personnalisées"""
    recommendations = []
    
    total_activities = user_data.get('total_activities', 0)
    avg_distance = user_data.get('avg_distance_km', 0)
    avg_hr = user_data.get('avg_heart_rate', 0)
    
    # Recommandations basées sur l'historique
    if total_activities == 0:
        recommendations.extend([
            "🚀 Commencez par 3 sorties courtes par semaine",
            "📱 Enregistrez vos activités pour un suivi personnalisé",
            "👟 Investissez dans de bonnes chaussures de course"
        ])
    elif total_activities < 20:
        recommendations.extend([
            "📈 Augmentez progressivement votre fréquence d'entraînement",
            "⏱️ Focalisez-vous sur la durée plutôt que la vitesse",
            "🔄 Alternez les intensités pour éviter la monotonie"
        ])
    
    # Recommandations basées sur la distance moyenne
    if avg_distance < 3:
        recommendations.append("🎯 Travaillez l'extension de vos sorties jusqu'à 5km")
    elif avg_distance > 8:
        recommendations.append("💪 Excellent volume ! Intégrez du travail qualitatif")
    
    # Recommandations cardiaque
    if avg_hr == 0:
        recommendations.append("❤️ Utilisez un capteur cardiaque pour optimiser vos zones")
    elif avg_hr > 170:
        recommendations.append("⚠️ Attention aux allures trop soutenues - privilégiez l'endurance")
    
    # Recommandations par objectif
    goal_recommendations = {
        '5k': ["🏃‍♂️ Intégrez 1 séance de fractionné court par semaine", "⏱️ Visez une progression de 10-15s par semaine"],
        '10k': ["🏃‍♀️ Travaillez l'endurance avec des sorties de 45min+", "🎯 Pratiquez l'allure spécifique 10K en fractionné"],
        'fitness': ["😊 Écoutez votre corps et privilégiez le plaisir", "🌟 Variez les parcours pour maintenir la motivation"]
    }
    
    if goal in goal_recommendations:
        recommendations.extend(goal_recommendations[goal])
    
    # Toujours ajouter les recommandations de base
    recommendations.extend([
        "💧 Hydratez-vous avant, pendant et après l'effort",
        "🛌 Respectez au moins 1 jour de repos complet par semaine",
        "🏥 Consultez un médecin en cas de douleur persistante"
    ])
    
    return recommendations[:6]  # Limiter à 6 recommandations


def generate_fallback_plan(form_data, user_data):
    """Plan d'entraînement de base si l'agent n'est pas disponible"""
    
    goal = form_data['goal']
    level = form_data['level']
    sessions = int(form_data['sessions_per_week'])
    
    # Plan basique selon l'objectif
    plan_templates = {
        '5k': {
            'beginner': f"{sessions} séances/semaine : Alternez marche/course, augmentez progressivement.",
            'intermediate': f"{sessions} séances/semaine : Endurance + 1 séance tempo par semaine.",
            'advanced': f"{sessions} séances/semaine : Endurance + fractionné + récupération active."
        },
        '10k': {
            'beginner': f"{sessions} séances/semaine : Construisez d'abord une base d'endurance de 30min.",
            'intermediate': f"{sessions} séances/semaine : Longues sorties + travail au seuil.",
            'advanced': f"{sessions} séances/semaine : Volume + VMA + récupération."
        },
        'fitness': {
            'beginner': f"{sessions} séances/semaine : 20-30min de course facile, écoutez votre corps.",
            'intermediate': f"{sessions} séances/semaine : Variez les plaisirs : endurance, fartlek, côtes.",
            'advanced': f"{sessions} séances/semaine : Maintenez la forme avec 80% endurance, 20% intensité."
        }
    }
    
    plan_text = plan_templates.get(goal, {}).get(level, f"{sessions} séances par semaine adaptées à votre niveau.")
    
    return {
        'success': True,
        'plan': {
            'title': f'Plan {goal} - Niveau {level}',
            'description': plan_text,
            'weekly_sessions': sessions,
            'recommendations': [
                'Échauffez-vous toujours avant de courir',
                'Hydratez-vous régulièrement',
                'Respectez au moins 1 jour de repos par semaine',
                'Augmentez progressivement votre charge d\'entraînement'
            ],
            'user_analysis': user_data
        }
    }


def save_generated_plan(user, form_data, plan_data, user_data):
    """Sauvegarde le plan généré dans la base de données Azure SQL Server"""
    from datetime import datetime, timedelta
    
    try:
        # Calculer les dates du plan
        target_date = form_data.get('target_date')
        if target_date:
            end_date = target_date
            # Estimer 12 semaines de préparation par défaut
            start_date = target_date - timedelta(weeks=12)
        else:
            start_date = timezone.now().date()
            end_date = start_date + timedelta(weeks=12)
        
        # Créer le plan d'entraînement
        training_plan = TrainingPlan.objects.create(
            user=user,
            name=plan_data.get('title', f"Plan {form_data['goal'].upper()}"),
            description=plan_data.get('description', ''),
            goal=form_data['goal'],
            level=form_data['level'], 
            sessions_per_week=int(form_data['sessions_per_week']),
            duration_weeks=12,  # Durée standard
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        
        # Créer un objectif associé si il y a une date cible
        if target_date:
            Goal.objects.create(
                user=user,
                name=f"Objectif {form_data['goal'].upper()}",
                description=f"Atteindre l'objectif {form_data['goal']} le {target_date.strftime('%d/%m/%Y')}",
                goal_type='time_goal',
                target_value=0,  # Valeur par défaut
                target_unit='time',
                target_date=target_date,
                is_active=True
            )
        
        return training_plan
        
    except Exception as e:
        # Log l'erreur mais ne pas faire échouer la génération
        print(f"Erreur sauvegarde plan: {str(e)}")
        return None


def get_user_quick_stats(user):
    """Récupère rapidement les stats utilisateur pour affichage"""
    try:
        user_analysis = analyze_user_activities(user)
        return {
            'total_runs': user_analysis.get('total_activities', 0),
            'avg_distance': user_analysis.get('avg_distance_km', 0),
            'last_activity': user_analysis.get('recent_activities', [{}])[0] if user_analysis.get('recent_activities') else {}
        }
    except:
        return {'total_runs': 0, 'avg_distance': 0, 'last_activity': {}}


# ===== INTERFACE FORMULAIRES OBJECTIFS RUNNING =====

class RunningGoalWizardView(LoginRequiredMixin, TemplateView):
    """Vue principale pour l'assistant objectifs running"""
    template_name = 'coaching/running_goal_wizard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Étape courante (par défaut : 1)
        current_step = int(self.request.GET.get('step', 1))
        context['current_step'] = current_step
        
        # Informations utilisateur existantes
        user_profile = getattr(user, 'profile', None)
        context['user_profile'] = user_profile
        
        # Activités récentes pour analyse
        recent_activities = Activity.objects.filter(
            user=user,
            activity_type='running'
        ).order_by('-start_time')[:10]
        context['recent_activities'] = recent_activities
        
        # Objectifs existants
        active_goals = Goal.objects.filter(user=user, is_active=True)
        context['active_goals'] = active_goals
        
        # Plans d'entraînement actifs
        active_plans = TrainingPlan.objects.filter(user=user, is_active=True)
        context['active_plans'] = active_plans
        
        # Formulaires selon l'étape
        if current_step == 1:
            context['personal_form'] = PersonalInfoForm(user=user)
        elif current_step == 2:
            context['goal_form'] = RunningGoalWizardForm()
        elif current_step == 3:
            context['preferences_form'] = TrainingPreferencesForm()
        elif current_step == 4:
            # Données de session pour génération
            session_data = self.request.session.get('wizard_data', {})
            context['session_data'] = session_data
            context['generation_form'] = PlanGenerationForm()
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Traitement des étapes du wizard"""
        current_step = int(request.POST.get('step', 1))
        
        if current_step == 1:
            return self._process_personal_info(request)
        elif current_step == 2:
            return self._process_running_goal(request)
        elif current_step == 3:
            return self._process_preferences(request)
        elif current_step == 4:
            return self._generate_training_plan(request)
        
        return self.get(request, *args, **kwargs)
    
    def _process_personal_info(self, request):
        """Traitement étape 1 : Informations personnelles"""
        form = PersonalInfoForm(request.POST, user=request.user)
        
        if form.is_valid():
            # Sauvegarder les données en session
            wizard_data = request.session.get('wizard_data', {})
            wizard_data.update({
                'personal_info': form.cleaned_data,
                'step_1_completed': True
            })
            request.session['wizard_data'] = wizard_data
            
            # Rediriger vers étape 2
            return HttpResponseRedirect(reverse('coaching:running_wizard') + '?step=2')
        else:
            # Réafficher avec erreurs
            return render(request, self.template_name, {
                'current_step': 1,
                'personal_form': form,
                'user_profile': getattr(request.user, 'profile', None),
            })
    
    def _process_running_goal(self, request):
        """Traitement étape 2 : Objectif running"""
        form = RunningGoalWizardForm(request.POST)
        
        if form.is_valid():
            wizard_data = request.session.get('wizard_data', {})
            wizard_data.update({
                'running_goal': form.cleaned_data,
                'step_2_completed': True
            })
            request.session['wizard_data'] = wizard_data
            
            return HttpResponseRedirect(reverse('coaching:running_wizard') + '?step=3')
        else:
            return render(request, self.template_name, {
                'current_step': 2,
                'goal_form': form,
            })
    
    def _process_preferences(self, request):
        """Traitement étape 3 : Préférences d'entraînement"""
        form = TrainingPreferencesForm(request.POST)
        
        if form.is_valid():
            wizard_data = request.session.get('wizard_data', {})
            wizard_data.update({
                'training_preferences': form.cleaned_data,
                'step_3_completed': True
            })
            request.session['wizard_data'] = wizard_data
            
            return HttpResponseRedirect(reverse('coaching:running_wizard') + '?step=4')
        else:
            return render(request, self.template_name, {
                'current_step': 3,
                'preferences_form': form,
            })
    
    def _generate_training_plan(self, request):
        """Traitement étape 4 : Génération du plan via FastAPI"""
        wizard_data = request.session.get('wizard_data', {})
        
        if not all([
            wizard_data.get('step_1_completed'),
            wizard_data.get('step_2_completed'),
            wizard_data.get('step_3_completed')
        ]):
            messages.error(request, 'Veuillez compléter toutes les étapes précédentes.')
            return HttpResponseRedirect(reverse('coaching:running_wizard'))
        
        try:
            # Appeler l'API FastAPI pour génération du plan
            plan_data = self._call_fastapi_for_plan_generation(request.user, wizard_data)
            
            # Créer le plan d'entraînement
            with transaction.atomic():
                training_plan = self._create_training_plan(request.user, wizard_data, plan_data)
                
                # Nettoyer la session
                if 'wizard_data' in request.session:
                    del request.session['wizard_data']
                
                messages.success(
                    request, 
                    f'Plan d\'entraînement "{training_plan.name}" créé avec succès!'
                )
                return HttpResponseRedirect(
                    reverse('coaching:plan_detail', kwargs={'pk': training_plan.pk})
                )
        
        except Exception as e:
            messages.error(
                request, 
                f'Erreur lors de la génération du plan : {str(e)}'
            )
            return render(request, self.template_name, {
                'current_step': 4,
                'session_data': wizard_data,
                'generation_form': PlanGenerationForm(),
                'error': str(e)
            })
    
    def _call_fastapi_for_plan_generation(self, user, wizard_data):
        """Appel à l'API FastAPI pour générer le plan"""
        fastapi_url = getattr(settings, 'FASTAPI_URL', 'http://fastapi:8000')
        
        # Récupérer le contexte utilisateur enrichi
        user_context = self._get_user_context_for_ai(user)
        
        # Préparer les données pour l'API
        payload = {
            'user_id': user.id,
            'user_email': user.email,
            'personal_info': wizard_data.get('personal_info', {}),
            'running_goal': wizard_data.get('running_goal', {}),
            'training_preferences': wizard_data.get('training_preferences', {}),
            'recent_activities': self._get_user_activity_summary(user),
            'user_context': user_context
        }
        
        # Headers avec authentification si nécessaire
        headers = {
            'Content-Type': 'application/json',
        }
        
        # Ajouter token JWT si disponible
        if hasattr(user, 'auth_token'):
            headers['Authorization'] = f'Bearer {user.auth_token}'
        
        # Appel API
        response = requests.post(
            f'{fastapi_url}/v1/coaching/generate-training-plan',
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'Erreur API: {response.status_code} - {response.text}')
    
    def _get_user_activity_summary(self, user):
        """Résumé des activités récentes de l'utilisateur avec détails pour l'IA"""
        activities = Activity.objects.filter(
            user=user,
            activity_type='running'
        ).order_by('-start_time')[:20]
        
        if not activities:
            return {
                'total_activities': 0,
                'message': 'Aucune activité running enregistrée'
            }
        
        # Statistiques de base
        total_distance = sum(a.distance_km for a in activities if a.distance_km)
        total_duration = sum(a.duration_seconds for a in activities if a.duration_seconds)
        hr_values = [a.average_hr for a in activities if a.average_hr]
        avg_hr = sum(hr_values) / len(hr_values) if hr_values else None
        
        # Analyse des performances récentes (5 dernières activités)
        recent_activities = activities[:5]
        recent_performances = []
        
        for activity in recent_activities:
            perf = {
                'date': activity.start_time.strftime('%Y-%m-%d'),
                'distance_km': activity.distance_km or 0,
                'duration_minutes': round(activity.duration_seconds / 60, 0) if activity.duration_seconds else 0,
                'pace_per_km': activity.pace_per_km,
                'average_hr': activity.average_hr,
                'perceived_exertion': activity.perceived_exertion,
                'is_race': activity.is_race,
                'notes': activity.notes[:100] if activity.notes else None  # Limiter les notes
            }
            recent_performances.append(perf)
        
        # Tendances (comparaison dernières 5 vs 5 précédentes)
        if len(activities) >= 10:
            recent_5 = activities[:5]
            previous_5 = activities[5:10]
            
            recent_avg_pace = sum([a.average_pace for a in recent_5 if a.average_pace]) / len([a for a in recent_5 if a.average_pace])
            previous_avg_pace = sum([a.average_pace for a in previous_5 if a.average_pace]) / len([a for a in previous_5 if a.average_pace])
            
            pace_trend = 'improving' if recent_avg_pace < previous_avg_pace else 'declining' if recent_avg_pace > previous_avg_pace else 'stable'
        else:
            pace_trend = 'insufficient_data'
        
        # Records personnels récents - refaire la requête depuis Activity
        best_5k = Activity.objects.filter(
            user=user,
            activity_type='running',
            distance_meters__gte=4900, 
            distance_meters__lte=5100
        ).order_by('duration_seconds').first()
        
        best_10k = Activity.objects.filter(
            user=user,
            activity_type='running',
            distance_meters__gte=9900, 
            distance_meters__lte=10100
        ).order_by('duration_seconds').first()
        
        return {
            # Statistiques globales
            'total_activities': len(activities),
            'total_distance_km': round(total_distance, 2),
            'total_duration_hours': round(total_duration / 3600, 2),
            'avg_heart_rate': round(avg_hr, 0) if avg_hr else None,
            'typical_distance': round(total_distance / len(activities), 2) if activities else 0,
            
            # Activité la plus récente
            'most_recent': {
                'date': activities[0].start_time.isoformat(),
                'distance_km': activities[0].distance_km,
                'pace': activities[0].pace_per_km,
                'days_ago': (timezone.now().date() - activities[0].start_time.date()).days
            },
            
            # Performances détaillées récentes
            'recent_performances': recent_performances,
            
            # Analyse des tendances
            'trends': {
                'pace_trend': pace_trend,
                'activity_frequency': len(activities) / 30,  # activités par jour (sur 20 activités)
                'consistency': 'regular' if len(activities) >= 15 else 'irregular'
            },
            
            # Records personnels
            'personal_records': {
                'best_5k_time': best_5k.duration_formatted if best_5k else None,
                'best_5k_date': best_5k.start_time.strftime('%Y-%m-%d') if best_5k else None,
                'best_10k_time': best_10k.duration_formatted if best_10k else None,
                'best_10k_date': best_10k.start_time.strftime('%Y-%m-%d') if best_10k else None,
            },
            
            # Recommandations basées sur l'historique
            'analysis_notes': self._analyze_user_readiness(activities, user)
        }
    
    def _analyze_user_readiness(self, activities, user):
        """Analyse de l'état de forme et recommandations"""
        notes = []
        
        if not activities:
            return ['Utilisateur débutant - aucun historique d\'activités']
        
        # Fréquence d'entraînement
        recent_30_days = [a for a in activities if (timezone.now().date() - a.start_time.date()).days <= 30]
        frequency = len(recent_30_days)
        
        if frequency >= 12:  # 3+ par semaine
            notes.append('Entraînement régulier - bon niveau d\'activité')
        elif frequency >= 8:  # 2 par semaine
            notes.append('Entraînement modéré - peut augmenter progressivement')
        else:
            notes.append('Entraînement irrégulier - commencer doucement')
        
        # Distances parcourues
        avg_distance = sum(a.distance_km for a in activities[:10] if a.distance_km) / len([a for a in activities[:10] if a.distance_km])
        
        if avg_distance >= 10:
            notes.append('Habitude de longues distances - peut viser des objectifs ambitieux')
        elif avg_distance >= 5:
            notes.append('Distances moyennes - progression standard recommandée')
        else:
            notes.append('Courtes distances - privilégier l\'augmentation progressive')
        
        # Blessures récentes (basées sur les notes)
        injury_mentions = [a for a in activities[:5] if a.notes and ('douleur' in a.notes.lower() or 'mal' in a.notes.lower())]
        if injury_mentions:
            notes.append('Attention: mentions de douleurs récentes - plan prudent recommandé')
        
        return notes
    
    def _get_user_context_for_ai(self, user):
        """Récupérer le contexte utilisateur enrichi pour l'IA"""
        context = {}
        
        # Profil utilisateur de base
        if hasattr(user, 'profile'):
            profile = user.profile
            context['user_profile'] = {
                'weight': profile.weight,
                'height': profile.height,
                'birth_date': profile.birth_date.isoformat() if profile.birth_date else None,
                'gender': profile.gender,
                'activity_level': profile.activity_level,
                'main_goal': profile.main_goal,
                'preferred_activity': profile.preferred_activity,
            }
            
            # Zones de fréquence cardiaque si disponibles
            if all([profile.hr_zone_1, profile.hr_zone_2, profile.hr_zone_3, profile.hr_zone_4, profile.hr_zone_5]):
                context['hr_zones'] = {
                    'zone_1': f"{profile.hr_zone_1_min}-{profile.hr_zone_1}" if hasattr(profile, 'hr_zone_1_min') else str(profile.hr_zone_1),
                    'zone_2': f"{profile.hr_zone_2_min}-{profile.hr_zone_2}" if hasattr(profile, 'hr_zone_2_min') else str(profile.hr_zone_2),
                    'zone_3': f"{profile.hr_zone_3_min}-{profile.hr_zone_3}" if hasattr(profile, 'hr_zone_3_min') else str(profile.hr_zone_3),
                    'zone_4': f"{profile.hr_zone_4_min}-{profile.hr_zone_4}" if hasattr(profile, 'hr_zone_4_min') else str(profile.hr_zone_4),
                    'zone_5': f"{profile.hr_zone_5_min}-{profile.hr_zone_5}" if hasattr(profile, 'hr_zone_5_min') else str(profile.hr_zone_5),
                }
            
            # Prédictions de performance si disponibles
            context['predictions'] = {
                'prediction_5k': profile.prediction_5k.strftime('%M:%S') if profile.prediction_5k else None,
                'prediction_10k': profile.prediction_10k.strftime('%M:%S') if profile.prediction_10k else None,
                'prediction_half_marathon': profile.prediction_half_marathon.strftime('%H:%M:%S') if profile.prediction_half_marathon else None,
                'prediction_marathon': profile.prediction_marathon.strftime('%H:%M:%S') if profile.prediction_marathon else None,
            }
        
        # Métriques de performance les plus récentes
        latest_metrics = PerformanceMetrics.objects.filter(user=user).order_by('-calculation_date').first()
        if latest_metrics:
            context['latest_metrics'] = {
                'vma': latest_metrics.vma,
                'vo2_max': latest_metrics.vo2_max,
                'fitness_7d': latest_metrics.fitness_7d,
                'fitness_28d': latest_metrics.fitness_28d,
                'fatigue_7d': latest_metrics.fatigue_7d,
                'form': latest_metrics.form,
                'calculation_date': latest_metrics.calculation_date.isoformat(),
                'recommendation': latest_metrics.recommendation
            }
        
        # Plans d'entraînement précédents (pour éviter les répétitions)
        previous_plans = TrainingPlan.objects.filter(user=user, is_completed=True).order_by('-updated_at')[:3]
        if previous_plans:
            context['previous_plans'] = [
                {
                    'name': plan.name,
                    'goal': plan.goal,
                    'level': plan.level,
                    'duration_weeks': plan.duration_weeks,
                    'sessions_per_week': plan.sessions_per_week,
                    'completion_date': plan.updated_at.isoformat()
                }
                for plan in previous_plans
            ]
        
        # Objectifs actuels pour cohérence
        active_goals = Goal.objects.filter(user=user, is_active=True)
        if active_goals:
            context['current_goals'] = [
                {
                    'name': goal.name,
                    'goal_type': goal.goal_type,
                    'target_value': goal.target_value,
                    'target_unit': goal.target_unit,
                    'current_value': goal.current_value,
                    'progress_percentage': goal.progress_percentage,
                    'target_date': goal.target_date.isoformat() if goal.target_date else None
                }
                for goal in active_goals
            ]
        
        return context
    
    def _create_training_plan(self, user, wizard_data, plan_data):
        """Créer le plan d'entraînement à partir des données générées"""
        goal_data = wizard_data.get('running_goal', {})
        preferences_data = wizard_data.get('training_preferences', {})
        
        # Créer le plan principal
        training_plan = TrainingPlan.objects.create(
            user=user,
            name=plan_data.get('name', f"Plan {goal_data.get('race_type', 'Running').title()}"),
            description=plan_data.get('description', ''),
            goal=goal_data.get('race_type', 'general_fitness'),
            duration_weeks=plan_data.get('duration_weeks', 12),
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(weeks=plan_data.get('duration_weeks', 12)),
            level=preferences_data.get('current_level', 'intermediate'),
            sessions_per_week=preferences_data.get('sessions_per_week', 3),
            is_active=True
        )
        
        # Créer les séances individuelles
        sessions_data = plan_data.get('sessions', [])
        for session_info in sessions_data:
            WorkoutSession.objects.create(
                training_plan=training_plan,
                user=user,
                name=session_info.get('name', ''),
                description=session_info.get('description', ''),
                session_type=session_info.get('type', 'easy_run'),
                planned_date=timezone.now().date() + timedelta(days=session_info.get('day_offset', 0)),
                planned_duration=session_info.get('duration_minutes', 30),
                planned_distance=session_info.get('distance_km'),
                target_hr_zone=session_info.get('hr_zone'),
                status='planned'
            )
        
        # Créer l'objectif associé
        if goal_data.get('target_time'):
            Goal.objects.create(
                user=user,
                name=f"Objectif {goal_data.get('race_type', 'Running').title()}",
                description=f"Terminer en {goal_data.get('target_time')}",
                goal_type='time_goal',
                target_value=self._parse_time_to_seconds(goal_data.get('target_time', '00:30:00')),
                target_unit='seconds',
                target_date=goal_data.get('target_date', timezone.now().date() + timedelta(weeks=12)),
                is_active=True
            )
        
        return training_plan
    
    def _parse_time_to_seconds(self, time_str):
        """Convertir HH:MM:SS en secondes"""
        try:
            h, m, s = map(int, time_str.split(':'))
            return h * 3600 + m * 60 + s
        except:
            return 1800  # 30 minutes par défaut


# ===== GESTION DES PLANS D'ENTRAÎNEMENT =====

class TrainingPlanListView(LoginRequiredMixin, ListView):
    """Liste des plans d'entraînement de l'utilisateur"""
    model = TrainingPlan
    template_name = 'coaching/plan_list.html'
    context_object_name = 'plans'
    paginate_by = 10
    
    def get_queryset(self):
        return TrainingPlan.objects.filter(user=self.request.user).order_by('-created_at')


class TrainingPlanDetailView(LoginRequiredMixin, DetailView):
    """Détail d'un plan d'entraînement"""
    model = TrainingPlan
    template_name = 'coaching/plan_detail.html'
    context_object_name = 'plan'
    
    def get_queryset(self):
        return TrainingPlan.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        plan = self.get_object()
        
        # Sessions du plan
        sessions = plan.sessions.all().order_by('planned_date')
        context['sessions'] = sessions
        
        # Statistiques de progression
        total_sessions = sessions.count()
        completed_sessions = sessions.filter(status='completed').count()
        context['progress_percentage'] = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        # Sessions de la semaine courante
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        context['current_week_sessions'] = sessions.filter(
            planned_date__gte=week_start,
            planned_date__lte=week_end
        )
        
        # Prochaines sessions
        context['upcoming_sessions'] = sessions.filter(
            planned_date__gte=today,
            status='planned'
        )[:5]
        
        return context


# ===== VUES RAPIDES =====

@login_required
def quick_goal_view(request):
    """Vue pour création rapide d'objectif"""
    if request.method == 'POST':
        form = QuickGoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            messages.success(request, f'Objectif "{goal.name}" créé avec succès!')
            return redirect('coaching:goal_list')
    else:
        form = QuickGoalForm()
    
    return render(request, 'coaching/quick_goal.html', {'form': form})


@login_required
def dashboard_coaching_view(request):
    """Dashboard coaching avec vue d'ensemble"""
    user = request.user
    
    # Plans actifs
    active_plans = TrainingPlan.objects.filter(user=user, is_active=True)
    
    # Objectifs actifs
    active_goals = Goal.objects.filter(user=user, is_active=True)
    
    # Sessions à venir
    upcoming_sessions = WorkoutSession.objects.filter(
        user=user,
        planned_date__gte=timezone.now().date(),
        status='planned'
    ).order_by('planned_date')[:5]
    
    # Sessions récentes
    recent_sessions = WorkoutSession.objects.filter(user=user).order_by('-updated_at')[:5]
    
    # Métriques récentes
    latest_metrics = PerformanceMetrics.objects.filter(user=user).order_by('-calculation_date').first()
    
    context = {
        'active_plans': active_plans,
        'active_goals': active_goals,
        'upcoming_sessions': upcoming_sessions,
        'recent_sessions': recent_sessions,
        'latest_metrics': latest_metrics,
    }
    
    return render(request, 'coaching/dashboard.html', context)
