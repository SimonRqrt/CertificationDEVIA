#!/usr/bin/env python3
"""
Tests simples pour l'API REST simplifiée
"""

import requests
import json

def test_api():
    base_url = "http://localhost:8001"
    
    print("Tests API REST Simple")
    print("=" * 40)
    
    # Test 1: Santé
    print("1. Test santé...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("API en bonne santé")
        else:
            print(f"Problème santé: {response.status_code}")
    except Exception as e:
        print(f"API non accessible: {e}")
        return
    
    # Test 2: Login
    print("\n2. Test authentification...")
    try:
        login_data = {"username": "admin", "password": "password"}
        response = requests.post(f"{base_url}/auth/login", json=login_data, timeout=5)
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            print("Login réussi, token obtenu")
            headers = {"Authorization": f"Bearer {token}"}
        else:
            print(f"Échec login: {response.status_code}")
            return
    except Exception as e:
        print(f"Erreur login: {e}")
        return
    
    # Test 3: Utilisateurs
    print("\n3. Test endpoint utilisateurs...")
    try:
        response = requests.get(f"{base_url}/api/v1/users", headers=headers, timeout=5)
        if response.status_code == 200:
            users = response.json()
            print(f"{len(users)} utilisateurs récupérés")
        else:
            print(f"Erreur utilisateurs: {response.status_code}")
    except Exception as e:
        print(f"Erreur endpoint users: {e}")
    
    # Test 4: Activités
    print("\n4. Test endpoint activités...")
    try:
        response = requests.get(f"{base_url}/api/v1/activities", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"{data['total']} activités (page {data['page']})")
        else:
            print(f"Erreur activités: {response.status_code}")
    except Exception as e:
        print(f"Erreur endpoint activities: {e}")
    
    # Test 5: Création activité
    print("\n5. Test création activité...")
    try:
        new_activity = {
            "user_id": 1,
            "activity_name": "Test API",
            "activity_type": "running",
            "start_time": "2025-01-08T10:00:00",
            "duration_seconds": 1800,
            "distance_meters": 3000,
            "average_hr": 140,
            "calories": 200
        }
        response = requests.post(f"{base_url}/api/v1/activities", json=new_activity, headers=headers, timeout=5)
        if response.status_code == 201:
            activity = response.json()
            print(f"Activité créée (ID: {activity['id']})")
        else:
            print(f"Erreur création: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Erreur création activité: {e}")
    
    print("\n" + "=" * 40)
    print("Tests terminés!")
    print("Documentation complète: http://localhost:8001/docs")

if __name__ == "__main__":
    test_api()