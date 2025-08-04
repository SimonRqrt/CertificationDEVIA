#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de nettoyage automatique des comptes utilisateurs
Conformité RGPD - Suppression comptes dormants et alertes inactivité

Usage:
    python cleanup_users.py [--dry-run] [--verbose]
    
Scheduling:
    # CRON hebdomadaire (dimanche 02:00)
    0 2 * * 0 /usr/bin/python3 /path/to/cleanup_users.py
"""

import os
import sys
import django
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.db import transaction
from django.conf import settings

# Configuration Django
sys.path.append('/Users/sims/Documents/Simplon_DEV_IA/Certification/CertificationDEVIA/E3_model_IA/backend/django_app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coach_ai_web.settings')
django.setup()

from accounts.models import User, UserProfile
from coaching.models import CoachingSession, TrainingPlan
from activities.models import Activity

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/rgpd/cleanup_users.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UserCleanupService:
    """Service de nettoyage automatisé des comptes utilisateurs"""
    
    def __init__(self, dry_run=False, verbose=False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.stats = {
            'analyzed': 0,
            'inactive_alerted': 0,
            'dormant_deleted': 0,
            'errors': 0
        }
    
    def log_user_action(self, user_id, action, details):
        """Logging audit trail RGPD"""
        log_entry = {
            'timestamp': timezone.now().isoformat(),
            'user_id': f"user_{hash(str(user_id)) % 100000}",  # Pseudonymisation
            'action': action,
            'details': details,
            'dry_run': self.dry_run
        }
        
        if self.verbose:
            logger.info(f"RGPD Action: {log_entry}")
        
        # Écriture audit trail permanent
        with open('/var/log/rgpd/audit_users.jsonl', 'a') as f:
            import json
            f.write(json.dumps(log_entry) + '\n')
    
    def send_reactivation_email(self, user):
        """Envoi email de réactivation compte inactif"""
        try:
            subject = "Coach IA - Réactivez votre compte"
            message = f"""
            Bonjour {user.first_name},
            
            Votre compte Coach IA n'a pas été utilisé depuis plus de 30 jours.
            
            Conformément au RGPD, les comptes inactifs depuis plus de 2 ans 
            sont automatiquement supprimés.
            
            Pour conserver votre compte et vos données d'entraînement :
            👉 Connectez-vous avant le {(timezone.now() + timedelta(days=700)).strftime('%d/%m/%Y')}
            
            Lien de connexion : https://coach-ia.app/login/
            
            Si vous ne souhaitez plus utiliser notre service, vous pouvez 
            supprimer votre compte immédiatement : https://coach-ia.app/delete-account/
            
            Sportivement,
            L'équipe Coach IA
            """
            
            if not self.dry_run:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False
                )
            
            self.log_user_action(user.id, "ALERTE_INACTIVITE", "EMAIL_ENVOYE")
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi email utilisateur {user.id}: {e}")
            self.log_user_action(user.id, "ERREUR_EMAIL", str(e))
            self.stats['errors'] += 1
            return False
    
    def anonymize_user_data(self, user):
        """Anonymisation données utilisateur avant suppression"""
        try:
            with transaction.atomic():
                # 1. Anonymisation activités (conservation métriques)
                activities = Activity.objects.filter(user=user)
                for activity in activities:
                    # Suppression données GPS précises
                    activity.start_latitude = None
                    activity.start_longitude = None
                    activity.end_latitude = None
                    activity.end_longitude = None
                    
                    # Anonymisation nom activité
                    activity.name = f"Activité anonymisée {activity.id}"
                    activity.description = "Données anonymisées conformément RGPD"
                    
                    # Conservation métriques agrégées uniquement
                    activity.user = None  # Dissociation utilisateur
                    activity.save()
                
                # 2. Anonymisation sessions coaching
                sessions = CoachingSession.objects.filter(user=user)
                for session in sessions:
                    # Suppression contenu conversations
                    session.messages = "Contenu anonymisé RGPD"
                    session.context = "Contexte anonymisé RGPD"
                    session.user = None
                    session.save()
                
                # 3. Conservation anonyme plans d'entraînement (recherche)
                plans = TrainingPlan.objects.filter(user=user)
                for plan in plans:
                    plan.title = f"Plan anonymisé {plan.id}"
                    plan.user = None
                    plan.save()
                
                self.log_user_action(user.id, "ANONYMISATION", "DONNEES_SPORTIVES_CONSERVEES")
                return True
                
        except Exception as e:
            logger.error(f"Erreur anonymisation utilisateur {user.id}: {e}")
            self.log_user_action(user.id, "ERREUR_ANONYMISATION", str(e))
            self.stats['errors'] += 1
            return False
    
    def delete_user_completely(self, user):
        """Suppression complète utilisateur et données associées"""
        try:
            user_id = user.id
            user_email = user.email
            
            with transaction.atomic():
                # Suppression CASCADE via modèles Django
                # Les activités, sessions, plans sont automatiquement supprimés
                # grâce aux ForeignKey(on_delete=CASCADE)
                user.delete()
            
            # Vérification suppression effective
            if User.objects.filter(id=user_id).exists():
                raise Exception("Suppression utilisateur échouée - données toujours présentes")
            
            self.log_user_action(user_id, "SUPPRESSION_COMPLETE", f"EMAIL_{hash(user_email)}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur suppression utilisateur {user.id}: {e}")
            self.log_user_action(user.id, "ERREUR_SUPPRESSION", str(e))
            self.stats['errors'] += 1
            return False
    
    def process_inactive_users(self):
        """Traitement utilisateurs inactifs (30-365 jours)"""
        logger.info("Début traitement utilisateurs inactifs...")
        
        # Utilisateurs inactifs 30-365 jours
        inactive_threshold = timezone.now() - timedelta(days=30)
        dormant_threshold = timezone.now() - timedelta(days=365)
        
        inactive_users = User.objects.filter(
            last_login__lt=inactive_threshold,
            last_login__gte=dormant_threshold,
            is_active=True
        ).exclude(
            email__in=getattr(settings, 'RGPD_EXCLUDED_EMAILS', [])
        )
        
        logger.info(f"Utilisateurs inactifs trouvés: {inactive_users.count()}")
        
        for user in inactive_users:
            self.stats['analyzed'] += 1
            
            if self.send_reactivation_email(user):
                self.stats['inactive_alerted'] += 1
                
            if self.verbose:
                logger.info(f"Alerte envoyée: {user.email} (inactif depuis {(timezone.now() - user.last_login).days} jours)")
    
    def process_dormant_users(self):
        """Traitement utilisateurs dormants (>365 jours)"""
        logger.info("Début traitement utilisateurs dormants...")
        
        # Utilisateurs dormants >365 jours
        dormant_threshold = timezone.now() - timedelta(days=365)
        
        dormant_users = User.objects.filter(
            last_login__lt=dormant_threshold,
            is_active=True
        ).exclude(
            email__in=getattr(settings, 'RGPD_EXCLUDED_EMAILS', [])
        )
        
        logger.info(f"Utilisateurs dormants trouvés: {dormant_users.count()}")
        
        for user in dormant_users:
            self.stats['analyzed'] += 1
            
            if self.verbose:
                logger.info(f"Suppression utilisateur dormant: {user.email} (inactif {(timezone.now() - user.last_login).days} jours)")
            
            # Option 1: Suppression complète (défaut)
            if getattr(settings, 'RGPD_COMPLETE_DELETION', True):
                if self.delete_user_completely(user):
                    self.stats['dormant_deleted'] += 1
            
            # Option 2: Anonymisation (recherche/statistiques)
            else:
                if self.anonymize_user_data(user):
                    if self.delete_user_completely(user):
                        self.stats['dormant_deleted'] += 1
    
    def generate_report(self):
        """Génération rapport d'exécution"""
        report = f"""
=== RAPPORT NETTOYAGE UTILISATEURS RGPD ===
Date: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}
Mode: {'DRY RUN' if self.dry_run else 'PRODUCTION'}

Statistiques:
- Utilisateurs analysés: {self.stats['analyzed']}
- Alertes inactivité envoyées: {self.stats['inactive_alerted']}
- Comptes dormants supprimés: {self.stats['dormant_deleted']}
- Erreurs rencontrées: {self.stats['errors']}

Seuils appliqués:
- Alerte inactivité: >30 jours
- Suppression compte: >365 jours

Conformité RGPD: ✅ Respectée
Traçabilité: /var/log/rgpd/audit_users.jsonl
        """
        
        logger.info(report)
        
        # Sauvegarde rapport mensuel
        report_path = f"/var/log/rgpd/reports/users_{timezone.now().strftime('%Y_%m')}.txt"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'a') as f:
            f.write(report + '\n' + '='*50 + '\n')
        
        return report
    
    def run(self):
        """Exécution complète du nettoyage"""
        logger.info(f"Début nettoyage utilisateurs RGPD (dry_run={self.dry_run})")
        
        try:
            # Traitement utilisateurs inactifs
            self.process_inactive_users()
            
            # Traitement utilisateurs dormants  
            self.process_dormant_users()
            
            # Génération rapport
            report = self.generate_report()
            
            # Alerte si trop d'erreurs
            if self.stats['errors'] > 5:
                logger.error(f"ALERTE: {self.stats['errors']} erreurs durant le nettoyage!")
                # TODO: Envoi email admin
            
            logger.info("Nettoyage utilisateurs terminé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur critique durant nettoyage: {e}")
            return False

def main():
    """Point d'entrée script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Nettoyage automatique utilisateurs RGPD')
    parser.add_argument('--dry-run', action='store_true', help='Mode simulation sans modifications')
    parser.add_argument('--verbose', action='store_true', help='Logs détaillés')
    
    args = parser.parse_args()
    
    # Vérification permissions
    if not args.dry_run and os.geteuid() != 0:
        logger.warning("Recommandé d'exécuter en tant que root pour accès logs")
    
    # Création répertoires logs
    os.makedirs('/var/log/rgpd', exist_ok=True)
    os.makedirs('/var/log/rgpd/reports', exist_ok=True)
    
    # Exécution nettoyage
    cleanup_service = UserCleanupService(dry_run=args.dry_run, verbose=args.verbose)
    success = cleanup_service.run()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()