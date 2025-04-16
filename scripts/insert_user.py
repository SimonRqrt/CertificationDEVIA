import sys
import os
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.db_manager import create_db_engine, create_tables, insert_user
from src.utils import logger

if __name__ == "__main__":
    engine = create_db_engine()
    tables = create_tables(engine)

    user = {
        "nom": "Durand",
        "prenom": "Simon",
        "age": 30,
        "sexe": "Homme",
        "taille_cm": 187,
        "poids_kg": 90.0,
        "niveau": "Intermédiaire",
        "objectif_type": "10km",
        "objectif_temps": "00:50:00",
        "disponibilite": "['Lundi', 'Mercredi', 'Samedi']",
        "blessures": "aucune",
        "terrain_prefere": "Route",
        "frequence_semaine": 3
    }

    insert_user(engine, tables, user)
