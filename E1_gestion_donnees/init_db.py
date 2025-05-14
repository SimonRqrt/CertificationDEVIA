import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Mise à jour des chemins d'importation en fonction de la nouvelle structure
from E1_gestion_donnees.db_manager import create_db_engine, create_tables  # Import mis à jour
from src.utils import logger  # Mise à jour du chemin pour le logger

def initialize_database():
    """Initialise la base de données et crée les tables nécessaires"""
    try:
        logger.info("Initialisation de la base de données...")
        
        engine = create_db_engine()
        tables = create_tables(engine)
        
        logger.info("Base de données initialisée avec succès !")
        logger.info(f"Tables créées : {', '.join(tables.keys()) if tables else 'Aucune table créée'}")
        
        return True
    except (ConnectionError, ValueError) as e:
        logger.error(f"Erreur spécifique lors de l'initialisation de la base de données : {e}")
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'initialisation de la base de données : {e}")
    return False

if __name__ == "__main__":
    initialize_database()
