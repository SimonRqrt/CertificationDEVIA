FROM python:3.11-slim

# ====== Env de base ======
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=coach_ai_web.settings

ARG APP_HOME=/app
WORKDIR ${APP_HOME}

# ====== Dépendances système minimales ======
# libpq-dev: psycopg2/psycopg
# postgresql-client: outils psql (utile en debug)
# libmagic1: détection MIME
# curl: healthcheck
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libpq-dev \
      postgresql-client \
      libmagic1 \
      curl \
 && rm -rf /var/lib/apt/lists/*

# ====== Dépendances Python (caching-friendly) ======
COPY E3_model_IA/backend/django_app/requirements-django.txt ${APP_HOME}/requirements.txt
RUN python -m pip install --upgrade pip \
 && pip install -r requirements.txt

# ====== Code applicatif ======
# On copie l'app Django + modules annexes nécessaires
COPY E3_model_IA/backend/django_app/ ${APP_HOME}/
COPY E3_model_IA/ ${APP_HOME}/E3_model_IA/
COPY E1_gestion_donnees/ ${APP_HOME}/E1_gestion_donnees/
COPY src/ ${APP_HOME}/src/
# (SUPPRIMÉ) COPY data/ /app/data/ -> on la montera en volume au runtime via docker-compose

# Alias pratique vers knowledge_base (si ton code l'importe à /app/knowledge_base)
RUN ln -sf ${APP_HOME}/E3_model_IA/knowledge_base ${APP_HOME}/knowledge_base

# ====== Répertoires utiles ======
RUN mkdir -p ${APP_HOME}/logs ${APP_HOME}/static ${APP_HOME}/media ${APP_HOME}/staticfiles

# ====== Sécurité: exécuter en non-root ======
RUN useradd -m appuser && chown -R appuser:appuser ${APP_HOME}
USER appuser

# ====== PYTHONPATH ======
ENV PYTHONPATH=${APP_HOME}:${APP_HOME}/E1_gestion_donnees:${APP_HOME}/src

# ====== Réseau ======
EXPOSE 8002

# ====== Healthcheck (prévois /health côté Django) ======
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -fsS http://localhost:8002/health || exit 1

# ====== Démarrage ======
# NB: ton docker-compose override déjà la commande pour:
#   migrate && collectstatic && runserver
# Ici on garde une commande par défaut simple.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8002"]
