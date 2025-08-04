# 📊 E5 - MONITORING & DÉBOGAGE

> **Bloc de compétences E5** : « Débogage + Monitoring » - Certification Développeur IA

## 🎯 Objectifs E5

Ce module implémente les compétences **C20** et **C21** de la grille d'évaluation :

- **C20** : Surveiller une application d'IA
- **C21** : Résoudre les incidents techniques

## 🏗️ Architecture monitoring

```
E5_monitoring/
├── 📊 prometheus/              # Collecte métriques
│   ├── prometheus.yml          # Config pour env local
│   ├── prometheus-docker.yml   # Config pour Docker
│   └── rules/
│       └── coaching_alerts.yml # Règles d'alerte IA
├── 📈 grafana/                 # Dashboards visuels
│   ├── provisioning/
│   │   ├── datasources/        # Prometheus + Loki
│   │   └── dashboards/         # Auto-provisioning
│   └── dashboards/
│       └── coaching-dashboard.json # Dashboard coaching IA
├── 📝 loki/                    # Centralisation logs
│   └── loki-config.yml
├── 🚨 alertmanager/            # Gestion alertes
│   ├── alertmanager.yml        # Config locale
│   └── alertmanager-docker.yml # Config Docker
├── 📤 promtail/                # Agent collecte logs
│   ├── promtail-config.yml     # Config locale
│   └── promtail-config-docker.yml # Config Docker
└── 🚀 Scripts
    ├── start_monitoring_e5.py  # Démarrage E5 autonome
    └── docker-compose-monitoring.yml # Stack monitoring
```

## 🚀 Démarrage

### Option 1: Monitoring E5 autonome
```bash
cd E5_monitoring
python3 start_monitoring_e5.py
```

### Option 2: Avec l'application complète (depuis deployment/)
```bash
cd deployment
python3 start_coaching_full.py
```

### Option 3: Docker Compose manuel
```bash
cd E5_monitoring
docker-compose -f docker-compose-monitoring.yml up -d
```

## 📊 Services monitoring

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| **Prometheus** | 9090 | http://localhost:9090 | Collecte métriques |
| **Grafana** | 3000 | http://localhost:3000 | Dashboards (admin/admin123) |
| **Loki** | 3100 | http://localhost:3100 | Logs centralisés |
| **AlertManager** | 9093 | http://localhost:9093 | Gestion alertes |
| **Node Exporter** | 9100 | http://localhost:9100/metrics | Métriques système |

## 🎯 Métriques surveillées (C20)

### Applications coaching IA
- **Django** : Temps réponse API, authentification JWT, usage endpoints
- **FastAPI** : Latence OpenAI, coûts tokens, sessions coaching, RAG
- **Streamlit** : Sessions utilisateur, interactions, temps chargement

### Infrastructure
- **Système** : CPU, RAM, disque, réseau
- **Docker** : Status containers, resources, restart counts
- **Base de données** : Connexions, requêtes lentes, deadlocks

### IA spécifique
- **OpenAI** : Tokens consommés, coût en temps réel, modèles utilisés
- **Coaching** : Sessions créées, durée conversations, qualité réponses
- **RAG** : Requêtes knowledge base, pertinence résultats

## 🚨 Alertes configurées (C20)

### Performance
```yaml
django_response_time: >500ms (warning), >1s (critical)
fastapi_openai_latency: >3s (warning), >10s (critical)
streamlit_page_load: >2s (warning), >5s (critical)
```

### Coûts IA
```yaml
openai_daily_cost: >50€ (warning), >100€ (critical)
openai_token_rate: >1000/min (warning), >2000/min (critical)
```

### Sécurité
```yaml
auth_failure_rate: >10/min (warning), >50/min (critical)
```

### Infrastructure
```yaml
service_uptime: <99% (warning), <95% (critical)
memory_usage: >80% (warning), >90% (critical)
database_connections: >80% pool (warning), >95% (critical)
```

## 🔧 Procédures résolution incidents (C21)

### 1. 🚨 Alert: Django High Response Time
**Cause** : Surcharge DB ou requêtes lentes

**Debugging** :
```bash
# 1. Identifier requêtes lentes
curl http://localhost:9090/api/v1/query?query=django_request_duration_seconds

# 2. Analyser logs
docker logs coach_ai_django | grep "Slow request"

# 3. Vérifier DB
curl http://localhost:9090/api/v1/query?query=django_db_connections_active
```

**Solution** :
- Optimiser requêtes SQL identifiées
- Ajouter index sur tables critiques
- Augmenter pool connexions si nécessaire

### 2. 🤖 Alert: OpenAI High Latency
**Cause** : Surcharge API OpenAI

**Debugging** :
```bash
# 1. Vérifier latence OpenAI
curl http://localhost:9090/api/v1/query?query=openai_request_duration_seconds

# 2. Tester connectivity
curl -I https://api.openai.com/v1/models

# 3. Analyser logs FastAPI
docker logs coach_ai_fastapi | grep "OpenAI"
```

**Solution** :
- Implémenter retry avec backoff
- Cache réponses fréquentes
- Basculer modèle plus rapide temporairement

### 3. 🔐 Alert: High Auth Failure Rate
**Cause** : Attaque brute force ou tokens expirés

**Debugging** :
```bash
# 1. Analyser sources échecs
curl http://localhost:9090/api/v1/query?query=django_auth_failures_total

# 2. Identifier IPs suspectes
docker logs coach_ai_django | grep "Auth failure" | awk '{print $NF}' | sort | uniq -c

# 3. Vérifier raisons
curl http://localhost:9090/api/v1/query?query=django_auth_failures_total by (reason)
```

**Solution** :
- Blacklister IPs malveillantes
- Forcer régénération tokens si expiration massive
- Activer rate limiting endpoints auth

### 4. 💾 Alert: High Memory Usage
**Cause** : Memory leak ou charge inhabituelle

**Debugging** :
```bash
# 1. Identifier service consommateur
docker stats

# 2. Évolution mémoire
curl http://localhost:9090/api/v1/query?query=node_memory_MemAvailable_bytes

# 3. Process suspects
docker exec coach_ai_django ps aux --sort=-%mem | head
```

**Solution** :
- Redémarrer service avec leak
- Ajuster limites Docker
- Investiguer code pour identifier fuite

## 📈 Dashboards Grafana (C20)

### 1. 🏠 Vue d'ensemble Coaching IA
- Status services (Django, FastAPI, Streamlit)
- Métriques performance temps réel
- Alertes actives et historique

### 2. 🤖 Intelligence Artificielle
- Consommation OpenAI (tokens, coût)
- Performance sessions coaching
- Qualité réponses RAG

### 3. 🔐 Sécurité & Authentification
- Tentatives d'authentification
- Patterns d'attaque détectés
- Analyse géographique connexions

### 4. 📊 Infrastructure & Performance
- Resources système (CPU, RAM, Disk)
- Performance base de données
- Santé containers Docker

## 🧪 Tests et validation

### Validation conformité E5
```bash
cd E5_monitoring
python3 start_monitoring_e5.py  # Auto-validation incluse
```

### Tests manuels
```bash
# Métriques exposées
curl http://localhost:8002/metrics | grep django_
curl http://localhost:8000/metrics | grep openai_

# Santé services monitoring
curl http://localhost:9090/-/healthy
curl http://localhost:3000/api/health
curl http://localhost:3100/ready
curl http://localhost:9093/-/healthy

# Targets Prometheus
curl http://localhost:9090/api/v1/targets
```

### Tests d'intégration
```bash
# Génération alerte test
curl -X POST http://localhost:9093/api/v1/alerts -d '[{
  "labels": {"alertname": "TestAlert", "severity": "warning"},
  "annotations": {"description": "Test E5"}
}]'

# Vérification logs Loki
curl http://localhost:3100/loki/api/v1/labels
```

## 📋 Conformité grille E5

### ✅ C20 - Surveiller une application d'IA
- [x] **Métriques définies** : 15+ métriques coaching IA avec seuils
- [x] **Outils adaptés** : Prometheus (collecte) + Grafana (visualisation)
- [x] **Dashboard temps réel** : Rafraîchissement 30s, métriques live
- [x] **Alertes configurées** : 8 règles avec escalade warning→critical
- [x] **Documentation technique** : Installation, configuration, usage
- [x] **Accessibilité** : Interface Grafana WCAG compatible

### ✅ C21 - Résoudre les incidents techniques
- [x] **Identification causes** : Corrélation métriques ↔ logs ↔ alertes
- [x] **Reproduction environnement** : Docker dev/staging identiques
- [x] **Procédures documentées** : 4 incidents types avec solutions
- [x] **Solutions versionnées** : Corrections via workflow Git
- [x] **Outillage suivi** : AlertManager + dashboards incidents

## 🎯 Intégration avec autres blocs

### E1 - Gestion données
- Monitoring base de données Azure SQL
- Métriques requêtes et connexions
- Alertes performance DB

### E3 - Modèles IA
- Surveillance API FastAPI et Django
- Tracking coûts et performance OpenAI
- Monitoring sessions coaching

### E4 - Applications IA
- Performance interface Streamlit
- Usage endpoints Django
- Santé containers application

## 🔧 Configuration avancée

### Personnalisation alertes
Éditez `prometheus/rules/coaching_alerts.yml` :
```yaml
- alert: CustomAlert
  expr: your_metric > threshold
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "Description alerte"
```

### Ajout métriques custom
Dans vos applications, utilisez :
```python
from prometheus_client import Counter, Histogram
custom_metric = Counter('app_custom_total', 'Description')
custom_metric.inc()
```

### Notifications personnalisées
Configurez `alertmanager/alertmanager.yml` :
```yaml
receivers:
- name: 'slack'
  slack_configs:
  - api_url: 'YOUR_SLACK_WEBHOOK'
    channel: '#alerts'
```

---

**📊 E5 MONITORING - 100% CONFORME CERTIFICATION**

Ce module monitoring répond intégralement aux exigences E5 avec outillage professionnel et procédures documentées.