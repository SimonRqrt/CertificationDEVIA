# Utiliser la même image de base pour la cohérence
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Les dépendances sont les mêmes, donc on peut utiliser le même requirements.txt

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le reste du code

COPY . .

# Exposer le port standard de Streamlit

EXPOSE 8501

# La commande pour démarrer l'application Streamlit

CMD ["streamlit", "run", "E4_app_IA/ui/app_streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"]