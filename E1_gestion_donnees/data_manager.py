import logging
import json
import numpy as np
from sqlalchemy import select
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from garminconnect import Garmin, GarminConnectAuthenticationError

# Ajouter le chemin racine du projet au PYTHONPATH
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
log = logging.getLogger(__name__)

from src.config import GARMIN_EMAIL, GARMIN_PASSWORD, DATA_DIR
from E1_gestion_donnees.db_manager import create_db_engine, create_tables, store_activities_in_db

def connect_garmin(email: str, password: str) -> Optional[Garmin]:
    """
    Établit une connexion sécurisée avec l'API Garmin Connect.

    Args:
        email (str): L'email de l'utilisateur Garmin.
        password (str): Le mot de passe de l'utilisateur Garmin.

    Returns:
        Optional[Garmin]: Une instance de l'objet Garmin si la connexion réussit, sinon None.
    """
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
    """
    Récupère TOUTES les activités d'un compte Garmin en gérant la pagination.

    Args:
        garmin (Garmin): Le client Garmin authentifié.
        batch_size (int): Le nombre d'activités à récupérer par appel API.

    Returns:
        List[Dict[str, Any]]: Une liste de toutes les activités récupérées.
    """
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
    """
    Transforme la liste d'activités brutes en un format structuré et enrichi.

    Cette fonction nettoie et mappe les champs de l'API Garmin vers le schéma
    de notre base de données.

    Args:
        activities (List[Dict[str, Any]]): La liste d'activités brutes de l'API.
        user_id (int): L'ID de l'utilisateur à associer à ces activités.

    Returns:
        List[Dict[str, Any]]: Une liste d'activités prêtes à être stockées.
    """
    processed_data = []

    for activity in activities:
        processed_data.append({
            "user_id": user_id,
            "activity_id": activity.get("activityId"),
            "activity_name": activity.get("activityName"),
            "activity_type": activity.get("activityType", {}).get("typeKey"),
            "start_time": activity.get("startTimeLocal"),
            "distance_meters": activity.get("distance",0.0),
            "duration_seconds": activity.get("duration",0.0),
            "average_speed": activity.get("averageSpeed"),
            "max_speed": activity.get("maxSpeed"),
            "calories": activity.get("calories",0.0),
            "average_hr": activity.get("averageHR"),
            "max_hr": activity.get("maxHR"),
            "elevation_gain": activity.get("elevationGain",0.0),
            "elevation_loss": activity.get("elevationLoss",0.0),
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
    log.info(f"{len(processed_data)} activités ont été traitées et normalisées.")
    return processed_data

def save_raw_data(activities, filename=None):
    """
    Sauvegarde les données brutes de l'API dans un fichier JSON horodaté.
    C'est une bonne pratique pour l'audit et le débogage.

    Args:
        activities (List[Dict[str, Any]]): Les données brutes à sauvegarder.

    Returns:
        str: Le chemin du fichier sauvegardé.
    """
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
    """Convertit les données structurées en DataFrame pandas"""
    df = pd.DataFrame(processed_data)
    return df

def fetch_and_process_garmin_data(user_id: int, save_raw: bool = True) -> Optional[Tuple[pd.DataFrame, List[Dict[str, Any]]]]:
    """
    Orchestre la récupération et le traitement des données Garmin.
    Ne gère PAS le stockage.

    Args:
        user_id (int): L'ID de l'utilisateur à traiter.
        save_raw (bool): Si True, sauvegarde les données brutes dans un fichier JSON.

    Returns:
        Optional[Tuple[pd.DataFrame, List[Dict[str, Any]]]]: 
        Un tuple contenant le DataFrame et la liste des données traitées, ou None si une erreur survient.
    """
    garmin_client = connect_garmin(GARMIN_EMAIL, GARMIN_PASSWORD)
    if not garmin_client:
        log.error("Échec de l'orchestration : la connexion à Garmin a échoué.")
        return None

    activities = get_all_garmin_activities(garmin_client)
    if not activities:
        log.warning("Aucune activité n'a été récupérée pour ce compte.")
        return None

    if save_raw:
        save_raw_data(activities)

    processed_data = process_garmin_activities(activities, user_id=user_id)
    df = pd.DataFrame(processed_data)

    return df, processed_data

def compute_performance_metrics(activities_df: pd.DataFrame, user_id: int) -> Dict[str, Any]:
    """
    Calcule des métriques de performance agrégées à partir d'un DataFrame d'activités.
    Cette fonction est PURE : elle ne lit/écrit pas en base de données.

    Args:
        activities_df (pd.DataFrame): Le DataFrame contenant l'historique des activités.
        user_id (int): L'ID de l'utilisateur.

    Returns:
        Dict[str, Any]: Un dictionnaire contenant les métriques calculées.
    """
    log.info(f"Début du calcul des métriques de performance pour l'utilisateur {user_id} à partir de {len(activities_df)} activités.")
    
    if activities_df.empty:
        log.warning("Le DataFrame d'activités est vide. Impossible de calculer les métriques.")
        return {}

    # --- Pré-requis : Nettoyage et conversion de types ---
    # S'assure que la colonne de date est bien au format datetime pour les comparaisons
    df = activities_df.copy() # Travailler sur une copie pour éviter les SettingWithCopyWarning
    df['start_time'] = pd.to_datetime(df['start_time'])

    # Filtrer uniquement les activités de course à pied pour les métriques spécifiques
    running_df = df[df['activity_type'] == 'running'].copy()
    if running_df.empty:
        log.warning("Aucune activité de 'running' trouvée. Certaines métriques ne seront pas calculées.")
    
    now = pd.Timestamp.now()

    # --- 1. Indicateurs de performance (VMA & VO2max) ---
    # Logique : Basée sur les valeurs maximales enregistrées lors des courses.
    vo2max_estimee = df['vo2max_estime'].max() if 'vo2max_estime' in df.columns and not df['vo2max_estime'].isnull().all() else None
    
    # La vitesse est en m/s, on la convertit en km/h (* 3.6)
    vma_kmh = (running_df['max_speed'].max() * 3.6) * 1.1 if not running_df.empty and 'max_speed' in running_df else None
    
    # --- 2. Charge d'entraînement (modèle TSB simplifié) ---
    # Logique : Somme des charges d'entraînement sur des périodes glissantes.
    # Charge chronique (Forme) sur 28 jours
    charge_28j_df = df[df['start_time'] >= now - pd.Timedelta(days=28)]
    charge_28j = charge_28j_df['training_load'].sum() if 'training_load' in charge_28j_df else 0.0

    # Charge aiguë (Fatigue) sur 7 jours
    charge_7j_df = df[df['start_time'] >= now - pd.Timedelta(days=7)]
    charge_7j = charge_7j_df['training_load'].sum() if 'training_load' in charge_7j_df else 0.0

    # Pour la certification, nommons explicitement la forme et la fatigue
    forme = charge_28j
    fatigue = charge_7j
    
    # --- 3. Profil d'endurance ---
    # Logique : Ratio entre le nombre de sorties longues et le nombre total de sorties.
    long_runs_count = (running_df['duration_seconds'] >= 45 * 60).sum() if not running_df.empty else 0
    total_runs_count = len(running_df)
    ratio_endurance = long_runs_count / total_runs_count if total_runs_count > 0 else None

    # --- 4. Prédiction de performance (10k) ---
    # Logique : Utilise le meilleur temps enregistré sur 10km. Si non disponible,
    # tente une extrapolation à partir de la meilleure performance sur une autre distance.
    prediction_10k = None
    if not running_df.empty and 'fastest_split_10000' in running_df and running_df['fastest_split_10000'].notna().any():
        # Le temps est en secondes, on le veut en minutes
        prediction_10k = running_df['fastest_split_10000'].min() / 60
    else:
        # Fallback : Modèle de Riegel simplifié si pas de 10k enregistré
        # On prend la meilleure performance (plus courte distance en moins de temps possible)
        if not running_df.empty and running_df['distance_meters'].notna().all() and running_df['duration_seconds'].notna().all():
            running_df['allure_s_par_m'] = running_df['duration_seconds'] / running_df['distance_meters']
            best_perf = running_df.loc[running_df['allure_s_par_m'].idxmin()]
            t_ref_min = best_perf['duration_seconds'] / 60
            d_ref_km = best_perf['distance_meters'] / 1000
            if d_ref_km > 0:
                 # Formule de Riegel : T2 = T1 * (D2/D1)^1.06
                prediction_10k = t_ref_min * ((10 / d_ref_km) ** 1.06)

    # --- 5. Recommandation du jour ---
    # Logique : Règle métier simple basée sur le ratio fatigue/forme.
    # Un ratio > 1.5 peut indiquer un risque de surentraînement.
    reco = "Entraînement normal"
    if forme > 0 and (fatigue / (forme / 4)) > 1.5: # On divise la forme par 4 pour avoir une charge hebdo moyenne
        reco = "Repos ou séance de récupération conseillée (fatigue élevée)."
    elif fatigue == 0:
        reco = "Prêt à commencer un nouveau cycle d'entraînement."

    # --- Assemblage final du dictionnaire de métriques ---
    # On s'assure que les valeurs sont des types JSON-compatibles (pas de np.float64)
    # et on arrondit pour la lisibilité.
    metrics = {
        "user_id": user_id,
        "date_calcul": now.isoformat(),
        "vma_kmh": round(vma_kmh, 2) if vma_kmh else None,
        "vo2max_estime": round(float(vo2max_estimee), 1) if vo2max_estimee and pd.notna(vo2max_estimee) else None,
        "charge_7j": round(float(charge_7j), 1),
        "charge_28j": round(float(charge_28j), 1),
        "forme": round(float(forme), 1),
        "fatigue": round(float(fatigue), 1),
        "ratio_endurance": round(ratio_endurance, 2) if ratio_endurance is not None else None,
        "prediction_10k_min": round(prediction_10k, 1) if prediction_10k else None,
        "recommandation_jour": reco
    }
    
    log.info(f"Métriques finales calculées pour l'utilisateur {user_id}: {metrics}")
    return metrics
