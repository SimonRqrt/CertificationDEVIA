"""
Gestion base de données simple
"""

import sys
import logging
from pathlib import Path
import sqlalchemy as sa
from fastapi import HTTPException, status

# Ajouter le chemin racine du projet
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(project_root))

from E1_gestion_donnees.db_manager import create_db_engine, create_tables

log = logging.getLogger(__name__)

# Variables globales
db_engine = None
db_tables = None

def init_database():
    """Initialiser la connexion base de données"""
    global db_engine, db_tables
    try:
        db_engine = create_db_engine()
        if db_engine:
            db_tables = create_tables(db_engine)
            log.info("✅ Base de données initialisée")
            return True
        else:
            log.warning("⚠️ Moteur base de données non créé")
            return False
    except Exception as e:
        log.error(f"❌ Erreur base de données: {e}")
        return False

def get_db_connection():
    """Obtenir une connexion base de données"""
    if db_engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de données non disponible"
        )
    return db_engine

def get_database_status() -> str:
    """Retourner le status de la base de données"""
    return "connected" if db_engine else "disconnected"