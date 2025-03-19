import sys
from pathlib import Path

# Ajouter le répertoire parent au chemin de recherche des modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.api_service import start_api
from src.utils import logger

if __name__ == "__main__":
    logger.info("Démarrage de l'API REST...")
    start_api()