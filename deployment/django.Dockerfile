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
        libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements Django
COPY E3_model_IA/backend/django_app/requirements-django.txt /app/requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copier le code Django ET les modules nécessaires
COPY E3_model_IA/backend/django_app/ /app/
COPY E3_model_IA/ /app/E3_model_IA/
COPY E1_gestion_donnees/ /app/E1_gestion_donnees/
COPY src/ /app/src/
COPY data/ /app/data/

# Créer le lien symbolique pour knowledge_base
RUN ln -sf /app/E3_model_IA/knowledge_base /app/knowledge_base

# Créer les répertoires nécessaires
RUN mkdir -p /app/logs /app/static /app/media /app/staticfiles

# Collecter les fichiers statiques et créer les migrations
RUN DJANGO_SETTINGS_MODULE=coach_ai_web.settings python manage.py collectstatic --noinput \
    && python manage.py makemigrations

# Exposer le port
EXPOSE 8002

# Commande de démarrage
CMD ["python", "manage.py", "runserver", "0.0.0.0:8002"]