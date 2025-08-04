# 🐳 INTÉGRATION MONITORING DOCKER

## Ajouts requis dans vos Dockerfiles

### 1. Django Dockerfile
Ajoutez dans `deployment/django.Dockerfile` :

```dockerfile
# Installation dépendances monitoring
COPY deployment/monitoring/requirements-monitoring.txt /tmp/
RUN pip install -r /tmp/requirements-monitoring.txt

# Copie du middleware monitoring
COPY E3_model_IA/backend/django_app/monitoring_middleware.py /app/E3_model_IA/backend/django_app/

# Création répertoire logs
RUN mkdir -p /var/log/django /app/logs
RUN chmod 777 /var/log/django /app/logs
```

### 2. FastAPI Dockerfile  
Ajoutez dans `deployment/fastapi.Dockerfile` :

```dockerfile
# Installation dépendances monitoring
COPY deployment/monitoring/requirements-monitoring.txt /tmp/
RUN pip install -r /tmp/requirements-monitoring.txt

# Copie du module monitoring
COPY E3_model_IA/backend/fastapi_app/monitoring.py /app/E3_model_IA/backend/fastapi_app/

# Création répertoire logs
RUN mkdir -p /var/log/fastapi
RUN chmod 777 /var/log/fastapi
```

### 3. Streamlit Dockerfile
Ajoutez dans `deployment/streamlit.Dockerfile` :

```dockerfile
# Installation dépendances monitoring
COPY deployment/monitoring/requirements-monitoring.txt /tmp/
RUN pip install -r /tmp/requirements-monitoring.txt

# Création répertoire logs
RUN mkdir -p /var/log/streamlit
RUN chmod 777 /var/log/streamlit
```

## Configuration dans le code

### Django - settings.py
```python
# Ajout du middleware monitoring
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'monitoring_middleware.PrometheusMiddleware',  # AJOUT
    'monitoring_middleware.AuthFailureMiddleware', # AJOUT
    # ... autres middlewares
]

# URL pour les métriques
PROMETHEUS_METRICS_ENABLED = True
```

### Django - urls.py (main)
```python
from monitoring_middleware import metrics_view

urlpatterns = [
    # ... autres URLs
    path('metrics/', metrics_view, name='metrics'),
]
```

### FastAPI - api_service.py
```python
from monitoring import PrometheusMiddleware, metrics_endpoint, OpenAIClientWrapper

# Ajout du middleware
app.add_middleware(PrometheusMiddleware)

# Endpoint métriques
@app.get("/metrics")
async def get_metrics():
    return await metrics_endpoint()

# Wrapper OpenAI (si utilisé)
# openai_client = OpenAIClientWrapper(openai_client)
```

### Streamlit - app_streamlit.py
```python
import time
import streamlit as st
from prometheus_client import Counter, Histogram, start_http_server

# Métriques Streamlit
streamlit_sessions = Counter('streamlit_sessions_total', 'Total Streamlit sessions')
streamlit_interactions = Counter('streamlit_interactions_total', 'User interactions', ['type'])

# Démarrage serveur métriques (port alternatif)
try:
    start_http_server(8502)  # Port différent de Streamlit
except:
    pass  # Server déjà démarré

# Tracking des sessions
if 'session_tracked' not in st.session_state:
    streamlit_sessions.inc()
    st.session_state.session_tracked = True
```

## Test de l'intégration

### Vérification métriques exposées
```bash
# Django
curl http://localhost:8002/metrics

# FastAPI  
curl http://localhost:8000/metrics

# Streamlit (si configuré)
curl http://localhost:8502/metrics
```

### Vérification logs
```bash
# Logs Docker
docker-compose -f docker-compose-full.yml logs django
docker-compose -f docker-compose-full.yml logs fastapi
docker-compose -f docker-compose-full.yml logs streamlit

# Logs dans les volumes
docker exec coach_ai_django ls -la /var/log/django
docker exec coach_ai_fastapi ls -la /var/log/fastapi
```

### Vérification Prometheus targets
```bash
# API Prometheus
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

## Troubleshooting

### Problème 1: Métriques non exposées
```bash
# Vérifier l'import du middleware
docker exec coach_ai_django python -c "import monitoring_middleware; print('OK')"

# Vérifier les logs d'erreur
docker-compose -f docker-compose-full.yml logs django | grep -i error
```

### Problème 2: Prometheus ne scrape pas
```bash
# Vérifier la configuration Prometheus
docker exec coach_ai_prometheus cat /etc/prometheus/prometheus.yml

# Tester la connectivité
docker exec coach_ai_prometheus wget -qO- http://coach_ai_django:8002/metrics
```

### Problème 3: Grafana sans données
```bash
# Vérifier les datasources
curl -u admin:admin123 http://localhost:3000/api/datasources

# Tester requête Prometheus depuis Grafana
curl -u admin:admin123 "http://localhost:3000/api/datasources/proxy/1/api/v1/query?query=up"
```

## Script de validation complète

```bash
#!/bin/bash
# validation_monitoring.sh

echo "🔍 Validation monitoring intégré..."

# Services principaux
echo "📊 Vérification services..."
curl -s http://localhost:8002/admin/ > /dev/null && echo "✅ Django UP" || echo "❌ Django DOWN"
curl -s http://localhost:8000/docs > /dev/null && echo "✅ FastAPI UP" || echo "❌ FastAPI DOWN"  
curl -s http://localhost:8501/ > /dev/null && echo "✅ Streamlit UP" || echo "❌ Streamlit DOWN"

# Monitoring
echo "📈 Vérification monitoring..."
curl -s http://localhost:9090/ > /dev/null && echo "✅ Prometheus UP" || echo "❌ Prometheus DOWN"
curl -s http://localhost:3000/ > /dev/null && echo "✅ Grafana UP" || echo "❌ Grafana DOWN"
curl -s http://localhost:3100/ready > /dev/null && echo "✅ Loki UP" || echo "❌ Loki DOWN"

# Métriques
echo "🎯 Vérification métriques..."
curl -s http://localhost:8002/metrics | grep -q "django_" && echo "✅ Django métriques" || echo "❌ Django métriques"
curl -s http://localhost:8000/metrics | grep -q "fastapi_" && echo "✅ FastAPI métriques" || echo "❌ FastAPI métriques"

# Targets Prometheus
echo "🎯 Targets Prometheus..."
curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | "\(.labels.job): \(.health)"'

echo "✅ Validation terminée"
```