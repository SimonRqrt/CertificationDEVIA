import sys
from pathlib import Path
import os

# Ajouter le répertoire racine du projet au chemin de recherche des modules
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

# Utiliser des imports absolus
from E1_gestion_donnees.data_manager import fetch_and_process_garmin_data, get_garmin_activities
from E1_gestion_donnees.db_manager import create_db_engine, create_tables, store_activities_in_db
from E3_model_IA.api_service import start_api

def run_garmin_data_pipeline():
    """Exécute l'ensemble du pipeline de données Garmin"""
    try:
        print("Démarrage du pipeline de données Garmin...")
        user = 1
        # 1. Récupération et traitement des données
        df, processed_data = fetch_and_process_garmin_data(user_id=user, save_raw=True)
        
        if df is None or processed_data is None:
            print("Erreur lors de la récupération des données. Arrêt du pipeline.")
            return
        
        print(f"DataFrame créé avec {len(df)} activités")
        
        # 2. Stockage dans la base de données
        engine = create_db_engine()
        tables = create_tables(engine)
        store_activities_in_db(engine, tables, processed_data)
        print("Données stockées dans la base de données")
        
        # 3. Optionnel : démarrer l'API
        start_api_server = input("Voulez-vous démarrer l'API REST ? (o/n): ").lower() == 'o'
        if start_api_server:
            print("Démarrage de l'API REST...")
            start_api()
        
    except Exception as e:
        print(f"Erreur lors de l'exécution du pipeline: {e}")

if __name__ == "__main__":
    run_garmin_data_pipeline()