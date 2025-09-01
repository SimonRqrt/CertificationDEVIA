FROM python:3.11-slim

# ====== Settings de base ======
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

ARG APP_HOME=/app
WORKDIR ${APP_HOME}

# ====== Dépendances système minimales ======
# - libpq-dev : bindings Postgres (psycopg2/psycopg)
# - curl : pour le healthcheck HTTP
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
  && rm -rf /var/lib/apt/lists/*

# ====== Dépendances Python (caching-friendly) ======
COPY E1_gestion_donnees/api_rest/requirements.txt ${APP_HOME}/requirements.txt
RUN python -m pip install --upgrade pip \
 && pip install -r requirements.txt

# ====== Code de l'API (uniquement le scope E1) ======
COPY E1_gestion_donnees/ ${APP_HOME}/E1_gestion_donnees/
COPY src/ ${APP_HOME}/src/

# ====== Droits non-root ======
# Crée un utilisateur applicatif pour éviter de tourner en root
RUN useradd -m appuser && chown -R appuser:appuser ${APP_HOME}
USER appuser

# ====== Contexte runtime ======
WORKDIR ${APP_HOME}/E1_gestion_donnees/api_rest
ENV PYTHONPATH=${APP_HOME}:${APP_HOME}/E1_gestion_donnees:${APP_HOME}/src

# ====== Réseau ======
EXPOSE 8001

# ====== Healthcheck ======
# Nécessite un endpoint /health dans ton API
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -fsS http://localhost:8001/health || exit 1

# ====== Démarrage (prod-friendly) ======
# En dev: ajoute --reload (mais à éviter en container)
# Ajuste --workers selon les ressources (2 workers par défaut)
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8001", \
     "--workers", "1", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
