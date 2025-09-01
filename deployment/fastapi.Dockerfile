FROM python:3.11-slim

# ====== Env de base ======
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

ARG APP_HOME=/app
WORKDIR ${APP_HOME}

# ====== Dépendances système ======
# - libpq-dev : clients/headers Postgres (psycopg2/psycopg)
# - unixodbc-dev + msodbcsql18 : ODBC SQL Server
# - libmagic1 : si ton app fait du mimetype (python-magic)
# - curl : healthcheck et debug réseau
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
      unixodbc-dev \
      libmagic1 \
      curl \
      gnupg \
 && rm -rf /var/lib/apt/lists/*

# ====== Repo Microsoft + Driver ODBC 18 (amd64 uniquement) ======
ARG TARGETARCH
RUN set -eux; \
    if [ "${TARGETARCH}" = "amd64" ]; then \
      curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg; \
      echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
        > /etc/apt/sources.list.d/mssql-release.list; \
      apt-get update; \
      ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18; \
      rm -rf /var/lib/apt/lists/*; \
    else \
      echo "Skipping msodbcsql18 install on ARCH=${TARGETARCH}"; \
    fi

# ====== Config odbcinst (driver path dynamique) ======
# Évite de figer la version exacte du .so ; on détecte la lib installée.
RUN set -eux; \
    if [ -d "/opt/microsoft/msodbcsql18/lib64" ]; then \
      DRIVER_PATH="$(find /opt/microsoft/msodbcsql18/lib64 -maxdepth 1 -type f -name 'libmsodbcsql-*.so*' | head -n1)"; \
      echo "[ODBC Driver 18 for SQL Server]"                 > /etc/odbcinst.ini; \
      echo "Description=Microsoft ODBC Driver 18 for SQL Server" >> /etc/odbcinst.ini; \
      echo "Driver=${DRIVER_PATH}"                           >> /etc/odbcinst.ini; \
      echo "Threading=1"                                     >> /etc/odbcinst.ini; \
    else \
      echo "ODBC driver not installed (non-amd64); skipping odbcinst config"; \
    fi

# ====== Dépendances Python ======
COPY E3_model_IA/backend/fastapi_app/requirements-fastapi.txt ${APP_HOME}/requirements.txt
RUN python -m pip install --upgrade pip \
 && pip install -r /app/requirements.txt

# ====== Code applicatif ======
COPY E3_model_IA/ ${APP_HOME}/E3_model_IA/
COPY E1_gestion_donnees/ ${APP_HOME}/E1_gestion_donnees/
COPY src/ ${APP_HOME}/src/
COPY E3_model_IA/knowledge_base/ ${APP_HOME}/knowledge_base/
# (SUPPRIMÉ) COPY data/ ...  -> causait l'erreur; les données seront montées en volume via docker-compose

# ====== Permissions non-root ======
RUN useradd -m appuser && mkdir -p ${APP_HOME}/static ${APP_HOME}/logs \
    && chown -R appuser:appuser ${APP_HOME}
USER appuser

# ====== Contexte runtime ======
ENV PYTHONPATH="${APP_HOME}:${APP_HOME}/E3_model_IA/backend/fastapi_app:${APP_HOME}/E1_gestion_donnees"
WORKDIR ${APP_HOME}/E3_model_IA/backend/fastapi_app

# ====== Réseau ======
EXPOSE 8000

# ====== Healthcheck (prévoir /health côté app) ======
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

# ====== Démarrage ======
# Prod: workers + proxy headers; enlève --reload pour éviter le reloader en container
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]

# --- Variante DEV (si besoin de hot-reload) ---
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
