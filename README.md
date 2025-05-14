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
