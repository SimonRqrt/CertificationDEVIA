#!/bin/bash

echo "🚀 Démarrage Django..."

# Attendre que la base de données soit prête
echo "⏳ Attente de la base de données..."
sleep 10

# Appliquer les migrations
echo "📦 Application des migrations..."
python manage.py migrate --noinput

# Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Créer un superuser si nécessaire (optionnel)
echo "👤 Vérification du superuser..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser créé: admin/admin123')
else:
    print('Superuser existe déjà')
"

# Démarrer le serveur
echo "🌐 Démarrage du serveur Django..."
python manage.py runserver 0.0.0.0:8002 