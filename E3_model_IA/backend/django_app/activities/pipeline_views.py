import logging
import sys
import traceback
from pathlib import Path
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.conf import settings
import json

# Ajouter le chemin vers E1_gestion_donnees
project_root = Path(settings.BASE_DIR).parent.parent.parent
sys.path.append(str(project_root))

logger = logging.getLogger(__name__)

@login_required
def pipeline_dashboard(request):
    """Dashboard pour gérer la pipeline de récupération des données Garmin"""
    
    # Informations sur la dernière synchronisation
    from activities.models import Activity
    
    user = request.user
    last_activity = Activity.objects.filter(user=user).order_by('-synced_at').first()
    total_activities = Activity.objects.filter(user=user).count()
    
    # Statistiques récentes (7 derniers jours)
    recent_date = timezone.now() - timezone.timedelta(days=7)
    recent_activities = Activity.objects.filter(
        user=user,
        start_time__gte=recent_date
    ).count()
    
    context = {
        'last_sync': last_activity.synced_at if last_activity else None,
        'total_activities': total_activities,
        'recent_activities': recent_activities,
        'user_email': user.email,
        'pipeline_status': 'ready',  # ready, running, error
    }
    
    return render(request, 'activities/pipeline_dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def trigger_pipeline(request):
    """Déclenche la pipeline de récupération des données Garmin"""
    
    try:
        # Récupérer les paramètres depuis le formulaire
        garmin_email = request.POST.get('garmin_email')
        garmin_password = request.POST.get('garmin_password')
        
        if not garmin_email or not garmin_password:
            return JsonResponse({
                'success': False,
                'error': 'Email et mot de passe Garmin requis'
            })
        
        # Lancer la pipeline en arrière-plan
        result = run_garmin_pipeline_for_user(
            user=request.user,
            garmin_email=garmin_email,
            garmin_password=garmin_password
        )
        
        if result['success']:
            messages.success(request, f"Pipeline exécutée avec succès ! {result['activities_processed']} activités traitées.")
            return JsonResponse({
                'success': True,
                'message': f"Pipeline exécutée avec succès ! {result['activities_processed']} activités traitées.",
                'activities_processed': result['activities_processed']
            })
        else:
            messages.error(request, f"Erreur lors de l'exécution de la pipeline : {result['error']}")
            return JsonResponse({
                'success': False,
                'error': result['error']
            })
            
    except Exception as e:
        logger.error(f"Erreur lors du déclenchement de la pipeline : {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Erreur interne : {str(e)}'
        })


def run_garmin_pipeline_for_user(user, garmin_email: str, garmin_password: str) -> dict:
    """
    Exécute la pipeline de récupération Garmin pour un utilisateur Django
    
    Args:
        user: Instance de l'utilisateur Django
        garmin_email: Email Garmin Connect
        garmin_password: Mot de passe Garmin Connect
        
    Returns:
        dict: Résultat de l'exécution avec success, error, activities_processed
    """
    
    try:
        # Import des modules E1 (fait ici pour éviter les erreurs d'import au démarrage)
        from E1_gestion_donnees.data_manager import connect_garmin, get_all_garmin_activities
        
        logger.info(f"Démarrage de la pipeline Garmin pour l'utilisateur {user.email}")
        
        # 1. Connexion à Garmin avec les identifiants fournis
        try:
            garmin_client = connect_garmin(garmin_email, garmin_password)
            if not garmin_client:
                return {
                    'success': False,
                    'error': 'Impossible de se connecter à Garmin Connect. Vérifiez vos identifiants et réessayez dans quelques minutes.',
                    'activities_processed': 0
                }
        except Exception as auth_error:
            logger.error(f"Erreur d'authentification Garmin : {str(auth_error)}")
            return {
                'success': False,
                'error': f'Erreur d\'authentification Garmin : {str(auth_error)}. Vérifiez vos identifiants ou réessayez plus tard.',
                'activities_processed': 0
            }
        
        # 2. Récupération des activités directement depuis Garmin
        logger.info("Récupération des activités depuis Garmin Connect...")
        raw_activities = get_all_garmin_activities(garmin_client, batch_size=50)
        
        if not raw_activities:
            return {
                'success': False,
                'error': 'Aucune activité trouvée sur votre compte Garmin Connect',
                'activities_processed': 0
            }
        
        # 3. Stockage direct en base Django
        activities_count = store_activities_in_django(user, raw_activities)
        
        logger.info(f"Pipeline terminée avec succès. {activities_count} activités traitées.")
        
        return {
            'success': True,
            'error': None,
            'activities_processed': activities_count
        }
        
    except ImportError as e:
        logger.error(f"Erreur d'import des modules E1 : {str(e)}")
        return {
            'success': False,
            'error': f'Modules de pipeline non disponibles : {str(e)}',
            'activities_processed': 0
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de la pipeline : {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': f'Erreur d\'exécution : {str(e)}',
            'activities_processed': 0
        }


def store_activities_in_django(user, raw_activities: list) -> int:
    """
    Stocke les activités Garmin dans les modèles Django avec prévention de duplication renforcée
    
    Args:
        user: Instance utilisateur Django
        raw_activities: Liste des activités brutes Garmin
        
    Returns:
        int: Nombre d'activités stockées
    """
    from activities.models import Activity
    from django.utils.dateparse import parse_datetime
    from datetime import datetime
    from django.db import transaction
    
    stored_count = 0
    skipped_count = 0
    
    # Récupérer tous les activity_id existants pour cet utilisateur d'un coup
    existing_activity_ids = set(
        Activity.objects.filter(user=user)
        .exclude(activity_id__isnull=True)
        .values_list('activity_id', flat=True)
    )
    
    logger.info(f"Utilisateur {user.email} a déjà {len(existing_activity_ids)} activités")
    
    for activity_data in raw_activities:
        try:
            # Vérification renforcée de duplication
            activity_id = activity_data.get('activityId')
            
            # 1. Vérification par activity_id
            if activity_id and activity_id in existing_activity_ids:
                logger.debug(f"Activité {activity_id} déjà existante (par ID), ignorée")
                skipped_count += 1
                continue
            
            # 2. Vérification par nom et date (au cas où activity_id serait manquant)
            activity_name = activity_data.get('activityName', 'Activité Garmin')
            start_time_str = activity_data.get('startTimeLocal')
            
            if start_time_str:
                try:
                    start_time = parse_datetime(start_time_str)
                    if start_time and Activity.objects.filter(
                        user=user,
                        activity_name=activity_name,
                        start_time=start_time
                    ).exists():
                        logger.debug(f"Activité '{activity_name}' du {start_time} déjà existante (par nom/date), ignorée")
                        skipped_count += 1
                        continue
                except:
                    start_time = timezone.now()
            else:
                start_time = timezone.now()
            
            # Parser end_time
            end_time = None
            if activity_data.get('endTimeLocal'):
                try:
                    end_time = parse_datetime(activity_data.get('endTimeLocal'))
                except:
                    pass
            
            # Utiliser une transaction pour éviter les doublons en cas de concurrence
            with transaction.atomic():
                # Double vérification dans la transaction
                if activity_id and Activity.objects.filter(user=user, activity_id=activity_id).exists():
                    logger.debug(f"Activité {activity_id} créée entre temps, ignorée")
                    skipped_count += 1
                    continue
                
                # Créer la nouvelle activité
                activity = Activity.objects.create(
                    user=user,
                    activity_id=activity_id,
                    activity_name=activity_name,
                    activity_type=map_garmin_activity_type(activity_data.get('activityType', {}).get('typeKey', 'other')),
                    start_time=start_time,
                    end_time=end_time,
                    duration_seconds=int(activity_data.get('duration', 0)) if activity_data.get('duration') else 0,
                    distance_meters=float(activity_data.get('distance', 0)) if activity_data.get('distance') else 0.0,
                    average_speed=activity_data.get('averageSpeed'),
                    max_speed=activity_data.get('maxSpeed'),
                    average_hr=activity_data.get('averageHR'),
                    max_hr=activity_data.get('maxHR'),
                    calories=activity_data.get('calories'),
                    elevation_gain=activity_data.get('elevationGain'),
                    elevation_loss=activity_data.get('elevationLoss'),
                    device_name=activity_data.get('deviceDisplayName', ''),
                    synced_at=timezone.now()
                )
                
                # Ajouter à la liste des IDs existants
                if activity_id:
                    existing_activity_ids.add(activity_id)
                
                stored_count += 1
                logger.info(f"Activité '{activity.activity_name}' stockée avec succès (ID: {activity_id})")
            
        except Exception as e:
            logger.error(f"Erreur lors du stockage d'une activité : {str(e)}")
            continue
    
    logger.info(f"Pipeline terminée : {stored_count} nouvelles activités, {skipped_count} doublons évités")
    return stored_count


def map_garmin_activity_type(garmin_type: str) -> str:
    """
    Mappe les types d'activité Garmin vers les types Django
    
    Args:
        garmin_type: Type d'activité Garmin
        
    Returns:
        str: Type d'activité Django
    """
    mapping = {
        'running': 'running',
        'cycling': 'cycling',
        'swimming': 'swimming',
        'walking': 'walking',
        'hiking': 'hiking',
        'fitness_equipment': 'strength_training',
        'yoga': 'yoga',
    }
    
    return mapping.get(garmin_type.lower(), 'other')


@login_required
def pipeline_logs(request):
    """Affiche les logs de la pipeline"""
    
    # Lire les logs récents (dernières 200 lignes)
    log_content = ""
    logs_found = []
    
    try:
        # 1. Essayer le fichier django.log (où vont les logs actuellement)
        django_log_file = Path(settings.BASE_DIR) / "django.log"
        if django_log_file.exists():
            with open(django_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Filtrer les lignes liées à la pipeline
                pipeline_lines = [
                    line for line in lines[-500:]  # 500 dernières lignes
                    if any(keyword in line for keyword in [
                        'pipeline', 'Pipeline', 'Garmin', 'garmin', 
                        'Activité', 'activité', 'stockée', 'doublons', 
                        'synchronisation', 'connect_garmin'
                    ])
                ]
                logs_found.extend(pipeline_lines[-100:])  # 100 lignes max
        
        # 2. Essayer aussi le fichier pipeline_run.log
        pipeline_log_file = project_root / "E1_gestion_donnees/data/logs/pipeline_run.log"
        if pipeline_log_file.exists():
            with open(pipeline_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                logs_found.extend(lines[-50:])  # 50 dernières lignes
        
        if logs_found:
            log_content = ''.join(logs_found)
        else:
            log_content = "Aucun log de pipeline trouvé.\n\nVérifiez que :\n- Vous avez lancé une synchronisation\n- Les logs sont activés\n- Les permissions d'écriture sont correctes"
            
    except Exception as e:
        log_content = f"Erreur lors de la lecture des logs : {str(e)}\n\nFichiers recherchés :\n- {django_log_file if 'django_log_file' in locals() else 'django.log'}\n- {pipeline_log_file if 'pipeline_log_file' in locals() else 'pipeline_run.log'}"
    
    return JsonResponse({
        'logs': log_content,
        'timestamp': timezone.now().isoformat(),
        'files_checked': [
            str(django_log_file) if 'django_log_file' in locals() else 'django.log',
            str(pipeline_log_file) if 'pipeline_log_file' in locals() else 'pipeline_run.log'
        ]
    })


@login_required
def pipeline_status(request):
    """Retourne le statut actuel de la pipeline"""
    
    # Pour simplifier, on considère que la pipeline n'est jamais en cours
    # En production, on pourrait utiliser Celery ou un système de tâches
    
    from activities.models import Activity
    
    user = request.user
    last_activity = Activity.objects.filter(user=user).order_by('-synced_at').first()
    
    return JsonResponse({
        'status': 'ready',  # ready, running, error
        'last_sync': last_activity.synced_at.isoformat() if last_activity else None,
        'total_activities': Activity.objects.filter(user=user).count(),
        'timestamp': timezone.now().isoformat()
    })