# Documentation CI/CD - Coach AI

## Vue d'ensemble

Ce projet utilise GitHub Actions pour automatiser la livraison continue du modèle d'intelligence artificielle Coach AI. Le pipeline valide automatiquement les données, teste le modèle IA et assure la qualité du code avant déploiement.

## Architecture des pipelines

### 1. Pipeline principal - build.yml
**Déclencheurs :**
- Push sur branches : main, develop, test-pipeline, test-*
- Pull requests vers main ou develop  
- Exécution manuelle (workflow_dispatch)

**Étapes :**
1. **Setup environnement** : Python 3.10, cache pip
2. **Installation dépendances** : requirements.txt + outils dev
3. **Contrôle qualité code** : flake8 linting
4. **Validation données** : test data/sample_garmin_activities.json
5. **Tests modèle IA** : tests/test_e3_api_ia.py avec mocks
6. **Validation RAG** : vérification base connaissances (10+ fichiers MD)
7. **Tests couverture** : pytest avec rapport XML/terme
8. **Upload Codecov** : envoi métriques couverture

### 2. Pipeline déploiement - cd.yml
**Déclencheurs :**
- Push sur branche developp uniquement

**Étapes :**
- Build Docker local (simulation)
- Pas de déploiement réel configuré

### 3. Pipeline legacy - deploy.yml
**Déclencheurs :**
- Push sur main ou developp
- Pull requests

**Étapes :**
- Tests basiques Python
- Linting flake8 minimal

## Procédures d'installation

### Prérequis
- Compte GitHub avec Actions activé
- Secrets configurés dans Settings > Secrets :
  - `OPENAI_API_KEY` : Clé API OpenAI pour tests IA
  - `CODECOV_TOKEN` : Token pour upload couverture (optionnel)

### Configuration locale
```bash
# Cloner le dépôt
git clone https://github.com/SimonRqrt/CertificationDEVIA.git
cd CertificationDEVIA

# Installer dépendances
pip install -r requirements.txt
pip install flake8 pytest-cov

# Variables d'environnement pour tests
export OPENAI_API_KEY="sk-your-key"
export API_KEY="coach_ai_secure_key_2025"
```

### Tests locaux avant push
```bash
# Validation qualité données
python -c "import json; data=json.load(open('data/sample_garmin_activities.json')); print(f'OK: {len(data)} activités')"

# Tests modèle IA
pytest tests/test_e3_api_ia.py -v

# Linting
flake8 .

# Couverture complète
pytest --cov=. --cov-report=term
```

## Utilisation des pipelines

### Déclenchement automatique
- **Push code** : Pipeline build.yml se lance automatiquement
- **Pull Request** : Validation automatique avant merge
- **Merge develop** : Pipeline cd.yml + build.yml

### Déclenchement manuel
1. Aller sur Actions > CI Build & Test
2. Cliquer "Run workflow"
3. Choisir la branche
4. Cliquer "Run workflow"

### Lecture des résultats
- **Vert** : Tous tests passés, code déployable
- **Rouge** : Échec - voir logs détaillés
- **Jaune** : En cours d'exécution

## Débogage des échecs

### Échecs courants

**1. Tests données échouent**
```
AssertionError: Structure donnees invalide
```
**Solution :** Vérifier format JSON data/sample_garmin_activities.json

**2. Tests IA échouent**
```
ImportError: No module named 'openai'
```
**Solution :** Vérifier OPENAI_API_KEY dans Secrets GitHub

**3. Linting échoue**
```
flake8: E501 line too long
```
**Solution :** Corriger style code selon PEP8

**4. Couverture insuffisante**
```
Coverage below threshold
```
**Solution :** Ajouter tests manquants

### Logs détaillés
1. Actions > Workflow échoué
2. Cliquer sur job rouge
3. Dérouler l'étape qui échoue
4. Copier logs pour debug local

## Évolution et maintenance

### Ajout nouveaux tests
1. Créer test dans `tests/`
2. Mettre à jour pipeline si besoin
3. Tester localement
4. Push et vérifier Actions

### Modification pipeline
1. Éditer `.github/workflows/*.yml`
2. Commit avec message explicite
3. Vérifier exécution immédiate
4. Rollback si échec

### Nouveaux secrets
1. Settings > Secrets and variables > Actions
2. New repository secret
3. Utiliser dans workflow : `${{ secrets.SECRET_NAME }}`

## Métriques et monitoring

### Historique exécutions
- Actions > All workflows
- Filtrer par branche/statut
- Statistiques temps d'exécution

### Couverture de code
- Codecov dashboard (si configuré)
- Rapport local : `htmlcov/index.html`

### Alertes échecs
- Notifications GitHub automatiques
- Email configurable dans Settings

---

*Documentation conforme aux recommandations d'accessibilité WCAG 2.1*