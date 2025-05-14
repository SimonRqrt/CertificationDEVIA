import os
import json
import numpy as np
from sqlalchemy import select
from datetime import datetime, timedelta
import pandas as pd
from garminconnect import Garmin

# Ajouter le chemin racine du projet au PYTHONPATH
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from src.config import GARMIN_EMAIL, GARMIN_PASSWORD, DATA_DIR
from E1_gestion_donnees.db_manager import create_db_engine, create_tables, store_activities_in_db

def connect_garmin(email=GARMIN_EMAIL, password=GARMIN_PASSWORD):
    """Établit une connexion avec l'API Garmin Connect"""
    try:
        garmin = Garmin(email, password)
        garmin.login()
        print("Connexion à Garmin réussie")
        return garmin
    except Exception as e:
        print(f"Erreur de connexion à Garmin: {e}")
        return None

def get_garmin_activities(garmin, limit=10):
    """Récupère les activités récentes de Garmin Connect"""
    try:
        # Augmenter la limite pour récupérer plus d'activités
        activities = garmin.get_activities(0, 1000)  # Changé de 10 à 1000
        print(f"Nombre d'activités récupérées: {len(activities)}")
        # Afficher les dates des premières et dernières activités pour debug
        if activities:
            print(f"Date première activité: {activities[0].get('startTimeLocal')}")
            print(f"Date dernière activité: {activities[-1].get('startTimeLocal')}")
        return activities
    except Exception as e:
        print(f"Erreur lors de la récupération des activités: {e}")
        return []

def process_garmin_activities(activities, user_id):
    """Transforme les données d'activités Garmin en format base enrichi"""
    processed_data = []

    for activity in activities:
        processed_data.append({
            "user_id": user_id,
            "activity_id": activity.get("activityId"),
            "activity_name": activity.get("activityName"),
            "activity_type": activity.get("activityType", {}).get("typeKey"),
            "start_time": activity.get("startTimeLocal"),
            "distance_meters": activity.get("distance"),
            "duration_seconds": activity.get("duration"),
            "average_speed": activity.get("averageSpeed"),
            "max_speed": activity.get("maxSpeed"),
            "calories": activity.get("calories"),
            "average_hr": activity.get("averageHR"),
            "max_hr": activity.get("maxHR"),
            "elevation_gain": activity.get("elevationGain"),
            "elevation_loss": activity.get("elevationLoss"),
            "start_latitude": activity.get("startLatitude"),
            "start_longitude": activity.get("startLongitude"),
            "device_name": activity.get("deviceName"),
            "created_timestamp": datetime.now().isoformat(),
            # Champs enrichis
            "steps": activity.get("steps"),
            "average_running_cadence": activity.get("averageRunningCadenceInStepsPerMinute"),
            "max_running_cadence": activity.get("maxRunningCadenceInStepsPerMinute"),
            "stride_length": activity.get("avgStrideLength"),
            "vo2max_estime": activity.get("vO2MaxValue"),
            "training_load": activity.get("activityTrainingLoad"),
            "aerobic_effect": activity.get("aerobicTrainingEffect"),
            "anaerobic_effect": activity.get("anaerobicTrainingEffect"),
            "temp_min": activity.get("minTemperature"),
            "temp_max": activity.get("maxTemperature"),
            "fastest_split_5000": activity.get("fastestSplit_5000"),
            "fastest_split_10000": activity.get("fastestSplit_10000"),
            "hr_zone_1": activity.get("hrTimeInZone_1"),
            "hr_zone_2": activity.get("hrTimeInZone_2"),
            "hr_zone_3": activity.get("hrTimeInZone_3"),
            "hr_zone_4": activity.get("hrTimeInZone_4"),
            "hr_zone_5": activity.get("hrTimeInZone_5"),
        })

    return processed_data

def save_raw_data(activities, filename=None):
    """Sauvegarde les données brutes au format JSON"""
    if filename is None:
        filename = f"{DATA_DIR}/raw_garmin_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, "w") as f:
        json.dump(activities, f, indent=4)
    print(f"Données brutes sauvegardées dans {filename}")
    return filename

def create_activities_dataframe(processed_data):
    """Convertit les données structurées en DataFrame pandas"""
    df = pd.DataFrame(processed_data)
    return df

def fetch_and_process_garmin_data(user_id, save_raw=True):
    """Fonction principale pour récupérer et traiter les données Garmin"""
    try:
        garmin_client = connect_garmin()
        if not garmin_client:
            print("Impossible de se connecter à Garmin")
            return None, None

        activities = get_garmin_activities(garmin_client)
        if not activities:
            print("Aucune activité récupérée")
            return None, None

        print(f"Récupération de {len(activities)} activités réussie")

        if save_raw:
            save_raw_data(activities)

        processed_data = process_garmin_activities(activities, user_id=user_id)
        df = create_activities_dataframe(processed_data)

        print(f"Tentative de sauvegarde de {len(processed_data)} activités dans la BDD")

        engine = create_db_engine()
        tables = create_tables(engine)
        store_activities_in_db(engine, tables, processed_data)

        return df, processed_data
    except Exception as e:
        print(f"Erreur lors de la récupération des données Garmin: {e}")
        return None, None

def compute_metrics(user_id):
    """Calcule des métriques enrichies à partir des activités Garmin"""
    engine = create_db_engine()
    tables = create_tables(engine)

    with engine.connect() as conn:
        stmt = select(tables["activities"]).where(tables["activities"].c.user_id == user_id)
        result = conn.execute(stmt).mappings().fetchall()

        if not result:
            print("Aucune activité pour cet utilisateur.")
            return

        now = datetime.now()
        vo2_list = []
        training_loads = []
        total_duration = 0
        long_runs = 0
        speeds = []
        durations = []
        distances = []
        fastest_10k = None

        for row in result:
            duration = row["duration_seconds"]
            distance = row["distance_meters"]
            training_load = row.get("training_load")
            vo2 = row.get("vo2max_estime")
            speed = row.get("max_speed")

            if duration:
                durations.append(duration)
                total_duration += duration
                if duration >= 45 * 60:
                    long_runs += 1
            if distance:
                distances.append(distance)
            if training_load:
                training_loads.append((row["start_time"], training_load))
            if vo2:
                vo2_list.append(vo2)
            if speed:
                speeds.append(speed)
            if not fastest_10k and row.get("fastest_split_10000"):
                fastest_10k = row["fastest_split_10000"] / 60  # en minutes

        # VMA et VO2max
        vo2max_estimee = max(vo2_list) if vo2_list else None
        vma_kmh = max(speeds) * 1.1 if speeds else None  # simple estimation

        # Charge d'entraînement
        charge_7j = sum(load for date_str, load in training_loads
                        if datetime.fromisoformat(date_str) >= now - timedelta(days=7))
        charge_28j = sum(load for date_str, load in training_loads
                         if datetime.fromisoformat(date_str) >= now - timedelta(days=28))

        forme = charge_28j
        fatigue = charge_7j

        # Ratio endurance
        ratio_endurance = long_runs / len(durations) if durations else None

        # Prédiction 10K (fallback sur extrapolation)
        prediction_10k = fastest_10k
        if not prediction_10k and durations and distances:
            t_ref = min(durations) / 60
            d_ref = min(distances) / 1000
            if d_ref and d_ref < 10:
                prediction_10k = t_ref * (10 / d_ref) ** 1.06

        # Recommandation de base
        reco = "Repos conseillé, charge élevée." if fatigue > 1.5 * forme else "Poursuis le plan actuel."

        insert_stmt = tables["metrics"].insert().values(
            user_id=user_id,
            date_calcul=datetime.now().isoformat(),
            vma_kmh=round(vma_kmh, 2) if vma_kmh else None,
            vo2max_estime=round(vo2max_estimee, 1) if vo2max_estimee else None,
            zone_fc=None,
            charge_7j=round(charge_7j, 1),
            charge_28j=round(charge_28j, 1),
            forme=round(forme, 1),
            fatigue=round(fatigue, 1),
            tendance_progression=None,  # à implémenter plus tard
            ratio_endurance=round(ratio_endurance, 2) if ratio_endurance else None,
            prediction_10k_min=round(prediction_10k, 1) if prediction_10k else None,
            recommandation_jour=reco
        )

        conn.execute(insert_stmt)
        conn.commit()
        print("✅ Métriques enrichies calculées et insérées.")
