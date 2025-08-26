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
        unixodbc-dev \
        gnupg \
        libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Ajouter la clé et le référentiel Microsoft pour ODBC
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Installer le pilote ODBC version 18
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Configurer odbcinst pour enregistrer le driver ODBC
RUN echo '[ODBC Driver 18 for SQL Server]' > /etc/odbcinst.ini \
    && echo 'Description=Microsoft ODBC Driver 18 for SQL Server' >> /etc/odbcinst.ini \
    && echo 'Driver=/opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.5.so.1.1' >> /etc/odbcinst.ini \
    && echo 'Threading=1' >> /etc/odbcinst.ini

# Copier les requirements FastAPI
COPY E3_model_IA/backend/fastapi_app/requirements-fastapi.txt /app/requirements.txt

# Installer les dépendances Python
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY E3_model_IA/ /app/E3_model_IA/
COPY E1_gestion_donnees/ /app/E1_gestion_donnees/
COPY src/ /app/src/
COPY E3_model_IA/knowledge_base/ /app/knowledge_base/
COPY data/ /app/data/

# Définir le PYTHONPATH (éviter le conflit avec Django)
ENV PYTHONPATH="/app:/app/E3_model_IA/backend/fastapi_app:/app/E1_gestion_donnees"

# Exposer le port
EXPOSE 8000

# Créer répertoires nécessaires
RUN mkdir -p /app/static /app/logs

# Commande de démarrage
WORKDIR /app/E3_model_IA/backend/fastapi_app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]