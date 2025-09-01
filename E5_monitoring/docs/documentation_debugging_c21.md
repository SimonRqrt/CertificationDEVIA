# Documentation Debugging et Résolution d'Incidents - Coach IA (C21)

## Objectif
Cette documentation couvre les procédures de debugging et de résolution d'incidents pour l'application Coach IA, conformément au critère C21 de la certification.

## Architecture de Debugging

### Services de Logging et Tracing
- **Loki** (port 3100) : Centralisation des logs applicatifs
- **Promtail** : Agent de collecte des logs
- **Grafana** : Interface de consultation des logs et traces

### Points de Logging Applicatifs
- **FastAPI** : Logs API, requêtes IA, erreurs agent
- **Django** : Logs interface web, authentification, génération plans
- **Streamlit** : Logs interface utilisateur, interactions
- **PostgreSQL** : Logs requêtes lentes, connexions, erreurs

## Procédures de Debugging par Type d'Incident

### 1. Incidents Agent IA (Niveau CRITICAL)

#### Symptômes
- Temps de réponse IA > 15 secondes
- Échec génération plans d'entraînement
- Erreurs base de connaissances RAG
- Coûts API OpenAI anormalement élevés

#### Étapes de Debugging
```bash
# 1. Vérifier statut services IA
curl "http://localhost:9090/api/v1/query?query=up{job='coach-api-fastapi'}"

# 2. Consulter logs agent IA
docker logs coach-fastapi-container --tail=50

# 3. Vérifier métriques performances
curl "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95, rate(openai_response_time_seconds_bucket[5m]))"

# 4. Tester endpoint agent directement
curl -X POST "http://localhost:8000/v1/coaching/chat-legacy" \
  -H "X-API-Key: coach_ai_secure_key_2025" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test connection", "user_id": 1}'
```

#### Solutions Types
- **Timeout OpenAI** : Augmenter timeout ou retry automatique
- **RAG indisponible** : Redémarrer service FAISS ou recharger embeddings
- **Rate limit** : Implémenter circuit breaker ou réduire fréquence
- **Coûts élevés** : Vérifier loops infinies ou requêtes malformées

### 2. Incidents Base de Données (Niveau CRITICAL)

#### Symptômes
- PostgreSQL inaccessible
- Requêtes lentes > 2 secondes (P95)
- Erreurs connexion Django/FastAPI
- Lock timeout sur tables activités

#### Étapes de Debugging
```bash
# 1. Vérifier connexion PostgreSQL
psql -h localhost -U coach_user -d coach_ia_db -c "\conninfo"

# 2. Identifier requêtes lentes
psql -h localhost -U coach_user -d coach_ia_db -c "
SELECT query, mean_exec_time, calls 
FROM pg_stat_statements 
WHERE mean_exec_time > 1000 
ORDER BY mean_exec_time DESC 
LIMIT 10;"

# 3. Vérifier locks actives
psql -h localhost -U coach_user -d coach_ia_db -c "
SELECT blocked_locks.pid AS blocked_pid,
       blocked_activity.usename AS blocked_user,
       blocking_locks.pid AS blocking_pid,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;"

# 4. Vérifier espace disque et performances
df -h /var/lib/postgresql
iostat -x 1 5
```

#### Solutions Types
- **Connexions épuisées** : Augmenter max_connections ou implémenter pooling
- **Requêtes lentes** : Ajouter index, optimiser requêtes, VACUUM ANALYZE
- **Locks prolongées** : Identifier transactions longues, tuer sessions bloquantes
- **Espace disque** : Nettoyer logs anciens, archiver données historiques

### 3. Incidents Interface Utilisateur (Niveau WARNING)

#### Symptômes
- Streamlit inaccessible (port 8502)
- Django erreurs 500
- Timeout chargement données
- Interface utilisateur non responsive

#### Étapes de Debugging
```bash
# 1. Vérifier statut services web
curl -I "http://localhost:8502/_stcore/health"
curl -I "http://localhost:8002/health"

# 2. Consulter logs interfaces
tail -f E4_app_IA/frontend/streamlit_app/logs/app.log
tail -f E3_model_IA/backend/django_app/logs/django.log

# 3. Tester endpoints critiques
curl "http://localhost:8502/_stcore/metrics"
curl "http://localhost:8002/admin/login/"

# 4. Vérifier ressources système
docker stats coach-streamlit-container
docker stats coach-django-container
```

#### Solutions Types
- **Streamlit planté** : Redémarrer service, vérifier mémoire disponible
- **Django 500** : Vérifier logs erreurs, connexion base données
- **Timeout données** : Optimiser requêtes, mettre en cache
- **Mémoire insuffisante** : Augmenter limites Docker ou optimiser code

### 4. Incidents Monitoring (Niveau WARNING)

#### Symptômes
- Prometheus ne collecte plus de métriques
- Grafana dashboards vides
- Alertes non déclenchées
- Retention logs insuffisante

#### Étapes de Debugging
```bash
# 1. Vérifier stack monitoring
docker-compose -f deployment/docker-compose-monitoring.yml ps

# 2. Tester collecte Prometheus
curl "http://localhost:9090/api/v1/targets"
curl "http://localhost:9090/api/v1/query?query=up"

# 3. Vérifier configuration Grafana
curl -u admin:admin123 "http://localhost:3000/api/datasources"
curl -u admin:admin123 "http://localhost:3000/api/dashboards/tags"

# 4. Tester alertes
curl "http://localhost:9093/api/v1/alerts"
```

#### Solutions Types
- **Métriques manquantes** : Vérifier endpoints /metrics des services
- **Dashboards vides** : Re-importer dashboards, vérifier datasources
- **Alertes silencieuses** : Valider règles prometheus, tester AlertManager
- **Logs perdus** : Augmenter retention Loki, vérifier Promtail

## Outils de Debugging Intégrés

### Interface Grafana - Debugging
- **URL** : http://localhost:3000/explore
- **Datasources** : Prometheus (métriques) + Loki (logs)
- **Queries utiles** :
  ```promql
  # Services down
  up{job=~"coach-.*"} == 0
  
  # Latence élevée
  histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
  
  # Erreurs API
  rate(http_requests_total{status=~"5.."}[5m])
  
  # Utilisation ressources
  (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
  ```

### Commandes de Diagnostic Rapide
```bash
# Santé globale système
./E5_monitoring/scripts/health_check.sh

# Test bout-en-bout application
python tests/test_integration.py

# Redémarrage services en cas d'urgence
docker-compose -f deployment/docker-compose-monitoring.yml restart
cd E3_model_IA/backend/fastapi_app && python api_service.py &
cd E3_model_IA/backend/django_app && python manage.py runserver 8002 &
```

## Matrice d'Escalade

### Niveau 1 - Auto-Résolution (< 5 min)
- Redémarrage service spécifique
- Nettoyage cache/logs temporaires
- Restart container Docker

### Niveau 2 - Support Technique (< 15 min)
- Investigation logs détaillée
- Analyse métriques historiques
- Correction configuration

### Niveau 3 - Équipe Dev (< 30 min)
- Debug code applicatif
- Rollback déploiement récent
- Patch urgent en production

### Niveau 4 - Architecture (< 1h)
- Modification infrastructure
- Scaling horizontal/vertical
- Migration données

## Historique et Post-Mortem

### Template Incident Report
```markdown
# Incident Report - [YYYY-MM-DD-HH:MM]

## Résumé
- **Début** : [timestamp]
- **Fin** : [timestamp]
- **Durée** : [minutes]
- **Impact** : [utilisateurs/fonctionnalités affectées]
- **Criticité** : [WARNING/CRITICAL]

## Chronologie
- **HH:MM** : Alerte détectée
- **HH:MM** : Investigation démarrée
- **HH:MM** : Cause racine identifiée
- **HH:MM** : Correction appliquée
- **HH:MM** : Service restauré

## Cause Racine
[Description technique détaillée]

## Actions Correctives
- [ ] Correction immédiate appliquée
- [ ] Monitoring renforcé ajouté
- [ ] Documentation mise à jour
- [ ] Tests préventifs créés

## Leçons Apprises
[Améliorations processus/architecture]
```

### Localisation des Incidents
```bash
# Historique incidents
/E5_monitoring/incidents/
├── 2025-01-19-14-30-agent-ia-timeout.md
├── 2025-01-18-09-15-postgresql-lock.md
└── 2025-01-17-16-45-streamlit-crash.md

# Logs archivés
/var/log/coach-ai/
├── application/
├── monitoring/
└── incidents/
```

## Procédures de Recovery

### Backup et Restauration
```bash
# Backup base données
pg_dump -h localhost -U coach_user coach_ia_db > backup_$(date +%Y%m%d_%H%M).sql

# Restauration d'urgence
psql -h localhost -U coach_user coach_ia_db < backup_20250119_1430.sql

# Backup configuration monitoring
tar -czf monitoring_config_$(date +%Y%m%d).tar.gz E5_monitoring/

# Restauration configuration
tar -xzf monitoring_config_20250119.tar.gz
docker-compose -f deployment/docker-compose-monitoring.yml up -d
```

### Tests de Recovery
```bash
# Test recovery agent IA
python tests/test_recovery_agent.py

# Test recovery base données
python tests/test_recovery_database.py

# Test recovery monitoring
python tests/test_recovery_monitoring.py
```

## Contacts et Responsabilités

### Équipe Support
- **DevOps** : Monitoring, infrastructure, alertes
- **Backend** : Agent IA, API, base données
- **Frontend** : Interfaces Django/Streamlit
- **QA** : Tests, validation post-incident

### Outils de Communication
- **Alertes immédiates** : Webhook Slack #incidents
- **Suivi incidents** : Dashboard Grafana temps réel
- **Documentation** : Mise à jour automatique Git

---

**Dernière mise à jour** : 2025-08-19
**Version** : 1.0 (Conformité C21)
**Accessibilité** : WCAG 2.1 AA Compatible