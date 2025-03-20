# Projet de Recommandation sportive personnalisée

## Contexte et Objectifs
Le projet prend en compte la grille d'evaluation comme objectif, le projet ne peut pas être fini tant que tous les points ne sont pas cochés.
Pendant le développement du projet, si un point qui n'était pas coché est réalisé, alors il faut cocher le point en question en transformant '[ ]' en '[X]'.

L'objectif global du projet est de récupérer des données d'objets sportifs connectés comme Garmin ou Strava, puis de les stocker en BDD pour pouvoir les exploiter. Ces données seront utilisés afin de proposer à l'aide d'un service d'IA un programme d'entrainement personnalisé en fonction des données présentes et des objectifs. Afin d'exploiter ces données, un LLM enrichi d'un RAG ou d'agents ciblant des sites spécialisés et définis seront déployés pour donner un programme le plus cohérent possible et éviter les hallucinations. La récupération des données devra dans un premier temps s'appuyer sur des données d'un utilisateur test, puis trouver par la suite un système pour que chaque utilisateur puisse accéder à ce service en rentrant ses identifiants Garmin ou Strava sur un site Django afin d'accéder à ses données et de pouvoir les exploiter.

## Architecture Technique

### Technologies Principales
- Python pour le développement du projet.
- LLM : pour la génération du programme d'entrainement personnalisé.
- Agent IA (ou RAG): pour enrichir le LLM avec des sites spécialisés dans le sport recherché, et respecter des questions légales afin de ne pas stocker localement les données enrichies via d'autres sites.
- Docker pour la conteneurisation.
- FastAPI pour l'API REST.
- PostgreSQL ou MySQL pour la base de données.
- GitLab CI/CD pour l'intégration et le déploiement continu.
- Prometheus et Grafana pour le monitoring.

### Sources de Données
1. Données :
   - Format actuel : data/garmin_data.db
   - Contient les données des activités Garmin (une ligne par activité)
   - Analyser si possibilité d'avoir plusieurs instances pour rechercher les données gps par exemple

## Plan de Développement

### Phase 1 : Préparation et Architecture (E1)
1. Documentation initiale :
   - Spécifications techniques détaillées
   - Modélisation Merise de la base de données
   - Documentation RGPD
   - Diagrammes de flux de données

2. Mise en place de l'environnement :
   - Configuration Git et GitLab
   - Création des conteneurs Docker
   - Configuration de l'environnement Python

3. Développement du système de données :
   - Création de la base PostgreSQL
   - Scripts ETL pour l'import des données Excel
   - Mise en place des requêtes SQL d'agrégation
   - Développement de l'API REST pour l'accès aux données

### Phase 2 : Intelligence Artificielle (E2)
1. Veille technologique :
   - Mise en place d'un système de veille sur les LLMs et agents IA
   - Documentation des choix technologiques
   - Benchmark des solutions d'IA

2. Intégration IA :
   - Configuration du LLM choisi
   - Mise en place de l'agent LangChain
   - Développement des prompts et des tools

### Phase 3 : API et Services IA (E3)
1. Développement API :
   - Création de l'API REST avec FastAPI
   - Implémentation de l'authentification
   - Documentation OpenAPI
   - Tests automatisés

2. Intégration des services :
   - Configuration des endpoints IA
   - Mise en place du monitoring
   - Tests d'intégration

### Phase 4 : Application Principale (E4)
1. Développement core :
   - Création du service de génération de rapports
   - Intégration avec l'API IA
   - Système d'envoi de mails
   - Interface utilisateur web (si nécessaire)

2. Tests et Qualité :
   - Tests unitaires
   - Tests d'intégration
   - Tests de performance
   - Validation RGPD

### Phase 5 : Monitoring et Maintenance (E5)
1. Mise en place du monitoring :
   - Configuration Prometheus
   - Tableaux de bord Grafana
   - Alerting

2. Documentation opérationnelle :
   - Procédures de déploiement
   - Guide de maintenance
   - Procédures de debug

## Infrastructure et Déploiement

### Docker
- Conteneur PostgreSQL
- Conteneur Application Python
- Conteneur API
- Conteneur LLM
- Conteneur Monitoring

### CI/CD
1. Pipeline de test :
   - Linting
   - Tests unitaires
   - Tests d'intégration
   - Analyse de sécurité

2. Pipeline de déploiement :
   - Build des images Docker
   - Tests de déploiement
   - Déploiement en production

### Sécurité
- Authentification API
- Chiffrement des données
- Conformité RGPD
- Gestion des secrets

## Livrables Attendus

### Documentation
- Documentation technique complète
- Documentation utilisateur
- Documentation d'API (OpenAPI)
- Registre RGPD
- Rapports de tests

### Code Source
- Scripts Python
- Configuration Docker
- Scripts CI/CD
- Tests automatisés
- Configuration monitoring

### Base de Données
- Schéma SQL
- Scripts de migration
- Procédures de sauvegarde
- Documentation RGPD