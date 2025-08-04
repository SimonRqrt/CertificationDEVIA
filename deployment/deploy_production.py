#!/usr/bin/env python3
"""
Script de déploiement production pour CertificationDEVIA
Teste et valide la configuration Supabase avant déploiement
"""

import os
import sys
import time
import subprocess
import psycopg2
from pathlib import Path

def load_env_vars():
    """Charge les variables d'environnement depuis .env"""
    env_file = Path(__file__).parent.parent / '.env'
    
    if not env_file.exists():
        print("❌ Fichier .env introuvable")
        return False
        
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    
    print("✅ Variables .env chargées")
    return True

def test_supabase_connection():
    """Test la connexion Supabase PostgreSQL"""
    print("\n=== TEST CONNEXION SUPABASE ===")
    
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL non définie")
            return False
            
        print(f"Test connexion: {database_url[:50]}...")
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Test version PostgreSQL
        cursor.execute('SELECT version()')
        version = cursor.fetchone()[0]
        print(f"✅ PostgreSQL: {version[:60]}...")
        
        # Test données existantes
        cursor.execute('SELECT COUNT(*) FROM activities_activity')
        count = cursor.fetchone()[0]
        print(f"✅ Activités trouvées: {count}")
        
        # Test performance
        start_time = time.time()
        cursor.execute('SELECT COUNT(*) FROM django_session')
        duration = time.time() - start_time
        print(f"✅ Performance: {duration*1000:.1f}ms")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur Supabase: {e}")
        return False

def check_production_requirements():
    """Vérifie les prérequis pour le déploiement production"""
    print("\n=== VÉRIFICATION PRÉREQUIS PRODUCTION ===")
    
    requirements = {
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', '').startswith('sk-'),
        'SECRET_KEY': len(os.environ.get('SECRET_KEY', '')) >= 32,
        'DB_TYPE': os.environ.get('DB_TYPE') == 'postgresql',
        'DATABASE_URL': 'postgresql://' in os.environ.get('DATABASE_URL', ''),
    }
    
    all_ok = True
    for req, status in requirements.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {req}: {'OK' if status else 'MANQUANT'}")
        if not status:
            all_ok = False
    
    return all_ok

def build_production_images():
    """Build les images Docker pour la production"""
    print("\n=== BUILD IMAGES DOCKER PRODUCTION ===")
    
    try:
        # Changer vers le répertoire de déploiement
        os.chdir(Path(__file__).parent)
        
        # Build avec cache
        cmd = [
            'docker', 'compose', '-f', 'docker-compose-production.yml', 
            'build', '--parallel'
        ]
        
        print(f"Commande: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Images Docker buildées avec succès")
            return True
        else:
            print(f"❌ Erreur build: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur build: {e}")
        return False

def deploy_production():
    """Déploie en mode production"""
    print("\n=== DÉPLOIEMENT PRODUCTION ===")
    
    try:
        # Variables d'environnement production
        prod_env = os.environ.copy()
        prod_env.update({
            'PRODUCTION_MODE': 'true',
            'DISABLE_SQLITE_FALLBACK': 'true',
            'DEBUG': 'false'
        })
        
        # Démarrer les services
        cmd = [
            'docker', 'compose', '-f', 'docker-compose-production.yml',
            'up', '-d'
        ]
        
        print(f"Commande: {' '.join(cmd)}")
        result = subprocess.run(cmd, env=prod_env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Services déployés en production")
            return True
        else:
            print(f"❌ Erreur déploiement: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur déploiement: {e}")
        return False

def test_production_deployment():
    """Test le déploiement production"""
    print("\n=== TEST DÉPLOIEMENT PRODUCTION ===")
    
    # Attendre que les services démarrent
    print("Attente démarrage services (30s)...")
    time.sleep(30)
    
    # Tests des endpoints
    tests = [
        ('http://localhost/health', 'Nginx'),
        ('http://localhost:8002/health/', 'Django'),
        ('http://localhost:8000/health', 'FastAPI'),
        ('http://localhost:8501/_stcore/health', 'Streamlit'),
    ]
    
    all_ok = True
    for url, service in tests:
        try:
            import urllib.request
            response = urllib.request.urlopen(url, timeout=10)
            status = "✅" if response.getcode() == 200 else "❌"
            print(f"{status} {service}: {response.getcode()}")
        except Exception as e:
            print(f"❌ {service}: {e}")
            all_ok = False
    
    return all_ok

def main():
    """Fonction principale"""
    print("🚀 DÉPLOIEMENT PRODUCTION CertificationDEVIA")
    print("=" * 50)
    
    # Étapes de validation
    steps = [
        ("Chargement variables environnement", load_env_vars),
        ("Test connexion Supabase", test_supabase_connection),
        ("Vérification prérequis", check_production_requirements),
        ("Build images Docker", build_production_images),
        ("Déploiement production", deploy_production),
        ("Test déploiement", test_production_deployment),
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        if not step_func():
            print(f"\n❌ ÉCHEC: {step_name}")
            print("\n🛑 Déploiement interrompu")
            sys.exit(1)
    
    print("\n🎉 DÉPLOIEMENT PRODUCTION RÉUSSI!")
    print("\n📊 URLs de production:")
    print("- Interface principale: http://localhost/")
    print("- API Django: http://localhost:8002/")
    print("- API FastAPI: http://localhost/api/v2/")
    print("- Chat Streamlit: http://localhost/chat/")
    print("- Admin Django: http://localhost:8002/admin/")
    
    print("\n✅ Le projet utilise Supabase PostgreSQL en mode production")
    print("✅ Aucun fallback SQLite en production")

if __name__ == '__main__':
    main()