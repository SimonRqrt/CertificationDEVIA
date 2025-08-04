#!/usr/bin/env python3
"""
Test direct de l'appel FastAPI
"""
import requests
import json
import os

def test_fastapi():
    print("🔧 Test de l'appel FastAPI direct...")
    
    fastapi_url = 'http://fastapi:8000'  # URL container
    api_key = os.getenv('API_KEY', 'default_key')
    
    payload = {
        'message': 'Test direct de génération de plan pour objectif 10K',
        'thread_id': 'test-plan-generation-direct',
        'user_id': 1
    }
    
    headers = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    print(f"📡 URL: {fastapi_url}/v1/coaching/chat-legacy")
    print(f"🔑 API Key: {api_key[:10]}...")
    print(f"📝 Payload: {payload}")
    
    try:
        response = requests.post(
            f'{fastapi_url}/v1/coaching/chat-legacy',
            json=payload,
            headers=headers,
            timeout=30
        )
        
        print(f"📈 Status: {response.status_code}")
        print(f"📄 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            # Traiter la réponse streaming
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if data.get("type") == "content":
                            full_response += data.get("data", "")
                    except:
                        continue
            
            print(f"📊 Réponse reçue: {len(full_response)} caractères")
            print(f"📋 Aperçu: {full_response[:200]}...")
            
            if 'plan' in full_response.lower() and 'tableau' in full_response.lower():
                print("✅ Plan structuré généré")
            else:
                print("⚠️ Plan non structuré")
            
        else:
            print(f"❌ Erreur HTTP: {response.text}")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'appel: {e}")

if __name__ == "__main__":
    test_fastapi()