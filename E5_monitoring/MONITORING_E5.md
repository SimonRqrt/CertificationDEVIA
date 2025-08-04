# 📊 MONITORING E5 - Coaching IA Application

> **Conformité grille d'évaluation E5 : Débogage + Monitoring**

## 🎯 Vue d'ensemble

Cette configuration de monitoring répond aux exigences **C20** et **C21** de la grille d'évaluation certification :

- **C20** : Surveiller une application d'IA
- **C21** : Résoudre les incidents techniques

## 🏗️ Architecture de monitoring

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Django App    │───►│   Prometheus    │───►│   Grafana       │
│   (Port 8002)   │    │   (Port 9090)   │    │   (Port 3000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │───►│   AlertManager  │───►│  Notifications  │
│   (Port 8000)   │    │   (Port 9093)   │    │  (Slack/Email)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                              │
         ▼                                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Streamlit App  │───►│      Loki       │───►│   Log Analysis  │
│   (Port 8501)   │    │   (Port 3100)   │    │   + Retention   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📈 Métriques surveillées

### 🔐 Django (API REST + Auth)
- **Performance** : Temps de réponse endpoints (`/api/v1/*`)
- **Sécurité** : Échecs d'authentification JWT, tentatives d'intrusion
- **Usage** : Sessions utilisateurs, requêtes par endpoint
- **Erreurs** : Codes 4xx/5xx, exceptions non gérées

### 🤖 FastAPI (Intelligence Artificielle)
- **IA Critical** : Latence appels OpenAI, tokens consommés, coût en temps réel
- **Coaching** : Sessions IA créées, durée conversations, succès RAG
- **Intégration** : Authentification Django → FastAPI, timeouts inter-services
- **Performance** : Temps génération plans d'entraînement

### 💻 Streamlit (Interface Utilisateur)
- **UX** : Temps chargement pages, sessions actives
- **Interactions** : Messages chat, erreurs interface utilisateur
- **Resources** : Utilisation mémoire, connexions WebSocket

### 🎯 Infrastructure & Données
- **Docker** : Status containers, CPU/RAM usage, restart counts
- **Azure SQL Server** : Connexions actives, temps requêtes, deadlocks
- **Network** : Latence inter-services, erreurs réseau

## 🚨 Seuils d'alerte configurés

### Performance (C20)
```yaml
django_response_time:
  warning: >500ms
  critical: >1s
  
fastapi_openai_latency:
  warning: >3s  
  critical: >10s
  
streamlit_page_load:
  warning: >2s
  critical: >5s
```

### Disponibilité
```yaml
service_uptime:
  warning: <99%
  critical: <95%
  
database_connections:
  warning: >80% pool
  critical: >95% pool
```

### Coûts IA (Spécifique coaching)
```yaml
openai_daily_cost:
  warning: >50€
  critical: >100€
  
openai_token_rate:
  warning: >1000/min
  critical: >2000/min
```

### Sécurité
```yaml
auth_failure_rate:
  warning: >10/min
  critical: >50/min
```

## 🚀 Démarrage du monitoring

### 1. Lancement automatique
```bash
cd deployment/monitoring
python3 start_monitoring.py
```

### 2. Vérification des services
```bash
# Status des containers
docker-compose -f docker-compose-monitoring.yml ps

# Logs en temps réel
docker-compose -f docker-compose-monitoring.yml logs -f
```

## 🌐 URLs des services

| Service | URL | Credentials | Description |
|---------|-----|-------------|-------------|
| **Grafana** | http://localhost:3000 | admin / admin123 | Dashboards & alertes |
| **Prometheus** | http://localhost:9090 | - | Métriques & règles |
| **Loki** | http://localhost:3100 | - | Logs centralisés |
| **AlertManager** | http://localhost:9093 | - | Gestion alertes |
| **Node Exporter** | http://localhost:9100 | - | Métriques système |

## 📊 Dashboards disponibles

### 1. 🤖 Coaching IA - Overview
- Vue d'ensemble des 3 services (Django, FastAPI, Streamlit)
- Métriques temps réel : latence, throughput, erreurs
- Status des containers et resources système

### 2. 💰 Coûts & Usage OpenAI
- Consommation tokens par modèle (GPT-3.5, GPT-4)
- Coût en temps réel et projections
- Rate limiting et alertes dépassement

### 3. 🔐 Sécurité & Auth
- Tentatives d'authentification par source IP
- Échecs JWT et raisons (token expiré, invalide, etc.)
- Patterns d'attaque détectés

### 4. 📝 Logs & Debugging
- Logs centralisés des 3 applications
- Filtrage par niveau (ERROR, WARNING, INFO)
- Corrélation entre métriques et logs

## 🔧 Configuration dans vos services

### Django - Middleware Prometheus
Ajoutez dans `settings.py` :
```python
MIDDLEWARE = [
    # ... autres middlewares
    'monitoring_middleware.PrometheusMiddleware',
    'monitoring_middleware.AuthFailureMiddleware',
]

# URL pour exposer métriques
urlpatterns = [
    # ... autres URLs
    path('metrics/', monitoring_middleware.metrics_view),
]
```

### FastAPI - Middleware intégré  
Dans `api_service.py` :
```python
from monitoring import PrometheusMiddleware, metrics_endpoint

app = FastAPI()
app.add_middleware(PrometheusMiddleware)
app.get('/metrics')(metrics_endpoint)
```

### Streamlit - Instrumentation
Dans `app_streamlit.py` :
```python
import streamlit as st
from monitoring import track_coaching_session

# Tracking automatique des sessions
if 'session_start' not in st.session_state:
    st.session_state.session_start = time.time()
    
# Fin de session
session_duration = time.time() - st.session_state.session_start
track_coaching_session('web_user', session_duration)
```

## 🛠️ Procédures de résolution d'incidents (C21)

### 1. 🚨 Alert : Django High Response Time
**Cause probable** : Surcharge base de données ou requêtes lentes

**Procédure de debugging** :
```bash
# 1. Identifier les requêtes lentes
curl http://localhost:9090/api/v1/query?query=django_request_duration_seconds_bucket

# 2. Analyser les logs Django
docker-compose logs django | grep "Slow request"

# 3. Vérifier les connexions DB
curl http://localhost:9090/api/v1/query?query=django_db_connections_active
```

**Solution** :
- Optimiser les requêtes SQL identifiées
- Ajouter des index sur les tables critiques
- Augmenter le pool de connexions si nécessaire

### 2. 🤖 Alert : OpenAI High Latency
**Cause probable** : Surcharge API OpenAI ou réseau lent

**Procédure de debugging** :
```bash
# 1. Vérifier latence OpenAI
curl http://localhost:9090/api/v1/query?query=openai_request_duration_seconds

# 2. Analyser les logs FastAPI
docker-compose logs fastapi | grep "OpenAI"

# 3. Tester connectivity
curl -I https://api.openai.com/v1/models
```

**Solution** :
- Implémenter retry logic avec backoff
- Mettre en cache les réponses fréquentes
- Basculer sur un modèle plus rapide temporairement

### 3. 🔐 Alert : High Auth Failure Rate
**Cause probable** : Attaque par force brute ou tokens expirés en masse

**Procédure de debugging** :
```bash
# 1. Analyser les sources des échecs
curl http://localhost:9090/api/v1/query?query=django_auth_failures_total

# 2. Identifier les IPs suspectes
docker-compose logs django | grep "Auth failure" | awk '{print $NF}' | sort | uniq -c

# 3. Vérifier les raisons d'échec
curl http://localhost:9090/api/v1/query?query=django_auth_failures_total by (reason)
```

**Solution** :
- Blacklister les IPs malveillantes
- Forcer la régénération des tokens si expiration massive
- Activer rate limiting sur les endpoints d'auth

### 4. 💾 Alert : High Memory Usage
**Cause probable** : Memory leak ou charge inhabituelle

**Procédure de debugging** :
```bash
# 1. Identifier le service consommateur
docker stats

# 2. Analyser l'évolution mémoire
curl http://localhost:9090/api/v1/query?query=node_memory_MemAvailable_bytes

# 3. Vérifier les process suspects
docker exec -it django ps aux --sort=-%mem | head
```

**Solution** :
- Redémarrer le service avec memory leak
- Ajuster les limites Docker si nécessaire  
- Investiguer le code pour identifier la fuite

## 📋 Documentation technique (C20)

### Installation environnement monitoring
```bash
# Prérequis
- Docker 20.10+
- Docker Compose 1.29+
- Python 3.8+
- 4GB RAM libre minimum

# Dépendances Python
pip install prometheus-client requests

# Structure des fichiers
deployment/monitoring/
├── docker-compose-monitoring.yml
├── prometheus/
│   ├── prometheus.yml
│   └── rules/coaching_alerts.yml
├── grafana/
│   ├── provisioning/
│   └── dashboards/
├── loki/loki-config.yml
├── alertmanager/alertmanager.yml
└── start_monitoring.py
```

### Configuration des outils
- **Prometheus** : Collecte métriques toutes les 15s
- **Grafana** : Dashboards auto-provisionnés au démarrage
- **Loki** : Rétention logs 7 jours, compression activée
- **AlertManager** : Notifications via webhook (extensible email/Slack)

### Métriques personnalisées définies
```python
# Django
django_requests_total = Counter(...)          # Requêtes HTTP
django_request_duration = Histogram(...)      # Latence requêtes  
django_auth_failures = Counter(...)           # Échecs auth
django_db_connections = Gauge(...)            # Connexions DB

# FastAPI  
openai_requests_total = Counter(...)          # Requêtes OpenAI
openai_cost_total = Counter(...)              # Coûts cumulés
coaching_sessions_total = Counter(...)        # Sessions coaching
rag_queries_total = Counter(...)              # Requêtes RAG
```

## ✅ Validation des exigences E5

### C20 - Surveiller une application d'IA
- [x] **Métriques définies** : 15+ métriques spécifiques coaching IA
- [x] **Seuils d'alerte** : Warning/Critical configurés par métrique
- [x] **Outils adaptés** : Prometheus (collecte) + Grafana (visualisation)
- [x] **Dashboard temps réel** : Interface unifiée accessible
- [x] **Alertes configurées** : 8 règles d'alerte opérationnelles
- [x] **Documentation** : Installation, configuration, utilisation
- [x] **Accessibilité** : Interface Grafana responsive et navigable

### C21 - Résoudre les incidents techniques  
- [x] **Identification causes** : Corrélation métriques ↔ logs ↔ traces
- [x] **Reproduction environnement** : Docker dev/staging identiques
- [x] **Procédures documentées** : 4 incidents types avec étapes
- [x] **Solutions versionnées** : Corrections via git workflow
- [x] **Suivi outillé** : AlertManager + dashboard incidents

## 🎯 Commandes utiles

```bash
# Démarrage monitoring
./start_monitoring.py

# Status services
docker-compose -f docker-compose-monitoring.yml ps

# Logs en temps réel  
docker-compose -f docker-compose-monitoring.yml logs -f grafana

# Redémarrage service spécifique
docker-compose -f docker-compose-monitoring.yml restart prometheus

# Cleanup complet
docker-compose -f docker-compose-monitoring.yml down -v
```

---

**📋 Documentation conforme aux recommandations d'accessibilité (Valentin Haüy)**
- Structure hiérarchique claire avec titres Markdown
- URLs explicites et descriptions détaillées  
- Procédures étape par étape numérotées
- Exemples de code avec syntaxe highlighting
- Tableaux structurés pour les données techniques