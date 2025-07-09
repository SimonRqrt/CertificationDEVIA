# Utiliser une image Python officielle et légère
FROM python:3.11-slim

# Définir des variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

ENV HF_HOME=/app/cache//huggingface
ENV TRANSFORMERS_CACHE=/app/cache/transformers

# --- Installation des dépendances système ---

USER root

# 1. Installation des outils de base et de libmagic
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    unixodbc-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Ajout de la clé et du référentiel de paquets Microsoft pour le pilote ODBC
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list

# 3. Installation du pilote ODBC version 18
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# --- Fin de l'installation des dépendances système ---

# Créer un utilisateur non-root pour la sécurité
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Créer et définir le répertoire de travail
WORKDIR /app

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code de l'application
COPY . .

# Exposer le port et lancer l'application
EXPOSE 8000
CMD ["uvicorn", "E3_model_IA.api_service:app", "--host", "0.0.0.0", "--port", "8000"]