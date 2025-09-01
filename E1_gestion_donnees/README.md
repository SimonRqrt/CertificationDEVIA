# E1 - Gestion des Données Garmin

> **Critères certification** : C1-C8 (Pipeline ETL, API REST, Base de données)

## Vue d'ensemble
Module de gestion complète des données sportives Garmin avec pipeline ETL, API REST sécurisée et persistance PostgreSQL/SQLite.

## Architecture Technique

### Services Déployés
- **API REST E1** (port 8001) : FastAPI pour données et authentification
- **PostgreSQL** (port 5432) : Base de données principale
- **Pipeline ETL** : Extraction/Transformation Garmin automatisée

### Composants Principaux

#### 1. Pipeline ETL Garmin
- **Fichier** : `scripts/run_pipeline.py`
- **Source** : Garmin Connect API
- **Transformation** : Validation, calculs métriques (VMA, charge)
- **Destination** : PostgreSQL avec fallback SQLite

#### 2. API REST Sécurisée
- **Fichier** : `api_rest/main.py`
- **Authentification** : JWT + X-API-Key
- **Rate limiting** : Protection OWASP
- **Documentation** : OpenAPI/Swagger sur `/docs`

#### 3. Gestionnaire Base de Données
- **Fichier** : `db_manager.py`
- **ORM** : SQLAlchemy avec modèles typés
- **Fallback** : SQLite si PostgreSQL indisponible
- **Pool** : Connexions optimisées

### Endpoints Disponibles

#### Authentification
```bash
POST /auth/login        # Connexion utilisateur
POST /auth/register     # Inscription
POST /auth/refresh      # Renouvellement token
```

#### Utilisateurs
```bash
GET  /users/me          # Profil utilisateur
PUT  /users/me          # Mise à jour profil
POST /users/            # Création utilisateur
```

#### Activités Sportives
```bash
GET  /activities/       # Liste activités paginée
GET  /activities/{id}   # Détail activité
POST /activities/sync   # Synchronisation Garmin
DELETE /activities/{id} # Suppression activité
```

#### Santé Système
```bash
GET /health            # Status API et base de données
```

## Base de Données

### Modèles Principaux
- **Users** : Profils utilisateurs avec authentification
- **Activities** : Activités sportives Garmin complètes
- **Metrics** : Métriques calculées (VMA, seuils, charge)

### Schema Relationnel
Voir documentation détaillée : [`docs/modelisation_merise.md`](docs/modelisation_merise.md)

## Pipeline de Données

### Étapes ETL
1. **Extract** : Connexion Garmin Connect via API
2. **Transform** : 
   - Validation données (format, cohérence)
   - Calculs métriques avancés
   - Détection anomalies
3. **Load** : Persistance PostgreSQL avec gestion erreurs

### Scripts Disponibles
- `scripts/fetch_garmin.py` : Extraction données Garmin
- `scripts/run_pipeline.py` : Pipeline ETL complet
- `scripts/insert_user.py` : Création utilisateur
- `scripts/attach_user.py` : Association données-utilisateur
- `scripts/export_db.py` : Export données (backup)

## Sécurité et Conformité

### RGPD
- **Documentation** : `rgpd/registre_traitements_donnees.md`
- **Procédures** : `rgpd/procedures_tri_donnees.md`
- **Scripts cleanup** : `rgpd/scripts/cleanup_*.py`

### Authentification
- JWT avec refresh tokens
- Hash sécurisé des mots de passe (bcrypt)
- Rate limiting anti-brute force
- Validation entrées stricte

## Démarrage et Tests

### Installation
```bash
# Dépendances
pip install -r api_rest/requirements.txt

# Base de données
python init_db.py

# Démarrage API
python api_rest/main.py
```

### Tests
```bash
# Tests API
pytest ../tests/test_e1_api_rest.py -v

# Tests pipeline
pytest ../tests/test_e1_pipeline.py -v

# Test validation
./api_rest/demo.sh
```

### Configuration Environnement
```bash
# Variables requises (.env)
DB_TYPE=postgresql
DB_HOST=localhost
DB_NAME=coach_ia_db
DB_USER=coach_user
DB_PASSWORD=coach_password
GARMIN_EMAIL=your@email.com
GARMIN_PASSWORD=your_password
JWT_SECRET=your-secret-key
```

## Monitoring et Logs

### Métriques Surveillées
- Nombre d'activités synchronisées
- Temps de réponse API (< 200ms)
- Taux d'erreur pipeline (< 5%)
- Connexions base de données

### Logs Structurés
- `data/logs/` : Logs pipeline ETL
- Rotation automatique des logs
- Niveau configurable (INFO, DEBUG, ERROR)

## Documentation Technique

### Fichiers Importants
- [`api_rest/main.py`](api_rest/main.py) : API REST FastAPI
- [`data_manager.py`](data_manager.py) : Logique métier ETL
- [`db_manager.py`](db_manager.py) : Gestionnaire base données
- [`api_rest/utils/models.py`](api_rest/utils/models.py) : Modèles SQLAlchemy
- [`api_rest/utils/auth.py`](api_rest/utils/auth.py) : Authentification JWT
- [`scripts/run_pipeline.py`](scripts/run_pipeline.py) : Orchestrateur ETL

### Tests et Validation
- [`api_rest/PIPELINE_TEST.md`](api_rest/PIPELINE_TEST.md) : Guide tests pipeline
- [`api_rest/test_simple.py`](api_rest/test_simple.py) : Tests unitaires API
- [`api_rest/demo.sh`](api_rest/demo.sh) : Script démonstration

### Conformité
- [`docs/modelisation_merise.md`](docs/modelisation_merise.md) : Modélisation Merise
- [`rgpd/`](rgpd/) : Documentation et scripts RGPD

## Intégrations

### Avec E3 (Modèle IA)
- Exposition des métriques utilisateur via API
- Données enrichies pour l'agent IA
- Format JSON standardisé

### Avec E5 (Monitoring)
- Endpoint `/health` pour supervision
- Métriques Prometheus disponibles
- Logs structurés pour alerting

---

*Module E1 - Pipeline de données et API REST sécurisée*