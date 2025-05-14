import sys
from pathlib import Path

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from E3_model_IA.api_service import start_api
from E1_gestion_donnees.src.utils import logger

if __name__ == "__main__":
    logger.info("Démarrage de l'API REST...")
    start_api()