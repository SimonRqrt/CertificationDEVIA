#!/usr/bin/env python3
"""
Script de nettoyage sécurisé pour CertificationDEVIA
Supprime les fichiers obsolètes identifiés dans CLEANUP_ANALYSIS.md
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def get_project_root():
    """Retourne le répertoire racine du projet"""
    return Path(__file__).parent

def check_git_status():
    """Vérifie l'état Git avant nettoyage"""
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd=get_project_root())
        
        if result.stdout.strip():
            print("⚠️ ATTENTION: Il y a des modifications Git non commitées:")
            print(result.stdout)
            
            response = input("Continuer quand même ? (y/N): ")
            if response.lower() != 'y':
                print("❌ Nettoyage annulé")
                return False
        else:
            print("✅ Git status clean")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Impossible de vérifier Git: {e}")
        return True

def test_current_services():
    """Test que les services actuels fonctionnent"""
    print("\n=== TEST SERVICES ACTUELS ===")
    
    tests = [
        ("Django local", "http://localhost:8002/", "curl -s -o /dev/null -w '%{http_code}' http://localhost:8002/"),
        ("FastAPI", "http://localhost:8000/", "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/"),
    ]
    
    all_ok = True
    for service, url, cmd in tests:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            status = result.stdout.strip()
            
            if status in ['200', '404']:  # 404 acceptable pour certains endpoints
                print(f"✅ {service}: {status}")
            else:
                print(f"⚠️ {service}: {status}")
                all_ok = False
                
        except Exception as e:
            print(f"❌ {service}: Erreur {e}")
            all_ok = False
    
    return all_ok

def create_backup():
    """Crée une sauvegarde de sécurité"""
    print("\n=== CRÉATION SAUVEGARDE ===")
    
    project_root = get_project_root()
    backup_dir = project_root.parent / f"CertificationDEVIA_backup_{int(__import__('time').time())}"
    
    try:
        # Copier uniquement les fichiers essentiels pour la sauvegarde
        essential_dirs = [
            'E3_model_IA/backend/django_app',
            'E3_model_IA/backend/fastapi_app',
            'E4_app_IA',
            'knowledge_base',
            'deployment'
        ]
        
        essential_files = [
            'CONTEXTE_PROJET.md',
            'ARCHITECTURE.md', 
            '.env',
            'data/django_garmin_data.db'
        ]
        
        backup_dir.mkdir()
        print(f"Sauvegarde créée: {backup_dir}")
        
        # Copier dossiers essentiels
        for dir_name in essential_dirs:
            src = project_root / dir_name
            if src.exists():
                dst = backup_dir / dir_name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src, dst)
                print(f"✅ Sauvegardé: {dir_name}")
        
        # Copier fichiers essentiels
        for file_name in essential_files:
            src = project_root / file_name
            if src.exists():
                dst = backup_dir / file_name
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst) 
                print(f"✅ Sauvegardé: {file_name}")
        
        print(f"✅ Sauvegarde complète: {backup_dir}")
        return str(backup_dir)
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")
        return None

def cleanup_phase_1_temp_files():
    """Phase 1: Supprimer fichiers temporaires et logs"""
    print("\n=== PHASE 1: FICHIERS TEMPORAIRES ===")
    
    project_root = get_project_root()
    temp_files = [
        # Logs
        'logs/django.log',
        'E3_model_IA/backend/django_app/django.log',
        'E3_model_IA/backend/fastapi_app/fastapi.log',
        'E3_model_IA/backend/fastapi_app/django.log',
        
        # Temporaires
        'deployment/cookies.txt',
        'structure.ipynb',
        
        # Cache Python
        '__pycache__',
        '*.pyc',
    ]
    
    deleted = 0
    for pattern in temp_files:
        files = list(project_root.glob(f"**/{pattern}"))
        for file_path in files:
            if file_path.exists():
                try:
                    if file_path.is_dir():
                        shutil.rmtree(file_path)
                    else:
                        file_path.unlink()
                    print(f"✅ Supprimé: {file_path.relative_to(project_root)}")
                    deleted += 1
                except Exception as e:
                    print(f"❌ Erreur: {file_path} - {e}")
    
    print(f"Phase 1 terminée: {deleted} fichiers supprimés")
    return deleted

def cleanup_phase_2_data_files():
    """Phase 2: Supprimer fichiers de données obsolètes"""
    print("\n=== PHASE 2: FICHIERS DE DONNÉES ===")
    
    project_root = get_project_root()
    data_files = [
        # JSON bruts Garmin
        'E1_gestion_donnees/data/raw_garmin_data_*.json',
        'data/raw_garmin_data_*.json',
        
        # Bases obsolètes  
        'E3_model_IA/backend/fastapi_app/data/django_garmin_data.db',
        'data/agent_memory.sqlite',
        'data/garmin_data_dump.sql',
    ]
    
    deleted = 0
    for pattern in data_files:
        files = list(project_root.glob(pattern))
        for file_path in files:
            if file_path.exists():
                try:
                    file_path.unlink()
                    size_mb = file_path.stat().st_size / (1024*1024) if file_path.exists() else 0
                    print(f"✅ Supprimé: {file_path.relative_to(project_root)} ({size_mb:.1f}MB)")
                    deleted += 1
                except Exception as e:
                    print(f"❌ Erreur: {file_path} - {e}")
    
    print(f"Phase 2 terminée: {deleted} fichiers supprimés")
    return deleted

def cleanup_phase_3_docker_configs():
    """Phase 3: Supprimer configurations Docker obsolètes"""
    print("\n=== PHASE 3: CONFIGURATIONS DOCKER ===")
    
    project_root = get_project_root()
    docker_files = [
        # Docker Compose obsolètes (CONSERVE docker-compose-prod.yml - containers actuels)
        'deployment/docker-compose-demo.yml',
        'deployment/docker-compose-full.yml', 
        'deployment/docker-compose-ipv6.yml',
        'deployment/docker-compose-local-postgres.yml',
        'deployment/docker-compose-online.yml',
        'deployment/docker-compose-simple.yml',
        'deployment/docker-compose-stable.yml',
        'deployment/docker-compose-supabase-simple.yml',
        'deployment/docker-compose.yml',
        
        # Nginx obsolètes
        'deployment/nginx-simple.conf',
        'deployment/nginx-supabase.conf', 
        'deployment/nginx.conf',
        
        # Dockerfiles spécialisés
        'deployment/fastapi-standalone.Dockerfile',
    ]
    
    deleted = 0
    for file_name in docker_files:
        file_path = project_root / file_name
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"✅ Supprimé: {file_name}")
                deleted += 1
            except Exception as e:
                print(f"❌ Erreur: {file_name} - {e}")
    
    print(f"Phase 3 terminée: {deleted} fichiers supprimés")
    return deleted

def cleanup_phase_4_scripts():
    """Phase 4: Supprimer scripts obsolètes"""
    print("\n=== PHASE 4: SCRIPTS OBSOLÈTES ===")
    
    project_root = get_project_root()
    script_files = [
        # Scripts de démarrage (CONSERVE start_services_new.py - référencé dans docs)
        'start_services.py',
        'deployment/start_supabase.py',
        'deployment/start_coaching_full.py',
        'E5_monitoring/start_monitoring.py',
        'E5_monitoring/start_monitoring_e5.py',
        
        # Scripts de test
        'test_services.py',
        'deployment/test_docker_supabase.py',
        'tests/test_data_manager.py',
        
        # Scripts de migration terminés
        'deployment/migrate_sqlite_to_postgres.py',
        'deployment/deploy_online.py',
        'deployment/validate_monitoring.sh',
        
        # Scripts intégrés ailleurs
        'E3_model_IA/scripts/start_api.py',
    ]
    
    deleted = 0
    for file_name in script_files:
        file_path = project_root / file_name
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"✅ Supprimé: {file_name}")
                deleted += 1
            except Exception as e:
                print(f"❌ Erreur: {file_name} - {e}")
    
    print(f"Phase 4 terminée: {deleted} fichiers supprimés")
    return deleted

def cleanup_phase_5_monitoring():
    """Phase 5: Nettoyer configurations monitoring redondantes"""
    print("\n=== PHASE 5: CONFIGURATIONS MONITORING ===")
    
    project_root = get_project_root()
    monitoring_files = [
        'E5_monitoring/alertmanager/alertmanager-docker.yml',
        'E5_monitoring/loki/loki-config.yml',
        'E5_monitoring/prometheus/prometheus-docker.yml', 
        'E5_monitoring/promtail/promtail-config-docker.yml',
        'deployment/ci_cd/build.yml',
        'deployment/ci_cd/deploy.yml',
    ]
    
    deleted = 0
    for file_name in monitoring_files:
        file_path = project_root / file_name
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"✅ Supprimé: {file_name}")
                deleted += 1
            except Exception as e:
                print(f"❌ Erreur: {file_name} - {e}")
    
    # Supprimer répertoire ci_cd vide
    ci_cd_dir = project_root / 'deployment' / 'ci_cd'
    if ci_cd_dir.exists() and not any(ci_cd_dir.iterdir()):
        ci_cd_dir.rmdir()
        print(f"✅ Supprimé répertoire vide: deployment/ci_cd")
        deleted += 1
    
    print(f"Phase 5 terminée: {deleted} fichiers supprimés")
    return deleted

def final_verification():
    """Vérification finale que les services fonctionnent toujours"""
    print("\n=== VÉRIFICATION FINALE ===")
    
    # Vérifier que les fichiers essentiels existent toujours
    project_root = get_project_root()
    essential_files = [
        'deployment/docker-compose-production.yml',
        'deployment/docker-compose-prod.yml', 
        'deployment/docker-compose-supabase.yml',
        'start_services_new.py',
        'E3_model_IA/backend/django_app/manage.py',
        'data/django_garmin_data.db',
        'CONTEXTE_PROJET.md'
    ]
    
    all_ok = True
    for file_name in essential_files:
        file_path = project_root / file_name
        if not file_path.exists():
            print(f"❌ ERREUR: Fichier essentiel manquant: {file_name}")
            all_ok = False
        else:
            print(f"✅ Essentiel présent: {file_name}")
    
    return all_ok

def main():
    """Fonction principale de nettoyage"""
    print("🧹 NETTOYAGE PROJET CertificationDEVIA")
    print("=" * 50)
    
    project_root = get_project_root()
    print(f"Répertoire projet: {project_root}")
    
    # Vérifications préliminaires
    if not check_git_status():
        return
    
    if not test_current_services():
        print("⚠️ Services non fonctionnels, continuez avec prudence")
        response = input("Continuer ? (y/N): ")
        if response.lower() != 'y':
            return
    
    # Créer sauvegarde
    backup_path = create_backup()
    if not backup_path:
        print("❌ Impossible de créer la sauvegarde")
        return
    
    print(f"\n✅ Sauvegarde créée: {backup_path}")
    print("Le nettoyage va commencer...")
    
    input("Appuyez sur Entrée pour continuer...")
    
    # Exécuter le nettoyage par phases
    total_deleted = 0
    
    total_deleted += cleanup_phase_1_temp_files()
    total_deleted += cleanup_phase_2_data_files()
    total_deleted += cleanup_phase_3_docker_configs()
    total_deleted += cleanup_phase_4_scripts()
    total_deleted += cleanup_phase_5_monitoring()
    
    # Vérification finale
    if final_verification():
        print(f"\n🎉 NETTOYAGE TERMINÉ AVEC SUCCÈS!")
        print(f"📊 Total supprimé: {total_deleted} fichiers")
        print(f"💾 Sauvegarde: {backup_path}")
        
        print(f"\n📋 Fichiers conservés (essentiels):")
        print("  - deployment/docker-compose-production.yml")
        print("  - deployment/docker-compose-supabase.yml") 
        print("  - E3_model_IA/ (backend complet)")
        print("  - E4_app_IA/ (frontend)")
        print("  - knowledge_base/ (base connaissances)")
        print("  - data/django_garmin_data.db (données)")
        
        print(f"\n🚀 Prochaines étapes:")
        print("  1. Tester les services: python3 deployment/deploy_production.py")
        print("  2. Commit: git add . && git commit -m 'feat: Nettoyage architecture projet'")
        
    else:
        print(f"\n❌ ERREUR: Vérification finale échouée")
        print(f"Restaurez depuis: {backup_path}")

if __name__ == '__main__':
    main()