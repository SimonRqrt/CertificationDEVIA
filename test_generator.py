#!/usr/bin/env python3
"""
Script de test pour le générateur de plans d'entraînement
"""
import os
import sys

# Ajouter le répertoire Django au PYTHONPATH
sys.path.insert(0, '/Users/sims/Documents/Simplon_DEV_IA/Certification/CertificationDEVIA/E3_model_IA/backend/django_app')

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coach_ai_web.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from coaching.views import simple_plan_generator
from django.test import RequestFactory
from django.http import HttpRequest

User = get_user_model()

def test_generator():
    print("🧪 Test du générateur de plans...")
    
    # Créer ou récupérer un utilisateur de test
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@coach-ai.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
    )
    
    if created:
        user.set_password('secure123')
        user.save()
        print(f"✅ Utilisateur créé: {user.username}")
    else:
        print(f"✅ Utilisateur existant: {user.username}")
    
    # Créer une requête POST simulée
    factory = RequestFactory()
    
    post_data = {
        'goal': '10K',
        'level': 'Intermédiaire',
        'sessions': '3',
        'target_date': '2025-09-01',
        'additional_notes': 'Test automatique du générateur'
    }
    
    request = factory.post('/api/v1/coaching/simple-plan/', post_data)
    request.user = user
    
    print("📝 Données de test:")
    for key, value in post_data.items():
        print(f"   {key}: {value}")
    
    try:
        # Appeler la vue
        print("\n🚀 Appel du générateur...")
        response = simple_plan_generator(request)
        print(f"✅ Réponse reçue: {response.status_code}")
        
        if hasattr(response, 'content'):
            content = response.content.decode('utf-8')
            print(f"📄 Longueur du contenu: {len(content)} caractères")
            
            # Rechercher différents indicateurs de plan
            plan_indicators = ['Plan d\'entraînement', 'plan d\'entraînement', 'Programme hebdomadaire', 'planning', 'Coach Michael']
            table_indicators = ['| Jour |', '|---|', 'Lundi', 'Mardi', 'Mercredi']
            
            plan_found = any(indicator in content for indicator in plan_indicators)
            table_found = any(indicator in content for indicator in table_indicators)
            
            # Vérifier d'abord l'origine de la réponse
            if 'agent ia avancé' in content.lower():
                print("✅ Appel FastAPI réussi")
            else:
                print("⚠️ Appel FastAPI échoué - utilisation du fallback local")
            
            if plan_found:
                print("✅ Plan généré avec succès!")
                if table_found:
                    print("✅ Tableau d'entraînement détecté")
                else:
                    print("⚠️ Format de tableau non détecté")
            else:
                print("⚠️ Plan non détecté dans la réponse")
                # Afficher un aperçu du contenu pour debug
                print(f"📋 Aperçu (200 premiers caractères): {content[:200]}...")
                
                # Chercher des messages d'erreur spécifiques
                if 'erreur' in content.lower() or 'error' in content.lower():
                    print("⚠️ Message d'erreur détecté dans la réponse")
                if 'fallback' in content.lower():
                    print("⚠️ Mode fallback activé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_generator()
    sys.exit(0 if success else 1)