# Utiliser une image Python officielle et légère
FROM python:3.11-slim

# Définir le répertoire de travail dans le conteneur

WORKDIR /app

# Définir des variables d'environnement pour Python

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Installer les dépendances système si nécessaire (ex: pour la compilation de certaines libs)

# RUN apt-get update && apt-get install -y build-essential

# Copier d'abord le fichier des dépendances pour profiter du cache Docker

COPY requirements.txt .

# Installer les dépendances Python

# L'option --no-cache-dir réduit la taille de l'image

RUN apt-get update && apt-get install -y libmagic1 && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install "unstructured"


# Copier tout le reste du code du projet dans le conteneur

COPY . .

# Exposer le port sur lequel l'API va tourner

EXPOSE 8000

# La commande pour démarrer le serveur FastAPI à l'intérieur du conteneur

# On utilise le module E3\_model\_IA.api\_service et l'objet 'app' qu'il contient

CMD ["uvicorn", "E3_model_IA.api_service:app", "--host", "0.0.0.0", "--port", "8000"]