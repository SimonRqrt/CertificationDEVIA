#!/usr/bin/env python3
"""
Script pour créer un superuser Django
"""
import os
import sys
import django

# Configuration Django
sys.path.append('/Users/sims/Documents/Simplon_DEV_IA/Certification/CertificationDEVIA/E1_gestion_donnees/api_rest')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coach_ai_web.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Vérifier si un superuser existe déjà
if User.objects.filter(is_superuser=True).exists():
    print("Un superuser existe déjà !")
    for user in User.objects.filter(is_superuser=True):
        print(f"- Email: {user.email}, Username: {user.username}")
else:
    # Créer un superuser par défaut
    email = "admin@coach-ai.com"
    username = "admin"
    password = "admin123"
    
    user = User.objects.create_superuser(
        email=email,
        username=username,
        password=password,
        first_name="Admin",
        last_name="User"
    )
    print(f"Superuser créé avec succès !")
    print(f"Email: {email}")
    print(f"Username: {username}")
    print(f"Password: {password}")