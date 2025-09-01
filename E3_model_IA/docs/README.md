# E3 - Modèle IA Coach AI

> **Critère certification** : C11 (Monitoring modèle IA)

## Vue d'ensemble
Architecture complète du modèle d'IA Coach AI avec agent conversationnel, base de connaissances RAG et API sécurisée.

## Architecture Technique

### Services Déployés
- **FastAPI** (port 8000) : API IA principale avec agent Coach
- **Django** (port 8002) : Interface web administrative  
- **Agent IA** : LangChain + OpenAI GPT-4 avec base de connaissances

### Composants Principaux

#### 1. Agent IA Conversationnel
- **Fichier** : `scripts/advanced_agent.py`
- **Modèle** : OpenAI GPT-4 
- **Base de connaissances** : RAG avec documents Markdown
- **Contexte** : Running, entraînement, nutrition

#### 2. API REST Sécurisée  
- **Endpoint principal** : `/v1/coaching/`
- **Authentification** : X-API-Key + JWT
- **Rate limiting** : 100 req/min par IP
- **Documentation** : OpenAPI/Swagger sur `/docs`

#### 3. Base de Connaissances RAG
- **Dossier** : `knowledge_base/`
- **Format** : Markdown structuré
- **Catégories** : Principes, séances, planification
- **Recherche** : Similarité vectorielle

### Endpoints Disponibles

#### Coaching IA
```bash
POST /v1/coaching/chat-legacy
POST /v1/coaching/generate-training-plan
GET  /v1/coaching/plans/{user_id}
```

#### Données Utilisateur
```bash
GET /v1/activities/{user_id}
GET /v1/stats/{user_id} 
GET /v1/database/status
```

#### Monitoring
```bash
GET /metrics        # Métriques Prometheus
GET /health         # Status système
```

## Utilisation

### Démarrage avec Docker
```bash
cd deployment
export OPENAI_API_KEY="your-key-here"
docker compose up -d fastapi django
```

### Test Chat IA
```bash
curl -X POST http://localhost:8000/v1/coaching/chat-legacy \
  -H "X-API-Key: coach_ai_secure_key_2025" \
  -H "Content-Type: application/json" \
  -d '{"message": "Comment améliorer ma VMA?", "user_id": 2}'
```

### Test Génération Plan
```bash
curl -X POST http://localhost:8000/v1/coaching/generate-training-plan \
  -H "X-API-Key: coach_ai_secure_key_2025" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 2,
    "level": "intermediate", 
    "sessions_per_week": 3,
    "goal": "10k",
    "duration_weeks": 8
  }'
```

## Métriques IA Surveillées

### Performance
- `training_plans_generated_total` : Plans générés
- `process_cpu_seconds_total` : CPU FastAPI
- `process_resident_memory_bytes` : Mémoire utilisée

### Qualité
- Temps de réponse moyen < 5s
- Taux de réussite > 95%
- Disponibilité 24/7

## Documentation Technique

### Architecture
- Modèle conversationnel avec mémoire de session
- Pipeline RAG optimisé pour le running
- API RESTful avec authentification robuste

### Sécurité  
- Authentification par clé API
- Validation des entrées utilisateur
- Logging de sécurité complet
- Rate limiting et protection DDoS

### Monitoring
- Métriques Prometheus intégrées
- Alerting sur performances critiques
- Dashboard Grafana temps réel

## Fichiers Importants
- `backend/fastapi_app/main.py` : Application FastAPI principale
- `backend/django_app/` : Interface web administrative  
- `knowledge_base/` : Base de connaissances RAG
- `scripts/advanced_agent.py` : Agent IA conversationnel