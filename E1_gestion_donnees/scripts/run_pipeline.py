# E1_gestion_donnees/scripts/run_pipeline.py

import sys
import os
import logging
import argparse
from pathlib import Path

# NOTE: C'est une solution temporaire. La meilleure pratique est de rendre
# le projet installable avec un fichier pyproject.toml et `pip install -e .`
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# --- Imports de votre logique métier ---
# MODIFICATION: On importe les nouvelles fonctions et dépendances
from E1_gestion_donnees.data_manager import fetch_and_process_garmin_data, compute_performance_metrics
from E1_gestion_donnees.db_manager import (
    create_db_engine, 
    create_tables, 
    store_activities_in_db,
    store_metrics_in_db  # NOTE: Fonction à créer dans db_manager.py
)
from src.config import USER_ID, LOG_LEVEL

# --- Configuration du Logging ---
# Le logger est maintenant configuré avec le niveau venant du fichier config.py
logging.basicConfig(
    level=LOG_LEVEL.upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / "E1_gestion_donnees/data/logs/pipeline_run.log"),
        logging.StreamHandler()
    ]
)
# On récupère le logger spécifique pour notre application
log = logging.getLogger(__name__)


def run_garmin_data_pipeline(user: int):
    """
    Exécute l'ensemble du pipeline de données Garmin pour un utilisateur donné.
    Ce script orchestre un processus en deux temps :
    1. ETL (Extract-Transform-Load) des activités brutes.
    2. Calcul et stockage des métriques de performance agrégées.
    
    Args:
        user (int): L'identifiant de l'utilisateur pour lequel exécuter le pipeline.
    """
    try:
        log.info(f"Démarrage du pipeline de données Garmin pour l'utilisateur ID: {user}...")
        
        # --- ÉTAPE 1: EXTRACTION ET TRANSFORMATION DES ACTIVITÉS ---
        log.info("Étape 1/4: Récupération et traitement des données depuis la source Garmin.")
        
        # data_manager est maintenant découplé et retourne les données traitées
        processed_result = fetch_and_process_garmin_data(user_id=user, save_raw=True)
        
        if processed_result is None:
            log.error("Aucune donnée n'a été récupérée ou traitée. Arrêt du pipeline.")
            return

        activities_df, processed_activities = processed_result
        log.info(f"DataFrame créé avec succès, contenant {len(activities_df)} activités.")
        
        # --- ÉTAPE 2: STOCKAGE DES ACTIVITÉS TRAITÉES ---
        log.info("Étape 2/4: Connexion à la base de données et stockage des activités.")
        engine = create_db_engine()
        tables = create_tables(engine)  # Assure que les tables existent
        store_activities_in_db(engine, tables, processed_activities)
        log.info("Activités stockées avec succès dans la base de données.")
        
        # --- ÉTAPE 3: CALCUL DES MÉTRIQUES DE PERFORMANCE ---
        log.info("Étape 3/4: Calcul des métriques de performance agrégées.")
        metrics_data = compute_performance_metrics(activities_df=activities_df, user_id=user)

        if not metrics_data:
            log.warning("Le calcul des métriques n'a retourné aucune donnée. Étape de stockage des métriques ignorée.")
        else:
            # --- ÉTAPE 4: STOCKAGE DES MÉTRIQUES CALCULÉES ---
            log.info("Étape 4/4: Stockage des métriques calculées dans la base de données.")
            store_metrics_in_db(engine, tables, metrics_data)
            log.info("Mètriques stockées avec succès.")

        log.info("Pipeline de données Garmin terminé avec succès.")
        
    except Exception as e:
        log.error(f"Une erreur critique est survenue lors de l'exécution du pipeline.", exc_info=True)
        # En production, on pourrait vouloir que le script se termine avec un code d'erreur non-nul
        # pour que les outils de CI/CD détectent l'échec.
        # raise e

def main():
    """Point d'entrée principal du script."""
    parser = argparse.ArgumentParser(description="Pipeline de traitement des données Garmin.")
    parser.add_argument(
        '--user-id', 
        type=int, 
        default=USER_ID,
        help=f"L'ID de l'utilisateur à traiter (défaut: {USER_ID} depuis le fichier de config)."
    )
    args = parser.parse_args()
    
    run_garmin_data_pipeline(user=args.user_id)

if __name__ == "__main__":
    main()