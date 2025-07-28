#!/usr/bin/env python3
"""
🚀 SCRIPT DE DÉMARRAGE COMPLET - Coaching IA + Monitoring E5
Démarre l'application complète avec monitoring intégré
"""

import subprocess
import time
import requests
import sys
import os
from pathlib import Path
import json

def run_command(cmd, description, check=True):
    """Exécute une commande avec gestion d'erreur"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - OK")
        else:
            print(f"⚠️  {description} - Warning: {result.stderr}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - ERREUR:")
        print(f"   Command: {cmd}")
        print(f"   Error: {e.stderr}")
        return None

def wait_for_service(url, service_name, timeout=60, expected_status=200):
    """Attend qu'un service soit disponible"""
    print(f"⏳ Attente de {service_name} ({url})...")
    
    for i in range(timeout):
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == expected_status:
                print(f"✅ {service_name} - Prêt!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
        if i % 10 == 0 and i > 0:
            print(f"   ... encore {timeout - i}s d'attente")
    
    print(f"❌ {service_name} - Timeout après {timeout}s")
    return False

def check_prerequisites():
    """Vérifie les prérequis"""
    print("🔍 Vérification des prérequis...")
    
    # Docker
    if not run_command("docker --version", "Docker installé"):
        print("❌ Docker requis. Installez Docker Desktop ou Docker Engine.")
        return False
    
    # Docker Compose
    if not run_command("docker compose version", "Docker Compose installé"):
        print("❌ Docker Compose requis.")
        return False
    
    # Fichier .env
    env_path = Path("../.env")
    if not env_path.exists():
        print("❌ Fichier .env manquant. Copiez .env.example vers .env")
        return False
    
    # Variables critiques
    required_vars = ['OPENAI_API_KEY', 'SECRET_KEY', 'API_KEY']
    with open(env_path) as f:
        env_content = f.read()
        missing_vars = [var for var in required_vars if var not in env_content]
        if missing_vars:
            print(f"❌ Variables .env manquantes: {', '.join(missing_vars)}")
            return False
    
    print("✅ Prérequis OK")
    return True

def setup_monitoring_structure():
    """Crée la structure de monitoring"""
    print("📁 Configuration structure monitoring...")
    
    monitoring_dir = Path("../E5_monitoring")
    directories = [
        "prometheus/rules",
        "grafana/provisioning/datasources",
        "grafana/provisioning/dashboards",
        "grafana/dashboards", 
        "loki",
        "alertmanager",
        "promtail",
        "logs/django",
        "logs/fastapi",
        "logs/streamlit"
    ]
    
    for directory in directories:
        dir_path = monitoring_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Permissions pour volumes Docker
    run_command("chmod -R 777 ../E5_monitoring/logs", "Permissions logs", check=False)
    
    print("✅ Structure monitoring créée")

def start_application_stack():  
    """Démarre la stack applicative complète"""
    print("🚀 Démarrage de la stack complète...")
    
    # Arrêt des services existants
    run_command(
        "docker compose -f docker-compose-full.yml down --remove-orphans",
        "Arrêt services existants",
        check=False
    )
    
    # Nettoyage des volumes orphelins
    run_command(
        "docker volume prune -f",
        "Nettoyage volumes",
        check=False
    )
    
    # Build et démarrage
    if not run_command(
        "docker compose -f docker-compose-full.yml up --build -d",
        "Build et démarrage stack complète"
    ):
        return False
    
    print("✅ Stack démarrée")
    return True

def wait_for_all_services():
    """Attend que tous les services soient disponibles"""
    print("⏳ Vérification disponibilité des services...")
    
    services = [
        # Services principaux
        ("http://localhost:8002/admin/", "Django Admin"),
        ("http://localhost:8000/docs", "FastAPI Docs"),
        ("http://localhost:8501", "Streamlit UI"),
        
        # Services monitoring
        ("http://localhost:9090", "Prometheus"),
        ("http://localhost:3000", "Grafana"),
        ("http://localhost:3100/ready", "Loki"),
        ("http://localhost:9093", "AlertManager"),
        ("http://localhost:9100/metrics", "Node Exporter"),
    ]
    
    all_ready = True
    for url, name in services:
        if not wait_for_service(url, name, timeout=90):
            all_ready = False
    
    return all_ready

def setup_grafana_datasources():
    """Configure automatiquement Grafana"""
    print("🔧 Configuration automatique Grafana...")
    
    time.sleep(15)  # Attente démarrage complet Grafana
    
    try:
        # Test connexion Grafana
        response = requests.get("http://admin:admin123@localhost:3000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Grafana configuré automatiquement via provisioning")
        else:
            print("⚠️  Configuration Grafana manuelle requise")
    except Exception as e:
        print(f"⚠️  Configuration Grafana: {e}")

def check_docker_health():
    """Vérifie la santé des containers"""
    print("🩺 Vérification santé des containers...")
    
    result = run_command(
        "docker-compose -f docker-compose-full.yml ps",
        "Status containers"
    )
    
    if result:
        lines = result.strip().split('\n')[1:]  # Skip header
        healthy_count = 0
        total_count = len(lines)
        
        for line in lines:
            if 'healthy' in line.lower() or 'up' in line.lower():
                healthy_count += 1
        
        print(f"✅ Containers: {healthy_count}/{total_count} en bonne santé")
        
        if healthy_count < total_count:
            print("⚠️  Certains containers ont des problèmes")
            print("   Utilisez: docker-compose -f docker-compose-full.yml logs [service]")

def display_dashboard():
    """Affiche le dashboard des services"""
    print("\n" + "="*70)
    print("🎉 COACHING IA + MONITORING E5 - PRÊT!")
    print("="*70)
    print("🏠 APPLICATION PRINCIPALE")
    print("   📊 Django Dashboard    : http://localhost:8002/api/v1/core/dashboard/")
    print("   🎯 Assistant Objectifs : http://localhost:8002/api/v1/coaching/running-wizard/")
    print("   📋 Admin Django        : http://localhost:8002/admin/")
    print("   🤖 FastAPI Docs        : http://localhost:8000/docs")
    print("   💬 Streamlit Chat      : http://localhost:8501/")
    print()
    print("🔍 MONITORING E5")
    print("   📈 Grafana Dashboards  : http://localhost:3000 (admin/admin123)")
    print("   🎯 Prometheus Metrics  : http://localhost:9090")
    print("   📝 Loki Logs           : http://localhost:3100 (via Grafana)")
    print("   🚨 AlertManager        : http://localhost:9093")
    print("   📊 Node Exporter       : http://localhost:9100/metrics")
    print("   🔔 Webhook Receiver    : http://localhost:5001 (logs alertes)")
    print()
    print("⚡ MÉTRIQUES TEMPS RÉEL")
    print("   Django    : http://localhost:8002/metrics")
    print("   FastAPI   : http://localhost:8000/metrics")
    print()
    print("🗂️  LOGS")
    print("   Application : docker-compose -f docker-compose-full.yml logs -f")
    print("   Monitoring  : docker-compose -f docker-compose-full.yml logs -f grafana")
    print("="*70)

def run_integration_tests():
    """Lance des tests d'intégration basiques"""
    print("🧪 Tests d'intégration rapides...")
    
    tests = [
        ("http://localhost:8002/metrics", "Django métriques"),
        ("http://localhost:8000/metrics", "FastAPI métriques"),
        ("http://localhost:9090/api/v1/targets", "Prometheus targets"),
        ("http://localhost:3000/api/health", "Grafana santé"),
    ]
    
    for url, test_name in tests:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"✅ {test_name}")
            else:
                print(f"⚠️  {test_name} - Status: {response.status_code}")
        except Exception as e:
            print(f"❌ {test_name} - Erreur: {e}")

def main():
    """Fonction principale"""
    print("🤖 COACHING IA + MONITORING E5")
    print("Démarrage application complète avec monitoring")
    print("="*60)
    
    # Changement vers le répertoire deployment
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Vérifications
    if not check_prerequisites():
        sys.exit(1)
    
    # Setup
    setup_monitoring_structure()
    
    # Démarrage
    if not start_application_stack():
        print("❌ Échec du démarrage de l'application")
        sys.exit(1)
    
    # Attente des services
    if not wait_for_all_services():
        print("⚠️  Certains services ne répondent pas, mais continuons...")
    
    # Configuration
    setup_grafana_datasources()
    
    # Vérifications
    check_docker_health()
    run_integration_tests()
    
    # Dashboard final
    display_dashboard()
    
    print("\n💡 CONSEILS:")
    print("   - Consultez Grafana pour les métriques temps réel")
    print("   - Vérifiez les alertes dans AlertManager")
    print("   - Logs complets: docker-compose -f docker-compose-full.yml logs")
    print("   - Arrêt: docker-compose -f docker-compose-full.yml down")

if __name__ == "__main__":
    main()