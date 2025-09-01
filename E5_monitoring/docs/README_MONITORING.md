# E5 - Monitoring et Observabilité Coach AI

> **Critères certification** : C11 (Monitoring modèle IA) et C20 (Surveillance seuils et alertes)

## Objectif
Architecture complète de monitoring pour Coach AI avec surveillance temps réel, alerting intelligent et notifications automatisées.

## Architecture de Monitoring

### Services Déployés
- **Prometheus** (port 9090) : Collecte des métriques
- **Grafana** (port 3000) : Dashboards et visualisation temps réel
- **AlertManager** (port 9093) : Gestion des alertes
- **Node Exporter** (port 9100) : Métriques système

### Services Monitorés
- **FastAPI** (coach-api-fastapi) : API IA Coach AI 
- **Django** (coach-django) : Interface web administrative
- **Streamlit** (coach-streamlit) : Interface utilisateur
- **PostgreSQL** (coach-postgresql) : Base de données

## Métriques Surveillées du Modèle IA

### 1. Métriques de Performance
- **`openai_response_time_seconds`** : Temps de réponse de l'API OpenAI
- **`agent_ia_requests_total`** : Nombre total de requêtes vers l'agent IA
- **`rag_knowledge_base_queries`** : Requêtes vers la base de connaissances RAG

### 2. Métriques de Disponibilité
- **`up{job="coach-api-fastapi"}`** : Statut API FastAPI (1=UP, 0=DOWN)
- **`up{job="coach-django"}`** : Statut interface Django
- **`up{job="coach-streamlit"}`** : Statut interface Streamlit
- **`up{job="coach-postgresql"}`** : Statut base de données PostgreSQL

### 3. Métriques Métier
- **`training_plans_generated_total`** : Nombre de plans d'entraînement générés
- **`coaching_sessions_active`** : Sessions de coaching actives
- **`openai_api_costs_usd`** : Coûts API OpenAI en temps réel

## Installation et Configuration

### Prérequis
- Docker et Docker Compose installés
- Port 3000, 9090, 9093, 3100, 9100 disponibles

### Démarrage de la Stack
```bash
cd deployment
docker compose -f docker-compose.yml up -d
```

## 🚨 Système d'Alerting (C20)

### Architecture d'Alerting
```
Métriques → Prometheus → Règles d'alerte → Alertmanager → Webhook Receiver
```

### Webhook Receiver 
- **Script** : `E5_monitoring/scripts/webhook_receiver.py`
- **Port** : 5001
- **Logs** : `E5_monitoring/webhook.log`
- **API** : http://localhost:5001/alerts (voir alertes reçues)

### Règles d'Alerte Configurées
- **HighMemoryUsage** : > 85% mémoire système
- **LowTrainingPlanGeneration** : < 1 plan/heure  
- **OpenAIHighLatency** : > 10s réponse OpenAI
- **ServiceDown** : Service indisponible

### URLs de Vérification
- **Alertmanager UI** : http://localhost:9093
- **Prometheus Rules** : http://localhost:9090/rules  
- **Webhook Status** : http://localhost:5001/alerts

### Test Manuel d'Alerte
```bash
# Lancer le webhook receiver
python3 E5_monitoring/scripts/webhook_receiver.py &

# Envoyer alerte test
curl -X POST http://localhost:9093/api/v2/alerts \
-H 'Content-Type: application/json' \
-d '[{
  "labels": {"alertname": "TestAlert", "severity": "critical"},
  "annotations": {"summary": "Test alerte Coach AI"}
}]'

# Vérifier réception
curl http://localhost:5001/alerts | jq .
```

### Vérification des Services
```bash
# Vérifier que tous les services sont UP
cd deployment && docker compose -f docker-compose-monitoring.yml ps

# Tester Prometheus
curl "http://localhost:9090/api/v1/query?query=up"

# Tester Grafana
curl http://localhost:3000/api/health
```

## Accès aux Dashboards

### Grafana (Interface Principal)
- **URL** : http://localhost:3000
- **Credentials** : admin / admin123
- **Dashboards disponibles** :
  - "Coach AI - Monitoring Temps Réel" (basique)
  - "Coach AI - Métriques Réelles Collectées" (complet avec CPU, mémoire, réseau)
- **Dossier** : "Coach AI - Architecture Unifiée"

### Prometheus (Métriques Brutes)
- **URL** : http://localhost:9090
- **Interface** : Console de requêtes PromQL

### AlertManager (Gestion Alertes)
- **URL** : http://localhost:9093
- **Configuration** : Alertes email et Slack configurées

## Alertes Configurées

### Alertes Critiques
1. **`CoachAIServiceDown`** : Service principal inaccessible
2. **`CoachAISlowResponse`** : Temps de réponse > 10 secondes
3. **`RAGKnowledgeBaseError`** : Erreur base de connaissances
4. **`OpenAICostAlert`** : Coûts API > seuil défini

### Seuils d'Alerte Détaillés

#### Critères Techniques
- **Temps de réponse Agent IA** : > 15 secondes (critique), > 10 secondes (warning)
- **Taux d'erreur global** : > 5% sur 5 minutes (critique), > 2% (warning)
- **Disponibilité services** : < 99% sur 15 minutes (critique), < 99.5% (warning)
- **Utilisation CPU** : > 80% (critique), > 70% (warning)
- **Utilisation mémoire** : > 85% (critique), > 75% (warning)
- **Espace disque** : < 10% libre (critique), < 20% (warning)

#### Critères Métier Spécifiques
- **Plans d'entraînement générés** : < 1/heure pendant 30min (warning)
- **Coûts API OpenAI** : > 10$/heure (critique), > 5$/heure (warning)
- **Latence base de données** : > 2 secondes P95 (critique), > 1 seconde (warning)
- **Requêtes RAG échouées** : > 10% sur 5min (critique), > 5% (warning)
- **Sessions utilisateur actives** : < 1 pendant 1h en heures ouvrées (warning)

## Tests et Validation

### Test Bac à Sable
```bash
# Tester une métrique simple
curl "http://localhost:9090/api/v1/query?query=up{job=~\"coach-.*\"}"

# Vérifier dashboard Grafana
curl -u admin:admin123 "http://localhost:3000/api/search?query=Coach"
```

### Validation Temps Réel
1. Accéder au dashboard "Coach AI - Métriques Réelles Collectées"
2. Vérifier que les métriques s'actualisent toutes les 30 secondes
3. Confirmer les statuts Coach AI :
   - FastAPI, Django, Streamlit : UP (vert)
   - PostgreSQL : DOWN (rouge, normal si non dockerisé)
4. Valider les graphiques temps réel : CPU, mémoire, réseau, Prometheus

## Accessibilité

### Standards Respectés
- Interface Grafana responsive (mobile/desktop)
- Contraste élevé pour les alertes (rouge/vert)
- Navigation clavier supportée
- Lecteurs d'écran compatibles avec les tableaux de bord

### Configuration Équipes
- **Administrateurs** : Accès complet Grafana (admin/admin123)
- **Développeurs** : Accès lecture Prometheus et dashboards
- **Équipes métier** : Dashboards simplifiés sans accès configuration

## Maintenance

### Sauvegarde
```bash
# Sauvegarder les données Prometheus
docker compose exec prometheus tar -czf /prometheus/backup-$(date +%Y%m%d).tar.gz /prometheus

# Sauvegarder configuration Grafana
docker compose exec grafana tar -czf /var/lib/grafana/backup-$(date +%Y%m%d).tar.gz /var/lib/grafana
```

### Mise à Jour
```bash
# Redémarrer un service spécifique
docker compose -f docker-compose-monitoring.yml restart grafana

# Mise à jour complète
cd deployment
docker compose -f docker-compose-monitoring.yml down
docker compose -f docker-compose-monitoring.yml pull
docker compose -f docker-compose-monitoring.yml up -d
```

## Support et Dépannage

### Logs des Services
```bash
# Logs Prometheus
docker compose logs prometheus

# Logs Grafana
docker compose logs grafana

# Logs AlertManager
docker compose logs alertmanager

# Logs généraux
docker compose logs
```

### Scripts de Diagnostic
```bash
# Test santé complète de la stack
cd E5_monitoring
./scripts/health_check_monitoring.sh

# Validation métriques temps réel
curl "http://localhost:9090/api/v1/query?query=up{job=~'coach-.*'}"

# Test alertes fonctionnelles
curl "http://localhost:9093/api/v1/alerts"
```

### Procédures d'Urgence
```bash
# Redémarrage complet monitoring
docker compose -f docker-compose-monitoring.yml down
docker compose -f docker-compose-monitoring.yml up -d

# Backup configuration avant modification
tar -czf backup_monitoring_$(date +%Y%m%d_%H%M).tar.gz .

# Restauration dernière configuration stable
tar -xzf backup_monitoring_20250819_1430.tar.gz
```

### Contact Support
- **Documentation complète** : `/E5_monitoring/documentation_debugging_c21.md`
- **Procédures incidents** : Matrice d'escalade niveau 1-4
- **Configuration** : Fichiers dans `/E5_monitoring/`
- **Issues** : Créer ticket avec logs, métriques et étapes reproduction

---

**Dernière mise à jour** : 2025-08-15
**Version** : 1.0 (Conformité C11)
**Accessibilité** : WCAG 2.1 AA Compatible