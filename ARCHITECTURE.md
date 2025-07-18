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

## 🔄 Migration depuis l'ancienne architecture

Les anciens scripts restent fonctionnels pour la compatibilité :
- `start_services.py` (ancienne version)
- `test_integration.py` (mis à jour)

La nouvelle architecture est dans :
- `start_services_new.py` (nouvelle version)
- `deployment/docker-compose-new.yml` (nouvelle version)

## 📚 Documentation

- **Architecture** : Ce fichier
- **API Django** : http://localhost:8002/swagger/
- **API FastAPI** : http://localhost:8000/docs
- **Grille d'évaluation** : `param/grille.md`
- **Mission** : `param/mission.md`