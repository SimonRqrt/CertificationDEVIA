import os
import json
from datetime import datetime
import pandas as pd
from garminconnect import Garmin
from .config import GARMIN_EMAIL, GARMIN_PASSWORD, DATA_DIR

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
        activities = garmin.get_activities(0, limit)
        print(f"Activités récupérées: {activities}")
        return activities
    except Exception as e:
        print(f"Erreur lors de la récupération des activités: {e}")
        return []

def process_garmin_activities(activities):
    """Traite et structure les données d'activités Garmin"""
    processed_data = []
    
    for activity in activities:
        # Extraire les champs pertinents
        activity_data = {
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
            "created_timestamp": datetime.now().isoformat()
        }
        processed_data.append(activity_data)
    
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

def fetch_and_process_garmin_data(save_raw=True):
    """Fonction principale pour récupérer et traiter les données Garmin"""
    try:
        garmin_client = connect_garmin()
        if not garmin_client:
            print("Impossible de se connecter à Garmin")
            return None, None
        
        activities = get_garmin_activities(garmin_client, limit=500)
        print(f"Récupération de {len(activities)} activités réussie")
        
        if save_raw:
            save_raw_data(activities)
        
        processed_data = process_garmin_activities(activities)
        df = create_activities_dataframe(processed_data)
        
        return df, processed_data
    except Exception as e:
        print(f"Erreur lors de la récupération des données Garmin: {e}")
        return None, None