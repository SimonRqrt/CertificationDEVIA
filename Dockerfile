# Utiliser une image Python comme base
FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY . /app

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port de l'API
EXPOSE 8000

# Commande par défaut pour démarrer l'application
CMD ["python", "E1_gestion_donnees/scripts/run_pipeline.py"]