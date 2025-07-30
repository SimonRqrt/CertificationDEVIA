FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=coach_ai_web.settings

# Répertoire de travail
WORKDIR /app

# Installer les dépendances système avec Microsoft ODBC Driver
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        libpq-dev \
        unixodbc-dev \
        gnupg2 \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Copier les requirements Django
COPY E3_model_IA/backend/django_app/requirements-django.txt /app/requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copier le code Django
COPY E3_model_IA/backend/django_app/ /app/
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