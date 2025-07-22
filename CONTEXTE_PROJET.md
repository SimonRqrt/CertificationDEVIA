# 📋 Contexte du projet CertificationDEVIA

> **Fichier de mémorisation du contexte pour reprise de développement**

## 🎯 Vue d'ensemble du projet

**Projet** : Application de coaching sportif IA  
**Objectif** : Certification Développeur IA (Simplon)  
**Technologies** : Django + FastAPI + Streamlit + OpenAI + LangChain  
**Données** : API Garmin Connect + Base de connaissances sportive  

## 🏗️ Architecture finale

```
CertificationDEVIA/
├── E1_gestion_donnees/          # Bloc E1 - Extraction données Garmin
│   ├── data_manager.py          # Connexion API Garmin, traitement données
│   ├── db_manager.py            # Gestion SQLite/SQLAlchemy
│   └── scripts/                 # Scripts automatisation
├── E2_veille_IA/               # Bloc E2 - Veille technologique (À COMPLÉTER)
├── E3_model_IA/                # Bloc E3 - Modèles IA
│   ├── backend/
│   │   ├── django_app/         # 🔐 Application Django complète
│   │   │   ├── accounts/       # Auth JWT + User personnalisé
│   │   │   ├── activities/     # Modèles activités Garmin
│   │   │   ├── coaching/       # Modèles coaching IA
│   │   │   └── coach_ai_web/   # Settings Django
│   │   └── fastapi_app/        # 🤖 API FastAPI
│   │       ├── api_service.py  # Endpoints coaching IA
│   │       ├── django_auth_service.py # Service auth Django
│   │       └── fastapi_auth_middleware.py # Middleware JWT
│   └── scripts/                # Agent LangGraph + RAG
├── E4_app_IA/                  # Bloc E4 - Applications IA
│   └── frontend/streamlit_app/ # 💻 Interface utilisateur
├── E5_monitoring/              # Bloc E5 - Monitoring (À COMPLÉTER)
├── deployment/                 # 🐳 Configuration Docker + CI/CD
│   ├── docker-compose-new.yml
│   ├── django.Dockerfile
│   ├── fastapi.Dockerfile
│   └── ci_cd/
├── knowledge_base/             # Base connaissances sportive (markdown)
├── data/                       # Données partagées
└── ARCHITECTURE.md             # Documentation architecture
```

## ✅ Fonctionnalités implémentées

### 🔐 Authentification Django (E3)
- **User personnalisé** : Email + profil sportif (poids, taille, objectifs)
- **UserProfile** : Métriques performance (VMA, VO2max, zones FC)
- **JWT Authentication** : Access + refresh tokens avec blacklist
- **API REST** : `/api/v1/auth/` (register, login, profile, password)
- **Admin Django** : Interface administration complète
- **Swagger/OpenAPI** : Documentation auto-générée

### 🤖 IA et Coaching (E3)
- **Agent LangGraph** : Coaching conversationnel avec RAG
- **Base de connaissances** : Markdown (principes, séances, planification)
- **FastAPI intégré** : Authentification Django + contexte utilisateur
- **Sessions tracées** : Historique conversations dans Django
- **Endpoints** :
  - `/v1/coaching/chat` (avec auth JWT Django)
  - `/v1/coaching/chat-legacy` (avec clé API)

### 📊 Modèles de données (E1 + E3)
**Utilisateurs :**
- `User` : Authentification + profil sportif
- `UserProfile` : Métriques performance avancées

**Activités sportives :**
- `Activity` : Données complètes Garmin (FC, vitesse, GPS, etc.)
- `ActivitySplit` : Segments/splits d'activité
- `GPSPoint` : Points GPS détaillés

**Coaching :**
- `TrainingPlan` : Plans d'entraînement
- `WorkoutSession` : Séances planifiées/réalisées
- `CoachingSession` : Sessions IA avec contexte
- `PerformanceMetrics` : Métriques calculées
- `Goal` : Objectifs utilisateur

### 🐳 Déploiement (E4 + E5)
- **Docker Compose** : Services séparés
- **CI/CD GitHub Actions** : Build + tests + deploy
- **Scripts démarrage** : `start_services_new.py`
- **Tests intégration** : `test_integration.py`

## 🚀 Démarrage rapide

### Local (recommandé)
```bash
# Démarrage automatique
python3 start_services_new.py

# Ou manuel
cd E3_model_IA/backend/django_app && python3 manage.py runserver 8002
cd E3_model_IA/backend/fastapi_app && uvicorn api_service:app --port 8000
cd E4_app_IA/frontend/streamlit_app && streamlit run app_streamlit.py --server.port 8501
```

### Docker
```bash
cd deployment
docker-compose -f docker-compose-new.yml up --build
```

### URLs services
- **Django Admin** : http://localhost:8002/admin/
- **Django API** : http://localhost:8002/api/v1/
- **FastAPI Docs** : http://localhost:8000/docs
- **Streamlit UI** : http://localhost:8501/
- **Swagger API** : http://localhost:8002/swagger/

## 🧪 Tests et validation

### Tests d'intégration
```bash
python3 test_integration.py
```

### Workflow de test
1. **Santé services** : Django + FastAPI accessibles
2. **Auth Django** : Inscription + connexion JWT
3. **Intégration** : FastAPI avec auth Django
4. **Legacy** : Endpoint avec clé API

### Créer un utilisateur test
```bash
curl -X POST http://localhost:8002/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@coach-ai.com",
    "password": "secure123",
    "password_confirm": "secure123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

## 🔧 Configuration environnement

### Variables .env obligatoires
```bash
# API Keys
OPENAI_API_KEY=sk-...
GARMIN_EMAIL=your_email@example.com
GARMIN_PASSWORD=your_password
API_KEY=your_secure_api_key

# Django
SECRET_KEY=your_django_secret_key  # ✅ Configurée (22/01/2025)
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Base de données
DB_TYPE=sqlserver  # ✅ Azure SQL Server configuré
DB_NAME=garmin_data
DATABASE_URL=mssql+pyodbc://...
```

### 🩺 Diagnostic Claude Doctor (22/01/2025)
```bash
# État système vérifié
✅ Services Docker     : 3/3 healthy (19h uptime)
✅ Endpoints           : Tous accessibles (<50ms)
✅ Variables .env      : Toutes présentes
✅ SECRET_KEY Django   : Sécurisée (réparée)
✅ Configuration       : Propre et fonctionnelle
⚠️  Azure SQL Server  : Timeout (base suspendue)
```

## 📈 État par bloc de compétences

### ✅ E1 - Gestion des données (COMPLET)
- [x] Extraction API Garmin automatisée
- [x] Base de données SQLite + migrations
- [x] Requêtes SQL optimisées
- [x] API REST pour accès données
- [x] Scripts d'import fonctionnels

### ⚠️ E2 - Veille IA (À COMPLÉTER)
- [ ] Documentation veille technologique
- [ ] Benchmark services IA
- [ ] Synthèses accessibilité
- [ ] Sources fiables documentées

### ✅ E3 - Modèles IA (COMPLET)
- [x] API FastAPI sécurisée JWT
- [x] Agent LangGraph + RAG
- [x] Intégration Django auth
- [x] Tests automatisés
- [x] Documentation OpenAPI
- [x] Monitoring sessions

### ✅ E4 - Applications IA (COMPLET)
- [x] Interface Streamlit fonctionnelle
- [x] Architecture microservices
- [x] Authentification intégrée
- [x] CI/CD GitHub Actions
- [x] Tests d'intégration

### ⚠️ E5 - Monitoring (PARTIEL)
- [x] Logging configuré
- [x] Health checks Docker
- [ ] Métriques avancées
- [ ] Dashboard monitoring
- [ ] Alertes configurées

## 🎯 État développement actuel (Janvier 2025)

### ✅ Réalisations Session Docker Azure SQL (21/01/2025)
- [x] **Driver ODBC corrigé** : Configuration odbcinst.ini avec bon chemin driver
- [x] **FastAPI Azure SQL** : Connexion établie et fonctionnelle
- [x] **PROJECT_ROOT Django** : Adaptation Docker avec DOCKER_ENV=true
- [x] **Architecture 3 services** : Django + FastAPI + Streamlit opérationnels
- [x] **Variables .env** : Accès vérifié dans tous les containers
- [x] **Nettoyage fichiers** : docker-compose-new.yml → docker-compose.yml

### ✅ Corrections Sécurité (22/01/2025)
- [x] **SECRET_KEY Django** : Générée et configurée (remplace fallback)
- [x] **Diagnostic complet** : Claude Doctor - tous services healthy
- [x] **Performance validée** : Endpoints <50ms, logs propres
- [x] **Configuration stable** : 19h uptime sans erreur
- [x] **Documentation mise à jour** : CONTEXTE_PROJET.md + ARCHITECTURE.md

### 🔧 Architecture finale stabilisée
1. ✅ **Django** : Interface web + admin + SECRET_KEY sécurisée
2. ✅ **FastAPI** : API IA + Azure SQL Server + driver ODBC fonctionnel  
3. ✅ **Streamlit** : Interface conversationnelle + agent coaching
4. ✅ **Docker** : 3 services healthy + variables .env + réseau configuré
5. ✅ **Git** : Structure propre + commits documentés + roadmap évolution

### 🎯 Configuration ODBC fonctionnelle (backend.Dockerfile)
```dockerfile
# Configuration ODBC qui fonctionne
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18
```

### ✅ Status Final Containers Docker (22/01/2025 - 11h30)
- **Django** : ✅ UP (healthy) - Port 8002 accessible + SECRET_KEY sécurisée
- **FastAPI** : ✅ UP (healthy) - Port 8000 avec Azure SQL Server  
- **Streamlit** : ✅ UP (healthy) - Port 8501 interface utilisateur

### 🔐 Corrections Sécurité (22/01/2025)
- **SECRET_KEY Django** : ✅ Générée et configurée (remplace fallback non sécurisé)
- **Variables .env** : ✅ Toutes les variables critiques présentes et accessibles
- **Configuration Docker** : ✅ Rechargement complet des services réussi

### 🚀 Roadmap Évolution Interface Django

**Vision** : Interface complémentaire à l'échange conversationnel (Streamlit)

#### Phase 1 - Interface formulaire d'objectifs running
- **Concept** : Système de formulaires structurés pour objectifs sportifs
- **Fonctionnalités** :
  - Sélection guidée d'objectifs running (10K, semi-marathon, marathon, etc.)
  - Paramètres utilisateur (niveau, disponibilité, préférences)
  - Génération automatique de plans d'entraînement via agent IA
- **Avantage** : Création de plan sans prompter, interface plus accessible

#### Phase 2 - Pipeline Garmin Connect temporaire (RGPD-friendly)
- **Concept** : Récupération ponctuelle des données sans stockage
- **Fonctionnalités** :
  - Formulaire de connexion Garmin (identifiants temporaires)
  - Pipeline d'extraction en temps réel
  - **Aucun stockage permanent** des identifiants (conformité RGPD)
  - Analyse immédiate → Plan personnalisé → Suppression données sensibles

#### Architecture cible
```
┌─────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   Django Web    │    │   FastAPI IA    │    │   Streamlit      │
│   Interface     │◄──►│   Agent Coach   │◄──►│   Chat IA        │
│   Formulaires   │    │   + RAG         │    │   Conversationnel│
└─────────────────┘    └─────────────────┘    └──────────────────┘
         │                       │                       
         ▼                       ▼                       
┌─────────────────┐    ┌─────────────────┐              
│   Garmin API    │    │   Azure SQL     │              
│   (temporaire)  │    │   Server        │              
└─────────────────┘    └─────────────────┘              
```

**Complémentarité des interfaces** :
- **Django** : Approche guidée, formulaires, plans structurés
- **Streamlit** : Échange libre, conseils personnalisés, coaching conversationnel

## 🎯 Prochaines étapes prioritaires

### 1. Compléter déploiement Docker (URGENT)
- [x] Diagnostiquer erreur FastAPI container
- [x] Ajouter PyJWT aux requirements
- [ ] Rebuild et redéployer container FastAPI
- [ ] Valider communication complète Django ↔ FastAPI ↔ Streamlit

### 2. Compléter E2 (Veille IA)
- [ ] Rédiger documentation veille technologique
- [ ] Créer benchmark OpenAI vs alternatives
- [ ] Documenter critères accessibilité

### 3. Finaliser E5 (Monitoring)
- [ ] Implémenter métriques Prometheus
- [ ] Dashboard Grafana ou équivalent
- [ ] Configuration alertes

### 4. Optimisations
- [ ] Tests unitaires complets
- [ ] Documentation RGPD
- [ ] Extraction multi-source (E1)
- [ ] Performance optimizations

## 💾 État Git

**Branche actuelle** : `developp`  
**Dernier commit** : `38dabee` - Refactorisation architecture  
**Status** : Clean, prêt pour développement  

### Commandes Git utiles
```bash
git status
git log --oneline -10
git diff HEAD~1  # Voir derniers changements
```

## 🔍 Points d'attention

### Dépendances critiques
- **OpenAI API** : Clé valide nécessaire
- **Garmin Connect** : Credentials utilisateur requis
- **Django migrations** : Toujours appliquer après pull

### Troubleshooting fréquent
1. **Port occupé** : Vérifier services en cours
2. **Import Django** : PYTHONPATH et répertoire de travail
3. **JWT invalide** : Régénérer tokens auth
4. **Docker fails** : Vérifier .env et volumes

## 📚 Documentation

- **ARCHITECTURE.md** : Architecture détaillée
- **param/grille.md** : Grille d'évaluation certification
- **param/mission.md** : Brief projet
- **README.md** : Vue d'ensemble projet

---

> **Note** : Ce fichier sert de mémoire contextuelle pour reprendre le développement. Maintenir à jour après changements majeurs.