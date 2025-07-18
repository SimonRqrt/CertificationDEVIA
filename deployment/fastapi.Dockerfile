FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Répertoire de travail
WORKDIR /app

# Installer les dépendances système
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements FastAPI
COPY E3_model_IA/backend/fastapi_app/requirements-fastapi.txt /app/requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY E3_model_IA/ /app/E3_model_IA/
COPY E1_gestion_donnees/ /app/E1_gestion_donnees/
COPY src/ /app/src/
COPY knowledge_base/ /app/knowledge_base/
COPY data/ /app/data/

# Définir le PYTHONPATH
ENV PYTHONPATH="/app:/app/E3_model_IA/backend/fastapi_app"

# Exposer le port
EXPOSE 8000

# Commande de démarrage
WORKDIR /app/E3_model_IA/backend/fastapi_app
CMD ["uvicorn", "api_service:app", "--host", "0.0.0.0", "--port", "8000"]