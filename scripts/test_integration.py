#!/usr/bin/env python3
"""
Script de test d'intégration Django + FastAPI
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configuration
DJANGO_URL = "http://localhost:8002"
FASTAPI_URL = "http://localhost:8000"

def test_django_health():
    """Tester la santé de Django"""
    try:
        response = requests.get(f"{DJANGO_URL}/admin/", timeout=5)
        if response.status_code == 200:
            print("✅ Django est accessible")
            return True
        else:
            print(f"❌ Django répond avec le code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Django n'est pas accessible: {e}")
        return False

def test_fastapi_health():
    """Tester la santé de FastAPI"""
    try:
        response = requests.get(f"{FASTAPI_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ FastAPI est accessible")
            return True
        else:
            print(f"❌ FastAPI répond avec le code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ FastAPI n'est pas accessible: {e}")
        return False

def test_django_auth():
    """Tester l'authentification Django"""
    try:
        # Test d'inscription
        register_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "password_confirm": "testpassword123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = requests.post(
            f"{DJANGO_URL}/api/v1/auth/register/",
            json=register_data,
            timeout=10
        )
        
        if response.status_code == 201:
            print("✅ Inscription Django réussie")
            return response.json()
        else:
            print(f"❌ Inscription échouée: {response.status_code}")
            print(f"   Détails: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de l'inscription: {e}")
        return None

def test_django_login():
    """Tester la connexion Django"""
    try:
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = requests.post(
            f"{DJANGO_URL}/api/v1/auth/login/",
            json=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Connexion Django réussie")
            return response.json()
        else:
            print(f"❌ Connexion échouée: {response.status_code}")
            print(f"   Détails: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la connexion: {e}")
        return None

def test_fastapi_with_django_auth(access_token: str):
    """Tester FastAPI avec authentification Django"""
    try:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        chat_data = {
            "message": "Bonjour, je suis un test d'intégration!"
        }
        
        # Test de l'endpoint de chat
        response = requests.post(
            f"{FASTAPI_URL}/v1/coaching/chat",
            json=chat_data,
            headers=headers,
            timeout=30,
            stream=True
        )
        
        if response.status_code == 200:
            print("✅ Chat FastAPI avec auth Django réussi")
            return True
        else:
            print(f"❌ Chat FastAPI échoué: {response.status_code}")
            print(f"   Détails: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors du chat FastAPI: {e}")
        return False

def test_legacy_fastapi():
    """Tester l'endpoint legacy FastAPI"""
    try:
        headers = {
            "X-API-Key": "test-api-key",
            "Content-Type": "application/json"
        }
        
        chat_data = {
            "message": "Test legacy endpoint"
        }
        
        response = requests.post(
            f"{FASTAPI_URL}/v1/coaching/chat-legacy",
            json=chat_data,
            headers=headers,
            timeout=30,
            stream=True
        )
        
        if response.status_code == 200:
            print("✅ Endpoint legacy FastAPI fonctionnel")
            return True
        else:
            print(f"❌ Endpoint legacy échoué: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur endpoint legacy: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 Démarrage des tests d'intégration...")
    print("=" * 50)
    
    # Test 1: Santé des services
    print("\n1️⃣ Test de santé des services:")
    django_ok = test_django_health()
    fastapi_ok = test_fastapi_health()
    
    if not django_ok or not fastapi_ok:
        print("❌ Services non disponibles. Arrêt des tests.")
        sys.exit(1)
    
    # Test 2: Authentification Django
    print("\n2️⃣ Test d'authentification Django:")
    auth_response = test_django_auth()
    
    if not auth_response:
        print("❌ Échec de l'authentification Django")
        sys.exit(1)
    
    access_token = auth_response.get('access')
    if not access_token:
        print("❌ Token d'accès manquant")
        sys.exit(1)
    
    # Test 3: Connexion Django
    print("\n3️⃣ Test de connexion Django:")
    login_response = test_django_login()
    
    if login_response:
        access_token = login_response.get('access', access_token)
    
    # Test 4: Intégration FastAPI + Django
    print("\n4️⃣ Test d'intégration FastAPI + Django:")
    integration_ok = test_fastapi_with_django_auth(access_token)
    
    # Test 5: Endpoint legacy
    print("\n5️⃣ Test endpoint legacy:")
    legacy_ok = test_legacy_fastapi()
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 Résumé des tests:")
    print(f"   Django: {'✅' if django_ok else '❌'}")
    print(f"   FastAPI: {'✅' if fastapi_ok else '❌'}")
    print(f"   Auth Django: {'✅' if auth_response else '❌'}")
    print(f"   Intégration: {'✅' if integration_ok else '❌'}")
    print(f"   Legacy: {'✅' if legacy_ok else '❌'}")
    
    if all([django_ok, fastapi_ok, auth_response, integration_ok, legacy_ok]):
        print("\n🎉 Tous les tests sont passés avec succès!")
        sys.exit(0)
    else:
        print("\n❌ Certains tests ont échoué.")
        sys.exit(1)

if __name__ == "__main__":
    main()