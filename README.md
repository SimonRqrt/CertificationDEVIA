# Coach AI Running

## Objectif du projet
Ce dépôt fournit une plateforme complète d'analyse des performances sportives avec intelligence artificielle. L'objectif principal est de construire une chaîne cohérente allant de l'extraction des données Garmin jusqu'à la génération de plans d'entraînement personnalisés via un agent IA conversationnel, le tout exposé via des applications web modernes.

## Architecture fonctionnelle (5 couches principales)
Le projet est structuré en cinq domaines (dossiers racines) reflétant une séparation de responsabilités claire :

| Couche | Dossier | Rôle principal |
|--------|---------|----------------|
| Gestion des données | `E1_gestion_donnees` | Extraction Garmin, validation, transformation, stockage (PostgreSQL/SQLite), API REST. |
| Veille & Connecteurs | `E2_veille_IA` | Veille technologique, benchmark IA, intégrations externes. |
| Modèle IA & Agent | `E3_model_IA` | Agent conversationnel LangGraph, RAG, backends FastAPI/Django, modèles ML. |
| Applications & Interfaces | `E4_app_IA` | Applications Streamlit/Django, interfaces utilisateur, visualisations interactives. |
| Monitoring & Observabilité | `E5_monitoring` | Métriques Prometheus, logs structurés, alertes, dashboards de surveillance. |

Chaque dossier possède sa propre documentation détaillée pour favoriser l'évolutivité et l'onboarding.

## Documentation par domaine
Accéder aux points d'entrée de chaque couche :
- [README E1-gestion-donnees](E1_gestion_donnees/README.md) – Pipeline de données & API REST.
- [README E2-veille-IA](E2_veille_IA/README.md) – Veille technologique & connecteurs externes.
- [README E3-model-IA](E3_model_IA/docs/README.md) – Agent IA conversationnel & backends.
- [README E4-app-IA](E4_app_IA/docs/README.md) – Applications & interfaces utilisateur.
- [README E5-monitoring](E5_monitoring/docs/README.md) – Observabilité & monitoring.

## Composants clés
- **Pipeline de données Garmin** : `E1_gestion_donnees/scripts/run_pipeline.py`
- **API REST** : `E1_gestion_donnees/api_rest/main.py`
- **Agent IA conversationnel** : `E3_model_IA/scripts/advanced_agent.py`
- **Backend FastAPI** : `E3_model_IA/backend/fastapi_app/main.py`
- **Backend Django** : `E3_model_IA/backend/django_app/manage.py`
- **Interface Streamlit** : `E4_app_IA/frontend/streamlit_app/app_streamlit.py`
- **Métriques Prometheus** : `E5_monitoring/prometheus/`
- **Tests complets** : `tests/` (56 tests unitaires et d'intégration)

## Technologies & Stack Technique

### Backend & APIs
- **FastAPI** : API moderne asynchrone pour l'agent IA
- **Django REST Framework** : API robuste pour la gestion des données
- **PostgreSQL/SQLite** : Stockage des données d'entraînement
- **SQLAlchemy** : ORM pour l'interaction base de données

### Intelligence Artificielle
- **LangChain/LangGraph** : Framework pour l'agent conversationnel
- **OpenAI GPT** : Modèle de langage pour la génération de conseils
- **RAG (Retrieval Augmented Generation)** : Base de connaissances expertes
- **FAISS** : Recherche vectorielle pour la récupération de documents

### Frontend & Interfaces
- **Streamlit** : Interface interactive principale
- **Django Templates** : Interface web traditionnelle
- **Plotly/Matplotlib** : Visualisations des performances

### Monitoring & DevOps
- **Prometheus** : Métriques et monitoring
- **Docker** : Conteneurisation des services
- **GitHub Actions** : CI/CD automatisé (56 tests)
- **Pytest** : Suite de tests complète

## Fonctionnalités Principales

### Analyse de Performance
- Extraction automatique des données Garmin (activités, métriques)
- Calculs avancés : VMA, charge d'entraînement, prédictions
- Détection d'anomalies et données aberrantes

### Coach IA Conversationnel
- Agent conversationnel expert en course à pied
- Génération de plans d'entraînement personnalisés
- Conseils adaptatifs basés sur la forme et la fatigue
- Base de connaissances expertes intégrée

### Visualisations Interactives
- Tableaux de bord de performance
- Graphiques d'évolution temporelle
- Métriques de forme et recommandations

### APIs & Intégrations
- API REST complète pour l'accès aux données
- Intégration météo pour l'adaptation des séances
- Support multi-utilisateurs avec authentification

## Gestion des secrets
- Variables d'environnement dans `.env` (non commitées)
- Clés API Garmin et OpenAI sécurisées
- Configuration séparée pour développement/production

## Qualité & Tests (CI/CD)
- **56 tests** unitaires et d'intégration automatisés
- Pipeline CI/CD GitHub Actions opérationnel
- Couverture de code avec pytest-cov
- Linting automatique avec flake8
- Tests asynchrones pour l'agent IA

## Monitoring & Observabilité
- Métriques Prometheus pour tous les services
- Logs structurés avec niveaux appropriés
- Dashboards de surveillance des performances
- Alertes automatiques sur incidents

## Installation & Démarrage Rapide

### Prérequis
- Python 3.10+
- PostgreSQL (optionnel, SQLite par défaut)
- Compte Garmin Connect
- Clé API OpenAI

### Installation
```bash
# 1. Cloner le dépôt
git clone https://github.com/SimonRqrt/CertificationDEVIA.git
cd CertificationDEVIA

# 2. Installer les dépendances
pip install -e .[test]

# 3. Configuration environnement
cp .env.example .env
# Éditer .env avec vos clés API

# 4. Initialiser la base de données
python E1_gestion_donnees/scripts/init_db.py

# 5. Lancer les services
docker-compose -f deployment/docker-compose.yml up -d
```

### Démarrage des Applications
```bash
# Interface Streamlit (recommandée)
streamlit run E4_app_IA/frontend/streamlit_app/app_streamlit.py

# Backend FastAPI
uvicorn E3_model_IA.backend.fastapi_app.main:app --host 0.0.0.0 --port 8000

# Backend Django
python E3_model_IA/backend/django_app/manage.py runserver 8002
```

## Architecture Technique (flux de données)
```
[Garmin Connect] -> [E1 Pipeline] -> [PostgreSQL] -> [E3 Agent IA] -> [E4 Interface]
                          |              |              |              |
                    [Validation]   [Métriques E5]  [RAG/LLM]    [Visualisations]
                          |              |              |              |
                    [API REST E1] <- [Monitoring] <- [FastAPI] <- [Streamlit/Django]
```

## Sécurité & Conformité
- Isolation des secrets et clés API
- Authentification JWT pour les APIs
- Validation stricte des entrées utilisateur
- Logs de sécurité et audit trail

## Tests & Validation
```bash
# Lancer tous les tests
pytest

# Tests avec couverture
pytest --cov=E1_gestion_donnees --cov=E3_model_IA

# Tests spécifiques
pytest tests/test_e3_agent_ia.py -v
```

## Documentation Technique
- Architecture détaillée dans `docs/`
- Guides d'installation par composant
- Documentation API avec Swagger/ReDoc
- Exemples d'utilisation et tutoriels

## Roadmap & Évolutions
- [ ] Support multi-plateformes (Strava, Polar)
- [ ] Modèles ML prédictifs avancés
- [ ] Application mobile
- [ ] Intégration capteurs IoT

## Contribution
1. Fork du projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalité`)
3. Tests passants requis (`pytest`)
4. Commit avec messages conventionnels
5. Pull Request vers `develop`

## Licence
Voir le fichier `LICENSE` à la racine du projet.

## Révision
- **Version** : 2.0
- **Dernière mise à jour** : 2025-01-27
- **Pipeline CI** : ✅ Fonctionnel (56/56 tests)