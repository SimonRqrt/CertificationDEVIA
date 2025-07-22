# Architecture du projet CertificationDEVIA

## 🏗️ Structure du projet

```
CertificationDEVIA/
├── E1_gestion_donnees/          # Bloc E1 - Gestion des données
│   ├── data_manager.py          # Extraction données Garmin
│   ├── db_manager.py            # Gestion base de données
│   └── scripts/                 # Scripts d'automatisation
├── E2_veille_IA/               # Bloc E2 - Veille technologique
├── E3_model_IA/                # Bloc E3 - Modèles IA
│   ├── backend/
│   │   ├── django_app/         # Application Django
│   │   │   ├── coach_ai_web/   # Settings Django
│   │   │   ├── accounts/       # Gestion utilisateurs
│   │   │   ├── activities/     # Modèles activités
│   │   │   ├── coaching/       # Modèles coaching
│   │   │   └── core/           # Fonctionnalités core
│   │   └── fastapi_app/        # Application FastAPI
│   │       ├── api_service.py  # API principale
│   │       └── auth_middleware.py # Authentification
│   ├── scripts/                # Scripts IA
│   └── shared/                 # Code partagé
├── E4_app_IA/                  # Bloc E4 - Applications IA
│   ├── frontend/
│   │   └── streamlit_app/      # Interface utilisateur
│   └── tests/                  # Tests E4
├── E5_monitoring/              # Bloc E5 - Monitoring
├── deployment/                 # Configuration déploiement
│   ├── docker-compose-new.yml  # Orchestration Docker
│   ├── django.Dockerfile       # Image Django
│   ├── fastapi.Dockerfile      # Image FastAPI
│   └── streamlit.Dockerfile    # Image Streamlit
├── shared/                     # Utilitaires communs
└── data/                       # Données partagées
```

## 🚀 Démarrage des services

### Option 1 : Script automatique
```bash
python3 start_services_new.py
```

### Option 2 : Démarrage manuel
```bash
# Terminal 1 - Django
cd E3_model_IA/backend/django_app
python3 manage.py runserver 8002

# Terminal 2 - FastAPI
cd E3_model_IA/backend/fastapi_app
uvicorn api_service:app --host 0.0.0.0 --port 8000

# Terminal 3 - Streamlit
cd E4_app_IA/frontend/streamlit_app
streamlit run app_streamlit.py --server.port 8501
```

### Option 3 : Docker Compose
```bash
cd deployment
docker-compose -f docker-compose-new.yml up --build
```

## 🔗 URLs des services

- **Django Admin** : http://localhost:8002/admin/
- **Django API** : http://localhost:8002/api/v1/
- **FastAPI Docs** : http://localhost:8000/docs
- **Streamlit UI** : http://localhost:8501/
- **API Documentation** : http://localhost:8002/swagger/

## 🔧 Configuration

### Variables d'environnement (.env)
```bash
# Base de données
DB_TYPE=sqlite
DB_NAME=django_garmin_data

# API Keys
OPENAI_API_KEY=your_openai_key
GARMIN_EMAIL=your_garmin_email
GARMIN_PASSWORD=your_garmin_password
API_KEY=your_api_key

# Django
SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

## 📦 Dépendances par service

### Django (`E3_model_IA/backend/django_app/requirements-django.txt`)
- Django 4.2.7
- Django REST Framework
- JWT Authentication
- Swagger/OpenAPI

### FastAPI (`E3_model_IA/backend/fastapi_app/requirements-fastapi.txt`)
- FastAPI
- LangChain
- OpenAI
- Pydantic

### Streamlit (`E4_app_IA/frontend/streamlit_app/requirements-streamlit.txt`)
- Streamlit
- Pandas
- Folium

## 🧪 Tests

### Tests d'intégration
```bash
python3 test_integration.py
```

### Tests unitaires
```bash
# Django
cd E3_model_IA/backend/django_app
python3 manage.py test

# FastAPI
cd E3_model_IA/backend/fastapi_app
pytest
```

## 🎯 Avantages de cette architecture

1. **Séparation claire** des responsabilités
2. **Déploiement indépendant** des services
3. **Scalabilité** horizontale possible
4. **Maintenance** facilitée
5. **Respect des blocs** de compétences
6. **Tests isolés** par technologie
7. **Configuration centralisée**

## 🚀 Évolution Architecture - Interfaces Spécialisées

### Vision : Deux interfaces complémentaires

#### Interface Django - Approche Structurée
**Objectif** : Interface formulaires pour génération automatique de plans d'entraînement

**Fonctionnalités prévues :**
- Formulaires multi-étapes d'objectifs running (distance, niveau, disponibilité)
- Intégration avec l'agent IA FastAPI pour génération automatique
- Interface utilisateur guidée sans besoin de prompter
- Gestion des profils utilisateur avec métriques de performance

**Architecture technique :**
```python
# Exemple de flux prévu
def generate_training_plan(request):
    # 1. Récupération des paramètres formulaire
    user_data = extract_form_data(request)
    
    # 2. Appel à l'agent IA FastAPI
    plan = call_fastapi_agent(user_data)
    
    # 3. Sauvegarde et présentation
    save_training_plan(plan)
    return render_plan_template(plan)
```

#### Pipeline Garmin Temporaire (Phase 2)
**Conformité RGPD** : Aucun stockage permanent des identifiants

**Flux technique prévu :**
```python
# Exemple de pipeline temporaire
def fetch_garmin_realtime(credentials):
    # 1. Connexion temporaire (en mémoire uniquement)
    session = create_temp_garmin_session(credentials)
    
    # 2. Extraction données récentes
    activities = fetch_recent_activities(session)
    
    # 3. Analyse immédiate
    analysis = analyze_with_ai_agent(activities)
    
    # 4. Nettoyage sécurisé
    del session, credentials  # Suppression immédiate
    
    return analysis
```

### Complémentarité des interfaces

| Aspect | Django Interface | Streamlit Chat |
|--------|------------------|----------------|
| **Usage** | Plans structurés | Coaching conversationnel |
| **Utilisateur** | Débutant/guidé | Expérimenté/libre |
| **Interaction** | Formulaires | Prompt naturel |
| **Résultat** | Plan formaté | Conseils personnalisés |

## 🔄 État Actuel vs Évolution

### ✅ Configuration Actuelle (Janvier 2025)
- Architecture microservices stabilisée
- Docker Azure SQL Server fonctionnel (driver ODBC corrigé)
- Services Django + FastAPI + Streamlit opérationnels (3/3 healthy)
- Variables d'environnement sécurisées + SECRET_KEY Django configurée
- Performance validée : tous endpoints <50ms
- Diagnostic système : Claude Doctor - état excellent

### 🔧 Corrections Techniques Récentes

#### Driver ODBC SQL Server (21/01/2025)
```dockerfile
# Configuration odbcinst.ini corrigée
RUN echo '[ODBC Driver 18 for SQL Server]' > /etc/odbcinst.ini \
    && echo 'Driver=/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.5.so.1.1' >> /etc/odbcinst.ini
```

#### PROJECT_ROOT Django (21/01/2025)
```python
# Adaptation Docker dans settings.py
if os.getenv('DOCKER_ENV'):
    PROJECT_ROOT = Path('/app')  # Contexte Docker
else:
    PROJECT_ROOT = BASE_DIR.parent.parent.parent  # Contexte local
```

#### SECRET_KEY Django (22/01/2025)
```python
# Génération sécurisée et configuration .env
from django.core.management.utils import get_random_secret_key
SECRET_KEY=get_random_secret_key()  # Ajoutée au .env
```

## 📚 Documentation

- **Architecture** : Ce fichier
- **API Django** : http://localhost:8002/swagger/
- **API FastAPI** : http://localhost:8000/docs
- **Grille d'évaluation** : `param/grille.md`
- **Mission** : `param/mission.md`
- **Rappel du contexte** : CONTEXTE_PROJET.md