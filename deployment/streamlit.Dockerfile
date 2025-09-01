FROM python:3.11-slim

# ====== Env de base ======
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

ARG APP_HOME=/app
WORKDIR ${APP_HOME}

# ====== Dépendances système minimales ======
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      curl \
 && rm -rf /var/lib/apt/lists/*

# ====== Dépendances Python (caching-friendly) ======
COPY E4_app_IA/frontend/streamlit_app/requirements-streamlit.txt ${APP_HOME}/requirements.txt
RUN python -m pip install --upgrade pip \
 && pip install -r requirements.txt

# ====== Code Streamlit ======
COPY E4_app_IA/frontend/streamlit_app/ ${APP_HOME}/
# (SUPPRIMÉ) COPY data/ /app/data/ -> on la montera en volume via docker-compose

# ====== Config Streamlit par défaut ======
# Tu peux aussi monter un secrets.toml via volume
RUN mkdir -p ${APP_HOME}/.streamlit
# Exemple de config par défaut "conteneur-friendly"
# (si tu as déjà un fichier, pas nécessaire)
RUN printf "[server]\nheadless = true\nenableCORS = false\nenableXsrfProtection = true\nport = 8501\n" > ${APP_HOME}/.streamlit/config.toml

# ====== Sécurité: non-root ======
RUN useradd -m appuser && chown -R appuser:appuser ${APP_HOME}
USER appuser

# ====== Réseau ======
EXPOSE 8501

# ====== Healthcheck (réutilise curl installé) ======
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -fsS http://localhost:8501/ || exit 1

# ====== Démarrage ======
CMD ["streamlit", "run", "app_streamlit.py", "--server.address=0.0.0.0", "--server.port=8501"]
