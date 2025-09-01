import logging
import json
import numpy as np
from sqlalchemy import select
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from garminconnect import Garmin, GarminConnectAuthenticationError

import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
log = logging.getLogger(__name__)

from src.config import GARMIN_EMAIL, GARMIN_PASSWORD, DATA_DIR
from E1_gestion_donnees.db_manager import create_db_engine, create_tables, store_activities_in_db

def connect_garmin(email: str, password: str) -> Optional[Garmin]:
    try:
        log.info("Tentative de connexion à l'API Garmin Connect...")
        garmin = Garmin(email, password)
        garmin.login()
        log.info("Connexion à Garmin réussie.")
        return garmin
    except GarminConnectAuthenticationError as e:
        log.error(f"Échec de l'authentification Garmin : {e}")
        return None
    except Exception as e:
        log.error(f"Une erreur inattendue est survenue lors de la connexion à Garmin.", exc_info=True)
        return None


def get_all_garmin_activities(garmin: Garmin, batch_size: int = 100) -> List[Dict[str, Any]]:
    all_activities = []
    start_index = 0
    log.info(f"Début de la récupération des activités par lots de {batch_size}.")
    
    while True:
        try:
            log.info(f"Récupération du lot d'activités démarrant à l'index {start_index}...")
            activities_batch = garmin.get_activities(start_index, batch_size)
            
            if not activities_batch:
                log.info("Aucune nouvelle activité trouvée. Fin de la récupération.")
                break
            
            all_activities.extend(activities_batch)
            log.info(f"{len(activities_batch)} activités ajoutées. Total actuel : {len(all_activities)}.")
            start_index += batch_size
            
        except Exception as e:
            log.error(f"Erreur lors de la récupération du lot d'activités à l'index {start_index}.", exc_info=True)
            break
            
    if all_activities:
        first_date = all_activities[0].get('startTimeLocal')
        last_date = all_activities[-1].get('startTimeLocal')
        log.info(f"Récupération terminée. {len(all_activities)} activités trouvées, de {first_date} à {last_date}.")
        
    return all_activities

def process_garmin_activities(activities: List[Dict[str, Any]], user_id: int) -> List[Dict[str, Any]]:
    processed_data = []

    for activity in activities:
        processed_data.append({
            "user_id": user_id,
            "activity_id": activity.get("activityId"),
            "activity_name": activity.get("activityName"),
            "activity_type": activity.get("activityType", {}).get("typeKey"),
            "start_time": pd.to_datetime(activity.get("startTimeLocal")) if activity.get("startTimeLocal") else None,
            "distance_meters": activity.get("distance", 0.0),
            "duration_seconds": activity.get("duration", 0.0),
            "average_speed": activity.get("averageSpeed"),
            "max_speed": activity.get("maxSpeed"),
            "calories": activity.get("calories", 0.0),
            "average_hr": activity.get("averageHR"),
            "max_hr": activity.get("maxHR"),
            "elevation_gain": activity.get("elevationGain", 0.0),
            "elevation_loss": activity.get("elevationLoss", 0.0),
            "start_latitude": activity.get("startLatitude"),
            "start_longitude": activity.get("startLongitude"),
            "device_name": activity.get("deviceName"),
            "created_timestamp": datetime.now(),
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
    log.info(f"{len(processed_data)} activités ont été traitées et normalisées.")
    return processed_data

def save_raw_data(activities, filename=None):
    filename = DATA_DIR / f"raw_garmin_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(filename, "w") as f:
            json.dump(activities, f, indent=4)
        log.info(f"Données brutes sauvegardées avec succès dans {filename}")
        return str(filename)
    except Exception as e:
        log.error(f"Impossible de sauvegarder les données brutes dans {filename}.", exc_info=True)
        raise

def create_activities_dataframe(processed_data):
    df = pd.DataFrame(processed_data)
    return df

def fetch_and_process_garmin_data(user_id: int, save_raw: bool = True) -> Optional[Tuple[pd.DataFrame, List[Dict[str, Any]]]]:
    garmin_client = connect_garmin(GARMIN_EMAIL, GARMIN_PASSWORD)

    activities: List[Dict[str, Any]] = []
    if garmin_client:
        activities = get_all_garmin_activities(garmin_client)

    # Fallback robuste: charger un jeu d'exemple si login/collecte échoue
    if not activities:
        sample_path = Path(__file__).resolve().parent / "data" / "sample_garmin_activities.json"
        try:
            with open(sample_path, "r", encoding="utf-8") as f:
                activities = json.load(f)
            log.warning(
                f"Aucune activité récupérée depuis Garmin. Utilisation des données d'exemple: {sample_path.name}"
            )
        except Exception:
            log.error("Impossible de charger le fichier d'exemple de données Garmin.", exc_info=True)
            return None

    if save_raw:
        save_raw_data(activities)

    processed_data = process_garmin_activities(activities, user_id=user_id)
    df = pd.DataFrame(processed_data)

    return df, processed_data

def compute_performance_metrics(activities_df: pd.DataFrame, user_id: int) -> Dict[str, Any]:
    log.info(f"Début du calcul des métriques de performance pour l'utilisateur {user_id} à partir de {len(activities_df)} activités.")
    
    if activities_df.empty:
        log.warning("Le DataFrame d'activités est vide. Impossible de calculer les métriques.")
        return {}

    df = activities_df.copy()
    df['start_time'] = pd.to_datetime(df['start_time'])

    running_df = df[df['activity_type'] == 'running'].copy()
    if running_df.empty:
        log.warning("Aucune activité de 'running' trouvée. Certaines métriques ne seront pas calculées.")
    
    now = pd.Timestamp.now()

    vma_kmh = None
    vma_source = None
    if not running_df.empty:
        if 'fastest_split_1000' in running_df and running_df['fastest_split_1000'].notna().any():
            best_1000 = running_df['fastest_split_1000'].min()  # en secondes
            if best_1000 > 0:
                vma_kmh = 3600 / best_1000  # 1 km en best_1000 secondes → km/h
                vma_source = f"VMA estimée sur le meilleur 1000m : {round(vma_kmh,2)} km/h"
        if vma_kmh is None:
            long_efforts = running_df[running_df['duration_seconds'] >= 6*60]
            if not long_efforts.empty:
                best = long_efforts.loc[long_efforts['distance_meters'].idxmax()]
                vma_kmh = (best['distance_meters'] / best['duration_seconds']) * 3.6
                vma_source = f"Allure moyenne sur {round(best['duration_seconds']/60,1)} min, distance {round(best['distance_meters']/1000,2)} km"
        if vma_kmh is None:
            valid = running_df[running_df['duration_seconds'] >= 5*60]
            if not valid.empty and 'max_speed' in valid:
                vma_kmh = valid['max_speed'].max() * 3.6
                vma_source = "Vitesse max sur activité > 5 min"
    if vma_kmh:
        vma_kmh = round(vma_kmh, 2)
        log.info(f"VMA estimée : {vma_kmh} km/h ({vma_source})")
    else:
        log.warning("Impossible d'estimer la VMA (pas d'effort suffisant trouvé)")

    charge_28j_df = df[df['start_time'] >= now - pd.Timedelta(days=28)]
    charge_28j = charge_28j_df['training_load'].sum() if 'training_load' in charge_28j_df else 0.0

    charge_7j_df = df[df['start_time'] >= now - pd.Timedelta(days=7)]
    charge_7j = charge_7j_df['training_load'].sum() if 'training_load' in charge_7j_df else 0.0

    forme = charge_28j
    fatigue = charge_7j
    
    long_runs_count = (running_df['duration_seconds'] >= 45 * 60).sum() if not running_df.empty else 0
    total_runs_count = len(running_df)
    ratio_endurance = long_runs_count / total_runs_count if total_runs_count > 0 else None

    prediction_10k = None
    pred_source = None
    if not running_df.empty and 'fastest_split_10000' in running_df and running_df['fastest_split_10000'].notna().any():
        prediction_10k = running_df['fastest_split_10000'].min() / 60
        pred_source = "Meilleur split 10k"
    else:
        valid = running_df[running_df['distance_meters'] >= 5000]
        if not valid.empty:
            best = valid.loc[valid['duration_seconds'].idxmin()]
            t_ref_min = best['duration_seconds'] / 60
            d_ref_km = best['distance_meters'] / 1000
            if d_ref_km > 0:
                prediction_10k = t_ref_min * ((10 / d_ref_km) ** 1.06)
                pred_source = f"Extrapolation Riegel depuis {round(d_ref_km,2)} km en {round(t_ref_min,1)} min"
    if prediction_10k:
        prediction_10k = round(prediction_10k, 1)
        log.info(f"Prédiction 10k : {prediction_10k} min ({pred_source})")
    else:
        log.warning("Impossible d'estimer la prédiction 10k (pas de course suffisante)")

    reco = "Entraînement normal"
    if forme > 0 and (fatigue / (forme / 4)) > 1.5:  # On divise la forme par 4 pour avoir une charge hebdo moyenne
        reco = "Repos ou récupération conseillée."
    elif fatigue == 0:
        reco = "Nouveau cycle d'entraînement possible."

    metrics = {
        "user_id": user_id,
        "date_calcul": now,
        "vma_kmh": vma_kmh,
        "vo2max_estime": round(float(df['vo2max_estime'].max()), 1) if 'vo2max_estime' in df.columns and not df['vo2max_estime'].isnull().all() else None,
        "charge_7j": round(float(charge_7j), 1),
        "charge_28j": round(float(charge_28j), 1),
        "forme": round(float(forme), 1),
        "fatigue": round(float(fatigue), 1),
        "ratio_endurance": round(ratio_endurance, 2) if ratio_endurance is not None else None,
        "prediction_10k_min": prediction_10k,
        "recommandation_jour": reco
    }
    
    log.info(f"Métriques finales calculées pour l'utilisateur {user_id}: {metrics}")
    return metrics

def extract_splits_from_activities(activities):
    all_splits = []
    for activity in activities:
        activity_id = activity.get("activityId")
        split_summaries = activity.get("splitSummaries", [])
        if not activity_id or not split_summaries:
            continue
        for idx, split in enumerate(split_summaries):
            if not isinstance(split, dict):
                continue
            all_splits.append({
                "activity_id": activity_id,
                "split_index": idx,
                "split_type": split.get("splitType"),
                "duration_seconds": split.get("duration"),
                "distance_meters": split.get("distance"),
                "average_speed": split.get("averageSpeed"),
                "max_speed": split.get("maxSpeed"),
                "elevation_gain": split.get("totalAscent"),
                "elevation_loss": split.get("elevationLoss"),
            })
    return all_splits

def fetch_and_store_splits(garmin, engine, tables, activities):
    splits_table = tables["splits"]
    all_splits = extract_splits_from_activities(activities)
    if all_splits:
        with engine.begin() as conn:
            conn.execute(splits_table.insert(), all_splits)
        log.info(f"{len(all_splits)} splits insérés dans la table splits.")
    else:
        log.info("Aucun split à insérer (aucun splitSummaries trouvé dans les activités).")
