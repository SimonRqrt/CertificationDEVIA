#!/usr/bin/env python3
"""
Django Management Command - Pipeline Garmin unifié
Remplace E1_gestion_donnees/scripts/run_pipeline.py
Utilise Django ORM au lieu de SQLAlchemy
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

# Imports pour les données Garmin
# Chemin depuis django_app vers la racine du projet
project_root = Path('/Users/sims/Documents/Simplon_DEV_IA/Certification/CertificationDEVIA')
sys.path.insert(0, str(project_root))

try:
    from E1_gestion_donnees.data_manager import fetch_and_process_garmin_data, compute_performance_metrics
    from src.config import GARMIN_EMAIL, GARMIN_PASSWORD
    GARMIN_IMPORTS_OK = True
except ImportError as e:
    GARMIN_IMPORTS_OK = False
    IMPORT_ERROR = str(e)

# Imports Django
from accounts.models import User
from activities.models import Activity, ActivitySplit


class Command(BaseCommand):
    help = 'Exécute le pipeline de données Garmin avec Django ORM'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id', 
            type=int, 
            default=1,
            help='ID de l\'utilisateur pour lequel exécuter le pipeline'
        )

    def handle(self, *args, **options):
        user_id = options['user_id']
        
        # Configuration logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
        log = logging.getLogger(__name__)

        log.info(f"🚀 Démarrage du pipeline Django pour l'utilisateur ID: {user_id}")

        # Vérifier les imports Garmin
        if not GARMIN_IMPORTS_OK:
            log.error(f"❌ Impossible d'importer les modules Garmin: {IMPORT_ERROR}")
            log.info("💡 Pour les tests, vous pouvez créer des activités manuellement")
            return

        try:
            # Vérifier que l'utilisateur existe
            try:
                django_user = User.objects.get(id=user_id)
                log.info(f"✅ Utilisateur trouvé: {django_user.email}")
            except User.DoesNotExist:
                log.error(f"❌ Utilisateur ID {user_id} non trouvé")
                return

            # --- ÉTAPE 1: EXTRACTION DES DONNÉES GARMIN ---
            log.info("📡 Étape 1/4: Récupération des données Garmin...")
            processed_result = fetch_and_process_garmin_data(user_id=user_id, save_raw=True)
            
            if processed_result is None:
                log.error("❌ Aucune donnée récupérée depuis Garmin")
                return

            activities_df, processed_activities = processed_result
            log.info(f"✅ DataFrame créé: {len(activities_df)} activités")

            # --- ÉTAPE 2: STOCKAGE AVEC DJANGO ORM ---
            log.info("💾 Étape 2/4: Stockage des activités avec Django ORM...")
            
            stored_count = 0
            updated_count = 0

            for activity_data in processed_activities:
                try:
                    with transaction.atomic():
                        # Convertir les données pour Django
                        garmin_id = activity_data.get('activity_id')
                        
                        # Parse de la date
                        start_time = activity_data.get('start_time')
                        if isinstance(start_time, str):
                            try:
                                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                            except:
                                start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
                        
                        if start_time and not timezone.is_aware(start_time):
                            start_time = timezone.make_aware(start_time)

                        # Créer ou mettre à jour l'activité
                        activity, created = Activity.objects.update_or_create(
                            garmin_id=garmin_id,
                            defaults={
                                'user': django_user,
                                'activity_name': activity_data.get('activity_name', f'Activité {garmin_id}'),
                                'activity_type': activity_data.get('activity_type', 'running'),
                                'start_time': start_time,
                                'duration_seconds': int(activity_data.get('duration_seconds', 0)),
                                'distance_meters': float(activity_data.get('distance_meters', 0)),
                                'average_speed': activity_data.get('average_speed'),
                                'max_speed': activity_data.get('max_speed'),
                                'calories': int(activity_data.get('calories')) if activity_data.get('calories') else None,
                                'average_hr': int(activity_data.get('average_hr')) if activity_data.get('average_hr') else None,
                                'max_hr': int(activity_data.get('max_hr')) if activity_data.get('max_hr') else None,
                                'elevation_gain': activity_data.get('elevation_gain'),
                                'elevation_loss': activity_data.get('elevation_loss'),
                                'start_latitude': activity_data.get('start_latitude'),
                                'start_longitude': activity_data.get('start_longitude'),
                                'device_name': activity_data.get('device_name') or 'Inconnu',
                                'steps': int(activity_data.get('steps')) if activity_data.get('steps') else None,
                                'average_cadence': int(activity_data.get('average_running_cadence')) if activity_data.get('average_running_cadence') else None,
                                'max_cadence': int(activity_data.get('max_running_cadence')) if activity_data.get('max_running_cadence') else None,
                                'stride_length': activity_data.get('stride_length'),
                                'vo2_max': activity_data.get('vo2max_estime'),
                                'training_load': activity_data.get('training_load'),
                                'aerobic_effect': activity_data.get('aerobic_effect'),
                                'anaerobic_effect': activity_data.get('anaerobic_effect'),
                                'fastest_5k': activity_data.get('fastest_split_5000'),
                                'fastest_10k': activity_data.get('fastest_split_10000'),
                                'hr_zone_1_time': int(activity_data.get('hr_zone_1', 0) * 60) if activity_data.get('hr_zone_1') else None,
                                'hr_zone_2_time': int(activity_data.get('hr_zone_2', 0) * 60) if activity_data.get('hr_zone_2') else None,
                                'hr_zone_3_time': int(activity_data.get('hr_zone_3', 0) * 60) if activity_data.get('hr_zone_3') else None,
                                'hr_zone_4_time': int(activity_data.get('hr_zone_4', 0) * 60) if activity_data.get('hr_zone_4') else None,
                                'hr_zone_5_time': int(activity_data.get('hr_zone_5', 0) * 60) if activity_data.get('hr_zone_5') else None,
                                'synced_at': timezone.now()
                            }
                        )

                        if created:
                            stored_count += 1
                        else:
                            updated_count += 1

                except Exception as e:
                    log.error(f"❌ Erreur traitement activité {garmin_id}: {e}")

            log.info(f"✅ Stockage terminé: {stored_count} créées, {updated_count} mises à jour")

            # --- ÉTAPE 3: CALCUL DES MÉTRIQUES ---
            log.info("📊 Étape 3/4: Calcul des métriques de performance...")
            
            try:
                metrics_data = compute_performance_metrics(activities_df=activities_df, user_id=user_id)
                if metrics_data:
                    log.info(f"✅ Métriques calculées: {len(metrics_data)} entrées")
                    # TODO: Stocker les métriques dans UserProfile si nécessaire
                else:
                    log.warning("⚠️ Aucune métrique calculée")
            except Exception as e:
                log.error(f"❌ Erreur calcul métriques: {e}")

            # --- ÉTAPE 4: RÉCAPITULATIF ---
            total_activities = Activity.objects.filter(user=django_user).count()
            latest_activity = Activity.objects.filter(user=django_user).order_by('-start_time').first()
            
            log.info("🎉 Pipeline Django terminé avec succès!")
            log.info(f"📊 Total activités en base: {total_activities}")
            if latest_activity:
                log.info(f"🏃 Dernière activité: {latest_activity.activity_name} ({latest_activity.start_time})")

        except Exception as e:
            log.error(f"💥 Erreur critique dans le pipeline: {e}")
            raise