# 🔐 RGPD Compliance - Coach IA

> **Conformité** : RGPD UE 2016/679  
> **Application** : Coach IA Sportif (CertificationDEVIA)  
> **Automatisation** : Scripts Python + CRON + monitoring  
> **Statut** : ✅ Certification ready

---

## 📋 **Vue d'ensemble**

Cette implémentation RGPD garantit la conformité légale pour le traitement des données personnelles dans l'application de coaching sportif IA.

### Livrables certification
1. **Registre traitements** : `registre_traitements_donnees.md`
2. **Procédures tri** : `procedures_tri_donnees.md` 
3. **Scripts automatisés** : `scripts/cleanup_*.py`
4. **Configuration CRON** : `scripts/setup_cron.sh`

---

## 🎯 **Fonctionnalités RGPD**

### Traitements couverts
- **Comptes utilisateurs** : Authentification, profils sportifs
- **Données Garmin** : Activités, FC, GPS, métriques performance
- **Sessions IA** : Conversations coaching, recommandations
- **Logs techniques** : Monitoring, sécurité, debugging

### Durées de conservation
- **Compte actif** : Utilisation + 3 ans
- **Compte inactif** : Suppression après 2 ans  
- **Données GPS** : Anonymisation après 2 ans
- **Sessions IA** : Conservation 1 an, anonymisation

### Droits utilisateurs implémentés
- ✅ **Accès** : Export JSON complet
- ✅ **Rectification** : Interface profil utilisateur
- ✅ **Suppression** : Effacement <48h
- ✅ **Portabilité** : Format machine-readable
- ✅ **Opposition** : Arrêt coaching IA

---

## 🤖 **Automatisation**

### Scripts de nettoyage automatisé

#### 1. Nettoyage utilisateurs (`cleanup_users.py`)
- **Fréquence** : Hebdomadaire (dimanche 02:00)
- **Fonction** : Alerte inactivité + suppression comptes dormants
- **Seuils** : >30j alerte, >365j suppression

#### 2. Nettoyage activités (`cleanup_activities.py`)  
- **Fréquence** : Mensuel (1er du mois 01:00)
- **Fonction** : Anonymisation GPS + suppression données anciennes
- **Seuils** : >2 ans anonymisation, >5 ans suppression

#### 3. Monitoring (`monitor_rgpd.py`)
- **Fréquence** : Quotidien (08:00)
- **Fonction** : Vérification exécution + alertes
- **Alertes** : Email admin si échec >48h

### Configuration automatique
```bash
# Installation complète CRON + logs
sudo bash scripts/setup_cron.sh

# Test scripts sans modification
python3 scripts/cleanup_users.py --dry-run --verbose
python3 scripts/cleanup_activities.py --dry-run --verbose
```

---

## 📊 **Monitoring et audit**

### Logs de conformité
- **Audit trail** : `/var/log/rgpd/audit_*.jsonl`
- **Rapports** : `/var/log/rgpd/reports/YYYY_MM.txt`
- **Monitoring** : `/var/log/rgpd/monitoring.log`

### Métriques suivies
- Volume suppressions quotidiennes
- Délais traitement demandes RGPD
- Taux erreurs scripts automatisés
- Respect durées conservation

### Dashboard Grafana (optionnel)
```python
# Métriques Prometheus exportées
rgpd_deletions_total{data_type="users"}
rgpd_deletions_total{data_type="activities"} 
rgpd_processing_time_seconds
rgpd_errors_total
```

---

## 🔒 **Sécurité et conformité**

### Mesures techniques
- **Chiffrement** : AES-256 repos, TLS 1.3 transit
- **Pseudonymisation** : Hash irréversibles identifiants
- **Suppression sécurisée** : 3 passes, vérification
- **Backup cleanup** : Scripts automated

### Mesures organisationnelles
- **Formation équipe** : Sensibilisation RGPD
- **Procédures incident** : Notification <72h
- **Audits** : Contrôle trimestriel externe
- **DPO** : Point de contact désigné

### Sous-traitants conformes
- **Supabase** : DPA signé, serveurs EU
- **OpenAI** : Pseudonymisation, clauses contractuelles
- **Monitoring** : Transferts internationaux sécurisés

---

## 📞 **Contacts RGPD**

### Responsable traitement
- **Email** : dev.ia.certification@simplon.co
- **Délai réponse** : 5 jours ouvrés maximum

### DPO (si applicable)
- **Email** : dpo@simplon.co  
- **Mission** : Conseil, contrôle, contact CNIL

### Support technique
- **Urgences** : security@projet-coach-ia.fr
- **Disponibilité** : 24/7 incidents graves

---

## 🚀 **Déploiement production**

### Installation initiale
```bash
# 1. Copier scripts sur serveur
scp -r rgpd/ user@server:/opt/coach-ia/

# 2. Configuration CRON automatique
sudo bash /opt/coach-ia/rgpd/scripts/setup_cron.sh

# 3. Test premier passage
sudo -u www-data python3 cleanup_users.py --dry-run
sudo -u www-data python3 cleanup_activities.py --dry-run

# 4. Vérification CRON installé
sudo crontab -u www-data -l
```

### Vérifications post-installation
- [ ] Scripts s'exécutent sans erreur
- [ ] Logs créés dans `/var/log/rgpd/`
- [ ] Permissions correctes (www-data:www-data)
- [ ] Rotation logs configurée
- [ ] Monitoring fonctionnel

---

## 📚 **Documentation légale**

### Références conformité
- **RGPD** : Articles 5.1.e, 17, 25, 32
- **CNIL** : Recommandations IA et données de santé
- **ISO 27001** : Sécurité information (visé 2026)

### Registres obligatoires
- ✅ Registre des traitements (Art. 30)
- ✅ Analyse d'impact (Art. 35) - si applicable
- ✅ Procédures violation données (Art. 33-34)
- ✅ Documentation mesures techniques (Art. 32)

### Audit et certification
- **Auto-évaluation** : Trimestrielle
- **Audit externe** : Annuel (cabinet spécialisé)
- **Certification** : ISO 27001 planifiée Q2 2026

---

## 🔄 **Maintenance**

### Révisions planifiées
- **Mensuelle** : Vérification métriques, erreurs
- **Trimestrielle** : Mise à jour procédures
- **Annuelle** : Audit complet, évolution réglementaire

### Évolutions prévues
- **Q3 2025** : ML détection anomalies suppressions
- **Q4 2025** : Blockchain audit trail immutable
- **Q1 2026** : API self-service utilisateurs
- **Q2 2026** : Certification ISO 27001

### Support communauté
- **Issues** : GitHub repository (si open-source)
- **Documentation** : Wiki mise à jour continue
- **Formation** : Webinaires RGPD pour développeurs

---

> **Statut certification** : ✅ E1 RGPD - 100% COMPLET  
> **Dernière révision** : 02/08/2025  
> **Prochaine révision** : 02/11/2025 (trimestrielle)  
> **Responsable** : Développeur IA Certification Simplon