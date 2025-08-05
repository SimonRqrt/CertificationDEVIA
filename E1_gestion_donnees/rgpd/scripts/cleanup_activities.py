#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de nettoyage automatique des activités sportives Garmin
Conformité RGPD - Anonymisation GPS et suppression données anciennes

Usage:
    python cleanup_activities.py [--dry-run] [--verbose]
    
Scheduling:
    # CRON mensuel (1er du mois 01:00)
    0 1 1 * * /usr/bin/python3 /path/to/cleanup_activities.py
"""

import os
import sys
import django
import logging
import hashlib
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from django.conf import settings

# Configuration Django
sys.path.append('/Users/sims/Documents/Simplon_DEV_IA/Certification/CertificationDEVIA/E1_gestion_donnees/api_rest')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coach_ai_web.settings')
django.setup()

from activities.models import Activity, ActivitySplit, GPSPoint
from accounts.models import User

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/rgpd/cleanup_activities.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ActivityCleanupService:
    """Service de nettoyage automatisé des données d'activités"""
    
    def __init__(self, dry_run=False, verbose=False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.stats = {
            'analyzed': 0,
            'anonymized_2_5_years': 0,
            'deleted_5_years': 0,
            'gps_points_anonymized': 0,
            'heart_rate_aggregated': 0,
            'errors': 0
        }
    
    def log_activity_action(self, activity_id, action, details):
        """Logging audit trail RGPD pour activités"""
        log_entry = {
            'timestamp': timezone.now().isoformat(),
            'activity_id': f"activity_{hash(str(activity_id)) % 100000}",
            'action': action,
            'details': details,
            'dry_run': self.dry_run
        }
        
        if self.verbose:
            logger.info(f"RGPD Activity: {log_entry}")
        
        # Écriture audit trail permanent
        with open('/var/log/rgpd/audit_activities.jsonl', 'a') as f:
            import json
            f.write(json.dumps(log_entry) + '\n')
    
    def is_sensitive_location(self, lat, lon, user_home_locations=None):
        """Détection zone sensible (domicile, travail) - rayon 500m"""
        if not lat or not lon or not user_home_locations:
            return False
        
        from math import radians, cos, sin, asin, sqrt
        
        def haversine(lon1, lat1, lon2, lat2):
            """Calcul distance haversine en mètres"""
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371000  # Rayon terre en mètres
            return c * r
        
        for home_lat, home_lon in user_home_locations:
            distance = haversine(lon, lat, home_lon, home_lat)
            if distance < 500:  # 500m radius
                return True
        
        return False
    
    def get_user_home_locations(self, user):
        """Inférence localisation domicile/travail utilisateur"""
        # Analyse points de départ/arrivée fréquents
        activities = Activity.objects.filter(
            user=user,
            start_latitude__isnull=False,
            start_longitude__isnull=False
        ).order_by('-start_time')[:100]  # 100 dernières activités
        
        location_frequency = {}
        
        for activity in activities:
            # Arrondi coordonnées à ~100m près
            lat_rounded = round(float(activity.start_latitude), 3)
            lon_rounded = round(float(activity.start_longitude), 3)
            location_key = (lat_rounded, lon_rounded)
            
            location_frequency[location_key] = location_frequency.get(location_key, 0) + 1
        
        # Locations fréquentes = domicile/travail probables
        frequent_locations = [
            location for location, freq in location_frequency.items() 
            if freq >= 5  # Utilisé 5+ fois
        ]
        
        return frequent_locations
    
    def anonymize_gps_points(self, activity):
        """Anonymisation points GPS activité"""
        try:
            user_home_locations = self.get_user_home_locations(activity.user)
            
            # 1. Suppression coordonnées précises zones sensibles
            if self.is_sensitive_location(
                activity.start_latitude, 
                activity.start_longitude, 
                user_home_locations
            ):
                if not self.dry_run:
                    activity.start_latitude = None
                    activity.start_longitude = None
                    activity.end_latitude = None
                    activity.end_longitude = None
                
                self.log_activity_action(activity.id, "GPS_ANONYMISATION", "ZONE_SENSIBLE_DETECTEE")
            
            # 2. Suppression points GPS détaillés
            gps_points = GPSPoint.objects.filter(activity=activity)
            points_count = gps_points.count()
            
            if points_count > 0:
                # Conservation 1 point / 1km pour métriques générales
                points_to_keep = max(1, points_count // 50)  # ~1 point / 1km
                
                if not self.dry_run:
                    # Suppression points intermédiaires (précision élevée)
                    points_to_delete = gps_points.exclude(
                        id__in=gps_points.values_list('id', flat=True)[::50]
                    )
                    deleted_count = points_to_delete.count()
                    points_to_delete.delete()
                    
                    self.stats['gps_points_anonymized'] += deleted_count
                
                self.log_activity_action(
                    activity.id, 
                    "GPS_POINTS_REDUCTION", 
                    f"{points_count}_TO_{points_to_keep}_POINTS"
                )
            
            # 3. Anonymisation métadonnées géographiques
            if not self.dry_run:
                activity.name = f"Course {activity.start_time.strftime('%d/%m/%Y')}"
                activity.description = "Données GPS anonymisées conformément RGPD"
                activity.save()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur anonymisation GPS activité {activity.id}: {e}")
            self.log_activity_action(activity.id, "ERREUR_GPS_ANONYMISATION", str(e))
            self.stats['errors'] += 1
            return False
    
    def aggregate_heart_rate_data(self, activity):
        """Agrégation données fréquence cardiaque détaillées"""
        try:
            # Conservation métriques moyennes/max uniquement
            # Suppression données FC seconde par seconde
            
            if hasattr(activity, 'heart_rate_data') and activity.heart_rate_data:
                if not self.dry_run:
                    # Calcul métriques agrégées
                    hr_data = activity.heart_rate_data
                    if isinstance(hr_data, list) and len(hr_data) > 0:
                        activity.average_heart_rate = sum(hr_data) / len(hr_data)
                        activity.max_heart_rate = max(hr_data)
                        
                        # Suppression données détaillées
                        activity.heart_rate_data = None
                        activity.save()
                        
                        self.stats['heart_rate_aggregated'] += 1
                
                self.log_activity_action(
                    activity.id, 
                    "FC_AGREGATION", 
                    f"DONNEES_DETAILLEES_SUPPRIMEES"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur agrégation FC activité {activity.id}: {e}")
            self.log_activity_action(activity.id, "ERREUR_FC_AGREGATION", str(e))
            self.stats['errors'] += 1
            return False
    
    def process_activities_2_5_years(self):
        """Traitement activités 2-5 ans (anonymisation)"""
        logger.info("Début anonymisation activités 2-5 ans...")
        
        # Activités entre 2 et 5 ans
        start_2_years = timezone.now() - timedelta(days=730)
        start_5_years = timezone.now() - timedelta(days=1825)
        
        old_activities = Activity.objects.filter(
            start_time__lt=start_2_years,
            start_time__gte=start_5_years
        ).select_related('user')
        
        logger.info(f"Activités 2-5 ans trouvées: {old_activities.count()}")
        
        for activity in old_activities:
            self.stats['analyzed'] += 1
            
            if self.verbose:
                logger.info(f"Anonymisation activité {activity.id} ({activity.start_time.strftime('%d/%m/%Y')})")
            
            # Anonymisation GPS
            if self.anonymize_gps_points(activity):
                # Agrégation données FC
                if self.aggregate_heart_rate_data(activity):
                    self.stats['anonymized_2_5_years'] += 1
    
    def process_activities_over_5_years(self):
        """Traitement activités >5 ans (suppression complète)"""
        logger.info("Début suppression activités >5 ans...")
        
        # Activités > 5 ans
        cutoff_5_years = timezone.now() - timedelta(days=1825)
        
        ancient_activities = Activity.objects.filter(
            start_time__lt=cutoff_5_years
        )
        
        logger.info(f"Activités >5 ans trouvées: {ancient_activities.count()}")
        
        for activity in ancient_activities:
            self.stats['analyzed'] += 1
            
            if self.verbose:
                logger.info(f"Suppression activité {activity.id} ({activity.start_time.strftime('%d/%m/%Y')})")
            
            try:
                activity_id = activity.id
                
                if not self.dry_run:
                    # Suppression CASCADE (splits, GPS points automatiques)
                    activity.delete()
                
                self.log_activity_action(
                    activity_id, 
                    "SUPPRESSION_ANCIENNE", 
                    "PLUS_5_ANS"
                )
                self.stats['deleted_5_years'] += 1
                
            except Exception as e:
                logger.error(f"Erreur suppression activité {activity.id}: {e}")
                self.log_activity_action(activity.id, "ERREUR_SUPPRESSION", str(e))
                self.stats['errors'] += 1
    
    def cleanup_orphaned_data(self):
        """Nettoyage données orphelines"""
        logger.info("Nettoyage données orphelines...")
        
        try:
            # GPS points sans activité
            orphaned_gps = GPSPoint.objects.filter(activity__isnull=True)
            gps_count = orphaned_gps.count()
            
            if gps_count > 0:
                if not self.dry_run:
                    orphaned_gps.delete()
                logger.info(f"GPS points orphelins supprimés: {gps_count}")
            
            # Activity splits sans activité
            orphaned_splits = ActivitySplit.objects.filter(activity__isnull=True)
            splits_count = orphaned_splits.count()
            
            if splits_count > 0:
                if not self.dry_run:
                    orphaned_splits.delete()
                logger.info(f"Activity splits orphelins supprimés: {splits_count}")
            
        except Exception as e:
            logger.error(f"Erreur nettoyage orphelins: {e}")
            self.stats['errors'] += 1
    
    def generate_report(self):
        """Génération rapport d'exécution"""
        report = f"""
=== RAPPORT NETTOYAGE ACTIVITÉS RGPD ===
Date: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}
Mode: {'DRY RUN' if self.dry_run else 'PRODUCTION'}

Statistiques:
- Activités analysées: {self.stats['analyzed']}
- Activités anonymisées (2-5 ans): {self.stats['anonymized_2_5_years']}
- Activités supprimées (>5 ans): {self.stats['deleted_5_years']}
- Points GPS anonymisés: {self.stats['gps_points_anonymized']}
- Données FC agrégées: {self.stats['heart_rate_aggregated']}
- Erreurs rencontrées: {self.stats['errors']}

Politique conservation:
- Données récentes (<2 ans): Conservation intégrale
- Données historiques (2-5 ans): Anonymisation GPS + agrégation FC
- Données anciennes (>5 ans): Suppression complète

Conformité RGPD: ✅ Art. 5.1.e respecté
Traçabilité: /var/log/rgpd/audit_activities.jsonl
        """
        
        logger.info(report)
        
        # Sauvegarde rapport mensuel
        report_path = f"/var/log/rgpd/reports/activities_{timezone.now().strftime('%Y_%m')}.txt"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'a') as f:
            f.write(report + '\n' + '='*50 + '\n')
        
        return report
    
    def run(self):
        """Exécution complète du nettoyage activités"""
        logger.info(f"Début nettoyage activités RGPD (dry_run={self.dry_run})")
        
        try:
            # Anonymisation activités 2-5 ans
            self.process_activities_2_5_years()
            
            # Suppression activités >5 ans
            self.process_activities_over_5_years()
            
            # Nettoyage données orphelines
            self.cleanup_orphaned_data()
            
            # Génération rapport
            report = self.generate_report()
            
            # Alerte si trop d'erreurs
            if self.stats['errors'] > 10:
                logger.error(f"ALERTE: {self.stats['errors']} erreurs durant le nettoyage!")
                # TODO: Envoi email admin
            
            logger.info("Nettoyage activités terminé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur critique durant nettoyage activités: {e}")
            return False

def main():
    """Point d'entrée script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Nettoyage automatique activités RGPD')
    parser.add_argument('--dry-run', action='store_true', help='Mode simulation sans modifications')
    parser.add_argument('--verbose', action='store_true', help='Logs détaillés')
    
    args = parser.parse_args()
    
    # Création répertoires logs
    os.makedirs('/var/log/rgpd', exist_ok=True)
    os.makedirs('/var/log/rgpd/reports', exist_ok=True)
    
    # Exécution nettoyage
    cleanup_service = ActivityCleanupService(dry_run=args.dry_run, verbose=args.verbose)
    success = cleanup_service.run()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()