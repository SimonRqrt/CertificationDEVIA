#!/usr/bin/env python3
"""
Script pour démarrer les services Django et FastAPI
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

# Configuration
DJANGO_PORT = 8002
FASTAPI_PORT = 8000
STREAMLIT_PORT = 8501

BASE_DIR = Path(__file__).resolve().parent

def start_django():
    """Démarrer le serveur Django"""
    print(f"🚀 Démarrage de Django sur le port {DJANGO_PORT}")
    
    # S'assurer que les migrations sont appliquées
    subprocess.run([
        sys.executable, "manage.py", "migrate", "--noinput"
    ], cwd=BASE_DIR)
    
    # Démarrer le serveur Django
    subprocess.run([
        sys.executable, "manage.py", "runserver", f"0.0.0.0:{DJANGO_PORT}"
    ], cwd=BASE_DIR)

def start_fastapi():
    """Démarrer le serveur FastAPI"""
    print(f"🚀 Démarrage de FastAPI sur le port {FASTAPI_PORT}")
    
    # Attendre que Django soit prêt
    time.sleep(5)
    
    # Démarrer le serveur FastAPI
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "E3_model_IA.api_service:app", 
        "--host", "0.0.0.0", 
        "--port", str(FASTAPI_PORT),
        "--reload"
    ], cwd=BASE_DIR)

def start_streamlit():
    """Démarrer l'application Streamlit"""
    print(f"🚀 Démarrage de Streamlit sur le port {STREAMLIT_PORT}")
    
    # Attendre que les APIs soient prêtes
    time.sleep(10)
    
    # Démarrer Streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", 
        "E4_app_IA/ui/app_streamlit.py",
        "--server.port", str(STREAMLIT_PORT),
        "--server.address", "0.0.0.0"
    ], cwd=BASE_DIR)

def signal_handler(signum, frame):
    """Gestionnaire pour arrêter proprement les services"""
    print("\n🛑 Arrêt des services...")
    sys.exit(0)

def main():
    """Fonction principale"""
    print("🎯 Démarrage des services Coach AI...")
    print(f"📊 Django Admin: http://localhost:{DJANGO_PORT}/admin/")
    print(f"🔗 Django API: http://localhost:{DJANGO_PORT}/api/v1/")
    print(f"🤖 FastAPI: http://localhost:{FASTAPI_PORT}/docs")
    print(f"💻 Streamlit: http://localhost:{STREAMLIT_PORT}/")
    print(f"📚 API Docs: http://localhost:{DJANGO_PORT}/swagger/")
    
    # Configuration des signaux
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Démarrer les services en parallèle
    threads = []
    
    # Django
    django_thread = threading.Thread(target=start_django)
    django_thread.daemon = True
    threads.append(django_thread)
    
    # FastAPI
    fastapi_thread = threading.Thread(target=start_fastapi)
    fastapi_thread.daemon = True
    threads.append(fastapi_thread)
    
    # Streamlit
    streamlit_thread = threading.Thread(target=start_streamlit)
    streamlit_thread.daemon = True
    threads.append(streamlit_thread)
    
    # Démarrer tous les threads
    for thread in threads:
        thread.start()
    
    # Attendre que tous les threads se terminent
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\n🛑 Arrêt demandé par l'utilisateur")
        sys.exit(0)

if __name__ == "__main__":
    main()