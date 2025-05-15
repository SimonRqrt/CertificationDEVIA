# CertificationDEVIA

# Projet d'Extraction et d'Analyse des Données Sportives

## Contexte
Le projet consiste à automatiser l'extraction des données provenant de différentes sources (API Garmin, fichiers CSV et JSON, bases de données) afin de permettre une analyse des performances sportives d'utilisateurs.

### Acteurs
- **Développeur principal** : Simon
- **Utilisateurs cibles** : Sportifs amateurs et professionnels souhaitant suivre leurs performances sur plusieurs plateformes (Garmin, Strava, etc.)

### Objectifs fonctionnels
- Récupérer les données d’activités sportives à partir de diverses sources.
- Stocker ces données dans une base de données centralisée.
- Fournir une API pour accéder à ces données.

### Objectifs techniques
- Langage : Python
- Technologies : API Garmin, SQLAlchemy pour l'accès à la base de données, Pandas pour l'analyse des données.
- Base de données : SQLite pour la phase initiale, avec un potentiel d'évolution vers un SGBD plus robuste (PostgreSQL).

### Contraintes techniques
- Accès aux API de Garmin et autres services.
- Traitement et stockage des données en conformité avec les normes RGPD.

# Spécifications Techniques

## Technologies et Outils
- **Langage** : Python 3.9
- **Bibliothèques** :
  - `requests` pour les appels API
  - `pandas` pour l'analyse et la manipulation des données
  - `SQLAlchemy` pour l'interaction avec la base de données
- **API externes** :
  - **Garmin API** pour la récupération des données d'activités
  - **Strava API** pour récupérer des informations sur les activités sportives

## Exigences de Programmation
- **Modularité** : Le code sera structuré en modules pour faciliter l'extension et la maintenance.
- **Gestion des erreurs** : Le code inclura des blocs `try-except` pour gérer les erreurs d'API et de connexion à la base de données.
- **Versionnement** : Utilisation de **Git** pour gérer le versionnement et assurer une bonne traçabilité des modifications.

## Accessibilité et Disponibilité
- Les services externes doivent être disponibles pour permettre l'extraction des données.
- Un mécanisme de gestion des erreurs sera mis en place pour garantir la robustesse du système.
