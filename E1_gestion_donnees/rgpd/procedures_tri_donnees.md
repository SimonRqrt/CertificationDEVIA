# 🗂️ Procédures de Tri des Données Personnelles

> **Application** : Coach IA Sportif (CertificationDEVIA)  
> **Conformité** : RGPD Art. 5.1.e (limitation durée) + Art. 17 (droit effacement)  
> **Automatisation** : Scripts Python + CRON + monitoring  
> **Révision** : Mensuelle - Prochaine: 02/09/2025

---

## 🎯 **Objectifs et principes**

### Finalités du tri
1. **Conformité RGPD** : Respect durées conservation légales
2. **Minimisation données** : Conservation uniquement nécessaire
3. **Performance système** : Optimisation stockage et requêtes
4. **Sécurité** : Réduction surface d'attaque sur données

### Principes directeurs
- **Automatisation maximale** : Scripts déclenchés, supervision humaine
- **Traçabilité complète** : Logs horodatés, audit trail
- **Récupération impossible** : Suppression définitive sécurisée
- **Continuité service** : Opérations transparentes utilisateurs

---

## 📅 **Calendrier et fréquences de tri**

### Tri quotidien (00:30 UTC)
- **Sessions expirées** : JWT tokens, cache temporaire
- **Logs temporaires** : Debug logs >24h, error logs traités
- **Données analytiques** : Métriques temps réel agrégées

### Tri hebdomadaire (Dimanche 02:00 UTC)
- **Comptes inactifs** : >30 jours sans connexion (alerte)
- **Conversations IA** : Sessions >7 jours sans interactions
- **Caches applicatifs** : Images, fichiers temporaires >7j

### Tri mensuel (1er du mois 01:00 UTC)
- **Données anonymisables** : Activités >2 ans
- **Comptes dormants** : >365 jours inactifs (suppression)
- **Logs archivés** : Rotation vers stockage froid

### Tri semestriel (1er janvier/juillet)
- **Révision durées** : Mise à jour politiques conservation
- **Audit complet** : Vérification procédures, métriques
- **Documentation** : Mise à jour registre traitements

---

## 🔄 **Procédures automatisées par type de données**

### 1. Comptes utilisateurs et authentification

#### Critères de tri
- **Compte actif** : Connexion <365 jours → Conservation
- **Compte inactif** : 365-730 jours → Alerte réactivation
- **Compte dormant** : >730 jours → Suppression automatique
- **Compte supprimé** : Demande utilisateur → Effacement immédiat

#### Script automatisé
```python
# Script: /E1_gestion_donnees/rgpd/scripts/cleanup_users.py
# Fréquence: Hebdomadaire

def cleanup_inactive_users():
    """Tri automatique comptes utilisateurs"""
    
    # Alerte comptes inactifs 30-365j
    inactive_users = User.objects.filter(
        last_login__lt=timezone.now() - timedelta(days=30),
        last_login__gte=timezone.now() - timedelta(days=365)
    )
    
    for user in inactive_users:
        send_reactivation_email(user)
        log_user_action(user.id, "ALERTE_INACTIVITE", "EMAIL_ENVOYE")
    
    # Suppression comptes dormants >730j
    dormant_users = User.objects.filter(
        last_login__lt=timezone.now() - timedelta(days=730)
    )
    
    for user in dormant_users:
        anonymize_user_data(user)
        log_user_action(user.id, "SUPPRESSION_DORMANT", "ANONYMISE")
        user.delete()
```

#### Journalisation
- **Logs conservation** : 3 ans (preuve conformité)
- **Métriques** : Nb suppressions, réactivations, erreurs
- **Alertes** : Email admin si >10 suppressions/jour

### 2. Données d'activités sportives Garmin

#### Critères de tri
- **Données récentes** : <2 ans → Conservation intégrale
- **Données historiques** : 2-5 ans → Anonymisation GPS/identifiants
- **Données anciennes** : >5 ans → Suppression complète
- **Données sensibles** : FC détaillée >1 an → Agrégation

#### Script automatisé
```python
# Script: /E1_gestion_donnees/rgpd/scripts/cleanup_activities.py
# Fréquence: Mensuelle

def cleanup_garmin_activities():
    """Tri et anonymisation activités Garmin"""
    
    # Anonymisation données 2-5 ans
    old_activities = Activity.objects.filter(
        start_time__lt=timezone.now() - timedelta(days=730),
        start_time__gte=timezone.now() - timedelta(days=1825)
    )
    
    for activity in old_activities:
        # Suppression coordonnées GPS précises
        anonymize_gps_points(activity)
        # Conservation métriques agrégées uniquement
        aggregate_heart_rate_data(activity)
        log_activity_action(activity.id, "ANONYMISATION", "GPS_FC_AGREGES")
    
    # Suppression données >5 ans
    ancient_activities = Activity.objects.filter(
        start_time__lt=timezone.now() - timedelta(days=1825)
    )
    
    for activity in ancient_activities:
        log_activity_action(activity.id, "SUPPRESSION_ANCIENNE", "5_ANS_DEPASSES")
        activity.delete()
```

#### Anonymisation GPS
- **Parcours détaillés** : Suppression points <10m précision
- **Zones sensibles** : Effacement domicile/travail (rayon 500m)
- **Métriques conservées** : Distance, durée, dénivelé global
- **Hash irréversible** : Identifiants utilisateur pseudonymisés

### 3. Sessions de coaching IA

#### Critères de tri
- **Sessions actives** : Conversation en cours → Conservation
- **Sessions récentes** : <30 jours → Conservation intégrale
- **Sessions historiques** : 30-365 jours → Anonymisation
- **Sessions anciennes** : >365 jours → Suppression

#### Script automatisé
```python
# Script: /E1_gestion_donnees/rgpd/scripts/cleanup_coaching_sessions.py
# Fréquence: Hebdomadaire

def cleanup_coaching_sessions():
    """Tri sessions coaching IA"""
    
    # Anonymisation sessions 30-365j
    old_sessions = CoachingSession.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=30),
        created_at__gte=timezone.now() - timedelta(days=365)
    )
    
    for session in old_sessions:
        # Suppression identifiants personnels des prompts
        anonymize_user_references(session.messages)
        # Conservation pattern coaching pour amélioration IA
        anonymize_personal_details(session.context)
        log_session_action(session.id, "ANONYMISATION", "DONNEES_PERSONNELLES")
    
    # Suppression sessions >1 an
    ancient_sessions = CoachingSession.objects.filter(
        created_at__lt=timezone.now() - timedelta(days=365)
    )
    
    count = ancient_sessions.count()
    ancient_sessions.delete()
    log_system_action("SUPPRESSION_SESSIONS_ANCIENNES", f"{count}_SESSIONS")
```

### 4. Logs techniques et monitoring

#### Critères de tri
- **Logs applicatifs** : >30 jours → Suppression
- **Logs sécurité** : >90 jours → Archive puis suppression 1 an
- **Métriques performance** : >365 jours → Agrégation mensuelle
- **Logs erreurs** : >180 jours si résolues → Suppression

#### Script automatisé
```python
# Script: /E1_gestion_donnees/rgpd/scripts/cleanup_logs.py
# Fréquence: Quotidienne

def cleanup_system_logs():
    """Nettoyage logs système"""
    
    # Suppression logs applicatifs >30j
    old_app_logs = SystemLog.objects.filter(
        level__in=['DEBUG', 'INFO'],
        timestamp__lt=timezone.now() - timedelta(days=30)
    )
    
    count = old_app_logs.count()
    old_app_logs.delete()
    
    # Archive logs sécurité 90j-1an
    security_logs = SystemLog.objects.filter(
        level__in=['WARNING', 'ERROR'],
        timestamp__lt=timezone.now() - timedelta(days=90),
        timestamp__gte=timezone.now() - timedelta(days=365)
    )
    
    archive_to_cold_storage(security_logs)
    
    # Suppression définitive >1 an
    ancient_logs = SystemLog.objects.filter(
        timestamp__lt=timezone.now() - timedelta(days=365)
    )
    
    ancient_logs.delete()
```

---

## 🔐 **Procédures de suppression sécurisée**

### Suppression base de données PostgreSQL
```sql
-- Suppression avec VACUUM FULL pour libération espace
DELETE FROM activities_activity WHERE user_id = %s;
DELETE FROM auth_user WHERE id = %s;
VACUUM FULL;

-- Vérification suppression effective
SELECT count(*) FROM activities_activity WHERE user_id = %s; -- Doit retourner 0
```

### Suppression fichiers système
```bash
# Suppression sécurisée fichiers (3 passes)
shred -vfz -n 3 /path/to/user/files/*
rm -rf /path/to/user/files/

# Suppression backups chiffrés
find /backups/ -name "*user_$USER_ID*" -exec shred -vfz -n 3 {} \;
```

### Suppression caches et CDN
```python
def secure_delete_user_data(user_id):
    """Suppression multi-couches données utilisateur"""
    
    # 1. Base données
    with transaction.atomic():
        User.objects.filter(id=user_id).delete()
    
    # 2. Cache Redis
    cache.delete_pattern(f"user:{user_id}:*")
    
    # 3. Fichiers stockage
    storage_path = f"/media/users/{user_id}/"
    if os.path.exists(storage_path):
        shutil.rmtree(storage_path)
    
    # 4. Logs applicatifs (anonymisation)
    SystemLog.objects.filter(
        user_id=user_id
    ).update(user_id=None, message=anonymize_message)
    
    # 5. Vérification suppression
    verify_user_data_deleted(user_id)
```

---

## 📊 **Monitoring et métriques**

### Dashboard de suivi (Grafana)
- **Suppressions quotidiennes** : Volume, répartition par type
- **Erreurs tri** : Échecs, retries, alertes
- **Durées conservation** : Respect moyens par catégorie
- **Demandes RGPD** : Délais traitement, taux succès

### Alertes automatiques
```python
# Alertes Prometheus/Grafana
RGPD_CLEANUP_ERRORS = Counter('rgpd_cleanup_errors_total')
RGPD_DELETIONS = Counter('rgpd_deletions_total', ['data_type'])
RGPD_PROCESSING_TIME = Histogram('rgpd_processing_seconds')

def alert_if_cleanup_fails():
    """Alertes en cas d'échec tri"""
    if RGPD_CLEANUP_ERRORS._value.sum() > 5:
        send_alert_email("RGPD: Échecs répétés tri automatique")
    
    if time.time() - last_successful_cleanup > 86400 * 2:  # 2 jours
        send_alert_email("RGPD: Tri automatique non exécuté depuis 48h")
```

### Métriques de conformité
- **Taux automatisation** : 95% suppressions sans intervention
- **Délai moyen** : <24h entre échéance et suppression effective
- **Précision** : 0% suppression données encore nécessaires
- **Audit** : 100% opérations tracées avec horodatage

---

## 🚨 **Procédures d'urgence et récupération**

### Suppression accidentelle
1. **Détection** : Monitoring volume suppressions anormal
2. **Arrêt** : Kill scripts en cours, isolation système
3. **Évaluation** : Audit logs, identification données perdues
4. **Récupération** : Restore depuis backup <24h
5. **Correction** : Patch script, tests, redéploiement

### Demande suppression urgente (RGPD)
```python
def urgent_user_deletion(user_id, request_timestamp):
    """Suppression urgente <48h conformité RGPD"""
    
    # 1. Validation demande
    user = validate_deletion_request(user_id, request_timestamp)
    
    # 2. Suppression immédiate base active
    with transaction.atomic():
        anonymize_user_activities(user_id)
        delete_user_coaching_sessions(user_id)
        user.delete()
    
    # 3. Planification suppression backups
    schedule_backup_cleanup(user_id, delay_hours=24)
    
    # 4. Confirmation utilisateur
    send_deletion_confirmation(user.email)
    
    # 5. Log audit RGPD
    log_rgpd_deletion(user_id, "DEMANDE_URGENTE", request_timestamp)
```

### Violation données détectée
1. **Isolation** : Arrêt scripts, mise hors ligne si nécessaire
2. **Évaluation** : Scope violation, données affectées
3. **Notification** : CNIL dans 72h si risque élevé
4. **Remédiation** : Suppression données compromises
5. **Renforcement** : Mise à jour procédures sécurité

---

## 📋 **Procédures manuelles exceptionnelles**

### Cas complexes nécessitant intervention humaine
- **Données litigieuses** : Demande suppression partielle
- **Compte partagé** : Plusieurs utilisateurs même email
- **Erreur technique** : Échec script, corruption données
- **Demande tribunaux** : Ordonnance conservation

### Workflow validation manuelle
1. **Ticket RGPD** : Création cas dans système
2. **Analyse DPO** : Évaluation légale, technique
3. **Validation** : Approbation procédure exceptionnelle
4. **Exécution** : Script personnalisé, supervision
5. **Documentation** : Justification, traçabilité

### Outils d'administration
```bash
# Script admin suppression sélective
python manage.py rgpd_cleanup --user-id 12345 --dry-run
python manage.py rgpd_cleanup --user-id 12345 --confirm
python manage.py rgpd_verify --user-id 12345

# Audit conformité
python manage.py rgpd_audit --start-date 2025-07-01 --end-date 2025-07-31
```

---

## 📊 **Reporting et documentation**

### Rapport mensuel conformité RGPD
- **Volume données traitées** : Nouveaux, supprimés, anonymisés
- **Durées moyennes conservation** : Par type données
- **Demandes utilisateurs** : Accès, rectification, suppression
- **Incidents** : Violations, échecs, corrections

### Audit trail permanent
```json
{
  "timestamp": "2025-08-02T10:30:00Z",
  "action": "USER_DELETION",
  "user_id": "user_12345_hash",
  "reason": "DORMANT_ACCOUNT_730_DAYS",
  "data_types": ["profile", "activities", "coaching_sessions"],
  "operator": "automated_script",
  "validation": "policy_rgpd_v1.0",
  "verification": "deletion_confirmed"
}
```

### Conservation documentation
- **Scripts exécution** : 3 ans (preuve conformité)
- **Logs suppression** : 5 ans (audit externe)
- **Rapports mensuels** : 7 ans (archives légales)
- **Procédures** : Versioning Git, historique complet

---

## 🔄 **Évolution et amélioration continue**

### Révision trimestrielle
- **Efficacité** : Métriques automatisation, erreurs
- **Conformité** : Évolution réglementation, jurisprudence
- **Technique** : Optimisation scripts, performance
- **Utilisateur** : Feedback, demandes spécifiques

### Indicateurs d'amélioration
- **Réduction délais** : <24h objectif pour 95% cas
- **Augmentation automatisation** : 98% suppressions sans intervention
- **Diminution erreurs** : <1% échecs scripts mensuels
- **Satisfaction audit** : 100% conformité contrôles externes

### Roadmap évolution
- **Q3 2025** : Machine Learning détection anomalies
- **Q4 2025** : Intégration blockchain audit trail
- **Q1 2026** : API self-service utilisateurs
- **Q2 2026** : Certification ISO 27001 complète

---

> **Validation** : Procédures validées DPO et auditées conformité RGPD  
> **Mise à jour** : 02/08/2025  
> **Prochaine révision** : 02/09/2025 (mensuelle)  
> **Responsable** : Administrateur RGPD - rgpd@projet-coach-ia.fr