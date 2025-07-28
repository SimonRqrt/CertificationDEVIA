# 🐳 MONITORING E5 DOCKERISÉ - Guide complet

## 🎯 Vue d'ensemble

Monitoring intégré pour votre application Coaching IA avec conformité **E5** de la grille certification.

**Architecture** : Application + Monitoring dans une seule stack Docker unifiée.

## 🚀 Démarrage rapide

### 1. Démarrage complet (recommandé)
```bash
cd deployment
python3 start_coaching_full.py
```

### 2. Démarrage Manuel Docker
```bash
cd deployment
docker-compose -f docker-compose-full.yml up --build -d
```

### 3. Validation du déploiement
```bash
cd deployment
./validate_monitoring.sh
```

## 🏗️ Architecture déployée

### Services Application (3)
- **Django** : `coach_ai_django:8002` - API REST + Admin
- **FastAPI** : `coach_ai_fastapi:8000` - IA + OpenAI  
- **Streamlit** : `coach_ai_streamlit:8501` - Interface utilisateur

### Services Monitoring E5 (6)
- **Prometheus** : `coach_ai_prometheus:9090` - Collecte métriques
- **Grafana** : `coach_ai_grafana:3000` - Dashboards visuels  
- **Loki** : `coach_ai_loki:3100` - Centralisation logs
- **Promtail** : `coach_ai_promtail` - Agent collecte logs
- **AlertManager** : `coach_ai_alertmanager:9093` - Gestion alertes
- **Node Exporter** : `coach_ai_node_exporter:9100` - Métriques système

**📁 Configuration** : Tous les fichiers monitoring sont dans `E5_monitoring/`

### Services Utilitaires (1)
- **Webhook Receiver** : `coach_ai_webhook:5001` - Réception alertes

## 📊 URLs disponibles

| Service | URL | Credentials | Description |
|---------|-----|-------------|-------------|
| **🏠 Django Dashboard** | http://localhost:8002/api/v1/core/dashboard/ | - | Interface principale |
| **🎯 Assistant Objectifs** | http://localhost:8002/api/v1/coaching/running-wizard/ | - | Formulaires coaching |
| **📋 Django Admin** | http://localhost:8002/admin/ | admin/admin | Administration |
| **🤖 FastAPI Docs** | http://localhost:8000/docs | - | API documentation |
| **💬 Streamlit Chat** | http://localhost:8501/ | - | Interface conversationelle |
| **📈 Grafana** | http://localhost:3000 | admin/admin123 | **Dashboards E5** |
| **🎯 Prometheus** | http://localhost:9090 | - | Métriques brutes |
| **📝 Loki** | http://localhost:3100 | - | Logs (via Grafana) |
| **🚨 AlertManager** | http://localhost:9093 | - | **Alertes E5** |

## 📈 Métriques exposées

### Django (`/metrics`)
```prometheus
# Performance
django_http_requests_total{method="GET",endpoint="/api/v1/activities/",status="200"} 42
django_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/activities/",le="0.5"} 40

# Authentification
django_auth_failures_total{reason="jwt_invalid"} 3
django_active_requests 2

# Base de données
django_db_connections_active 5
django_db_connections_max 100
```

### FastAPI (`/metrics`)
```prometheus
# IA Performance
openai_requests_total{model="gpt-3.5-turbo",status="success"} 28
openai_request_duration_seconds_bucket{model="gpt-3.5-turbo",le="5.0"} 25
openai_tokens_total{model="gpt-3.5-turbo",type="completion"} 15420
openai_cost_total_usd{model="gpt-3.5-turbo"} 0.031

# Coaching
coaching_sessions_total{user_type="web_user"} 12
coaching_session_duration_seconds_bucket{le="60.0"} 10
rag_queries_total{status="success"} 45
```

## 🚨 Alertes configurées (E5)

### Performance
- **Django High Response Time** : >500ms (warning), >1s (critical)
- **FastAPI High Latency** : >1s (warning), >3s (critical)  
- **OpenAI High Latency** : >10s (critical)

### Coûts IA
- **OpenAI High Cost** : >10€/h (warning), >50€/h (critical)
- **OpenAI Token Rate Limit** : >1000/min (warning), >2000/min (critical)

### Sécurité  
- **High Auth Failure Rate** : >10/min (warning), >50/min (critical)

### Infrastructure
- **Service Down** : up == 0 (critical)
- **High Memory Usage** : >90% (critical)
- **Database Connections High** : >80% pool (warning)

## 🔧 Configuration réseau Docker

### Réseau unifié
```yaml
networks:
  coach_ai_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Communication inter-services
- **Django ↔ Prometheus** : `coach_ai_django:8002/metrics`
- **FastAPI ↔ Prometheus** : `coach_ai_fastapi:8000/metrics`
- **Prometheus ↔ AlertManager** : `coach_ai_alertmanager:9093`
- **Grafana ↔ Prometheus** : `coach_ai_prometheus:9090`
- **Grafana ↔ Loki** : `coach_ai_loki:3100`

## 📝 Volumes et logs

### Volumes persistants
```yaml
volumes:
  prometheus_data: # Métriques historiques
  grafana_data:    # Dashboards et config
  loki_data:       # Logs historiques
  alertmanager_data: # État des alertes
  monitoring_logs: # Logs applicatifs partagés
```

### Logs applicatifs
- **Django** : `/var/log/django/` (dans volume `monitoring_logs`)
- **FastAPI** : `/var/log/fastapi/` (dans volume `monitoring_logs`)
- **Streamlit** : `/var/log/streamlit/` (dans volume `monitoring_logs`)

## 🧪 Validation et tests

### Health checks configurés
Tous les services ont des health checks Docker :
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:9090/-/healthy"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### Script de validation
```bash
# Validation complète
./validate_monitoring.sh

# Validation services spécifiques
curl http://localhost:8002/metrics | grep django_
curl http://localhost:8000/metrics | grep openai_
curl http://localhost:9090/api/v1/targets
```

### Tests d'intégration
```bash
# Status containers
docker-compose -f docker-compose-full.yml ps

# Logs en temps réel
docker-compose -f docker-compose-full.yml logs -f

# Health check manuel
docker-compose -f docker-compose-full.yml exec django curl http://localhost:8002/metrics
```

## 🔍 Debugging et troubleshooting

### Problèmes fréquents

#### 1. Service ne démarre pas
```bash
# Vérifier les logs
docker-compose -f docker-compose-full.yml logs [service_name]

# Vérifier les dépendances
docker-compose -f docker-compose-full.yml up django prometheus
```

#### 2. Métriques non collectées
```bash
# Tester l'endpoint depuis Prometheus
docker exec coach_ai_prometheus wget -qO- http://coach_ai_django:8002/metrics

# Vérifier la configuration Prometheus
docker exec coach_ai_prometheus cat /etc/prometheus/prometheus.yml
```

#### 3. Grafana sans données
```bash
# Tester datasource Prometheus
curl -u admin:admin123 "http://localhost:3000/api/datasources/proxy/1/api/v1/query?query=up"

# Vérifier configuration datasources
docker exec coach_ai_grafana cat /etc/grafana/provisioning/datasources/datasources.yml
```

#### 4. Alertes non envoyées
```bash
# Vérifier les règles d'alerte
curl http://localhost:9090/api/v1/rules

# Tester webhook
curl -X POST http://localhost:5001/webhook -H "Content-Type: application/json" -d '{"test":"alert"}'

# Logs AlertManager
docker-compose -f docker-compose-full.yml logs alertmanager
```

### Commandes utiles

```bash
# Redémarrage service spécifique
docker-compose -f docker-compose-full.yml restart prometheus

# Rebuild service modifié
docker-compose -f docker-compose-full.yml up --build -d django

# Nettoyage complet
docker-compose -f docker-compose-full.yml down -v
docker system prune -f

# Inspection réseau
docker network inspect deployment_coach_ai_network

# Monitoring resources
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

## 📋 Conformité E5 (Grille certification)

### ✅ C20 - Surveiller une application d'IA
- [x] **Métriques définies** : 15+ métriques spécifiques coaching IA
- [x] **Seuils d'alerte** : Warning/Critical configurés par métrique  
- [x] **Outils adaptés** : Prometheus + Grafana + AlertManager
- [x] **Dashboard temps réel** : Grafana avec refresh 30s
- [x] **Alertes configurées** : 8 règles opérationnelles
- [x] **Documentation technique** : Installation, configuration, usage
- [x] **Accessibilité** : Interface Grafana responsive

### ✅ C21 - Résoudre les incidents techniques
- [x] **Identification causes** : Corrélation métriques ↔ logs
- [x] **Reproduction environnement** : Docker dev identique
- [x] **Procédures documentées** : 4 types d'incidents couverts
- [x] **Solutions versionnées** : Git workflow intégré
- [x] **Outillage de suivi** : AlertManager + dashboard incidents

## 🎯 Commandes essentielles

```bash
# Démarrage
python3 start_coaching_full.py

# Validation
./validate_monitoring.sh

# Status
docker-compose -f docker-compose-full.yml ps

# Logs
docker-compose -f docker-compose-full.yml logs -f grafana

# Arrêt
docker-compose -f docker-compose-full.yml down

# Nettoyage complet  
docker-compose -f docker-compose-full.yml down -v && docker system prune -f
```

---

**🎉 Monitoring E5 Dockerisé - 100% Opérationnel**

Cette configuration vous donne une stack complète prête pour la certification avec monitoring professionnel intégré.