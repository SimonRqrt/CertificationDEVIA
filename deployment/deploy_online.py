#!/usr/bin/env python3
"""
Script de déploiement pour la mise en ligne Coach AI
Gère le déploiement avec Azure SQL Server + fallback automatique
"""

import os
import sys
import subprocess
import time
import requests
import socket
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
        return False
    
    return True

def check_azure_sql_connectivity():
    """Vérifie la connectivité vers Azure SQL Server"""
    print("\n🔍 Test de connectivité Azure SQL Server...")
    
    host = "adventureworks-server-hdf.database.windows.net"
    port = 1433
    
    try:
        socket.create_connection((host, port), timeout=10)
        print("✅ Azure SQL Server accessible")
        return True
    except (socket.error, socket.timeout) as e:
        print(f"⚠️ Azure SQL Server inaccessible: {e}")
        print("🔄 Django basculera automatiquement vers SQLite")
        return False

def check_service_health(url, service_name, timeout=90):
    """Vérifie la santé d'un service"""
    print(f"\n🏥 Vérification de {service_name}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                print(f"✅ {service_name} est opérationnel")
                return True
        except requests.RequestException:
            pass
        
        print(".", end="", flush=True)
        time.sleep(3)
    
    print(f"❌ {service_name} n'est pas accessible après {timeout}s")
    return False

def main():
    """Fonction principale de déploiement"""
    
    print("🚀 Déploiement Coach AI - Mode Online")
    print("====================================")
    
    # Vérifier le répertoire de travail
    if not Path("docker-compose-online.yml").exists():
        print("❌ docker-compose-online.yml non trouvé")
        print("Assurez-vous d'être dans le répertoire deployment/")
        sys.exit(1)
    
    # Vérifier le fichier .env
    env_file = Path("../.env")
    if not env_file.exists():
        print("❌ Fichier .env non trouvé")
        print("Créez le fichier .env avec vos configurations")
        sys.exit(1)
    
    # Test de connectivité Azure SQL
    azure_sql_available = check_azure_sql_connectivity()
    
    # Arrêter les services existants
    print("\n🛑 Arrêt des services existants...")
    run_command("docker compose -f docker-compose-online.yml down --remove-orphans", check=False)
    
    # Nettoyer les images orphelines
    print("\n🧹 Nettoyage des images...")
    run_command("docker image prune -f", check=False)
    
    # Construire les images
    print("\n🏗️  Construction des images...")
    if not run_command("docker compose -f docker-compose-online.yml build --no-cache"):
        print("❌ Échec de la construction des images")
        sys.exit(1)
    
    # Démarrer les services
    print("\n🚀 Démarrage des services...")
    if not run_command("docker compose -f docker-compose-online.yml up -d"):
        print("❌ Échec du démarrage des services")
        
        # Afficher les logs en cas d'erreur
        print("\n📜 Logs d'erreur:")
        run_command("docker compose -f docker-compose-online.yml logs --tail=20", check=False)
        sys.exit(1)
    
    # Attendre que les services soient prêts
    print("\n⏱️  Attente du démarrage des services...")
    time.sleep(45)  # Plus long pour Azure SQL
    
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
        print("🎉 Déploiement en ligne réussi !")
        print("\n📋 Services disponibles:")
        print("• Interface principale : http://localhost/")
        print("• Django Admin : http://localhost:8002/admin/")
        print("• API Documentation : http://localhost:8000/docs")
        print("• Chat IA Streamlit : http://localhost:8501/")
        print("• Générateur plans : http://localhost/api/v1/coaching/simple-plan/")
        
        db_status = "Azure SQL Server" if azure_sql_available else "SQLite (fallback automatique)"
        print(f"\n🗃️  Base de données : {db_status}")
        print("🤖 Agent IA : Coach Michael avec RAG")
        print("🐳 Architecture : Docker + Nginx + Fallback Azure SQL")
        
        print("\n🔧 Commandes utiles:")
        print("• Logs: docker compose -f docker-compose-online.yml logs -f")
        print("• Status: docker compose -f docker-compose-online.yml ps")
        print("• Restart: docker compose -f docker-compose-online.yml restart")
        
    else:
        print("❌ Certains services ne sont pas accessibles")
        print("Vérifiez les logs avec: docker compose -f docker-compose-online.yml logs")
    
    # Afficher les logs récents
    print("\n📜 Status des containers:")
    run_command("docker compose -f docker-compose-online.yml ps", check=False)

if __name__ == "__main__":
    main()