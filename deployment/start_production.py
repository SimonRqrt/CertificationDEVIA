#!/usr/bin/env python3
"""
Script de démarrage pour la production Coach AI
Gère le déploiement complet avec Azure SQL Server
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def run_command(command, description="", check=True):
    """Exécute une commande et affiche le résultat"""
    print(f"\n🔄 {description or command}")
    print("=" * 60)
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"⚠️  {result.stderr}")
    
    if check and result.returncode != 0:
        print(f"❌ Erreur lors de l'exécution de: {command}")
        sys.exit(1)
    
    return result

def check_service_health(url, service_name, timeout=60):
    """Vérifie la santé d'un service"""
    print(f"\n🏥 Vérification de {service_name}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {service_name} est opérationnel")
                return True
        except requests.RequestException:
            pass
        
        print(".", end="", flush=True)
        time.sleep(2)
    
    print(f"❌ {service_name} n'est pas accessible après {timeout}s")
    return False

def main():
    """Fonction principale de démarrage"""
    
    print("🚀 Démarrage de Coach AI - Production")
    print("=====================================")
    
    # Vérifier le répertoire de travail
    if not Path("docker-compose-prod.yml").exists():
        print("❌ docker-compose-prod.yml non trouvé")
        print("Assurez-vous d'être dans le répertoire deployment/")
        sys.exit(1)
    
    # Vérifier le fichier .env
    env_file = Path("../.env")
    if not env_file.exists():
        print("❌ Fichier .env non trouvé")
        print("Créez le fichier .env avec vos configurations")
        sys.exit(1)
    
    # Arrêter les services existants
    print("\n🛑 Arrêt des services existants...")
    run_command("docker compose -f docker-compose-prod.yml down", check=False)
    
    # Nettoyer les conteneurs orphelins
    print("\n🧹 Nettoyage des conteneurs orphelins...")
    run_command("docker compose -f docker-compose-prod.yml down --remove-orphans", check=False)
    
    # Construire les images
    print("\n🏗️  Construction des images Docker...")
    run_command("docker compose -f docker-compose-prod.yml build --no-cache")
    
    # Démarrer les services
    print("\n🚀 Démarrage des services...")
    run_command("docker compose -f docker-compose-prod.yml up -d")
    
    # Attendre que les services soient prêts
    print("\n⏱️  Attente du démarrage des services...")
    time.sleep(30)
    
    # Vérifier la santé des services
    services = [
        ("http://localhost:8002/admin/", "Django Admin"),
        ("http://localhost:8000/docs", "FastAPI Documentation"),
        ("http://localhost:8501/", "Streamlit Interface"),
        ("http://localhost/health", "Nginx Proxy")
    ]
    
    all_healthy = True
    for url, name in services:
        if not check_service_health(url, name):
            all_healthy = False
    
    # Afficher le statut final
    print("\n" + "=" * 60)
    if all_healthy:
        print("🎉 Déploiement réussi !")
        print("\n📋 Services disponibles:")
        print("• Interface principale : http://localhost/")
        print("• Django Admin : http://localhost:8002/admin/")
        print("• API Documentation : http://localhost:8000/docs")
        print("• Chat IA Streamlit : http://localhost:8501/")
        print("• Plan simplifié : http://localhost/api/v1/coaching/simple-plan/")
        
        print("\n🗃️  Base de données : Azure SQL Server")
        print("🤖 Agent IA : Coach Michael avec RAG")
        print("🐳 Architecture : Docker Compose + Nginx")
        
    else:
        print("❌ Certains services ne sont pas accessibles")
        print("Vérifiez les logs avec: docker compose -f docker-compose-prod.yml logs")
    
    # Afficher les logs récents
    print("\n📜 Logs récents:")
    run_command("docker compose -f docker-compose-prod.yml logs --tail=5", check=False)

if __name__ == "__main__":
    main()