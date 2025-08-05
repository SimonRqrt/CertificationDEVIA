FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=coach_ai_web.settings

# Répertoire de travail
WORKDIR /app

# Installer les dépendances système avec PostgreSQL
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libpq-dev \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements Django
COPY E1_gestion_donnees/api_rest/requirements-django.txt /app/requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copier le code Django
COPY E1_gestion_donnees/api_rest/ /app/
COPY data/ /app/data/

# Créer les répertoires nécessaires
RUN mkdir -p /app/logs /app/static /app/media

# Collecter les fichiers statiques et créer les migrations
RUN python manage.py collectstatic --noinput \
    && python manage.py makemigrations

# Exposer le port
EXPOSE 8002

# Commande de démarrage
CMD ["python", "manage.py", "runserver", "0.0.0.0:8002"]