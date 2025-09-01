import logging
import json
from datetime import datetime
import pandas as pd
from pathlib import Path
from src.config import DATA_DIR, LOG_LEVEL

def setup_logger(name="garmin_data", level=LOG_LEVEL):
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    log_dir = DATA_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"{datetime.now().strftime('%Y%m%d')}.log"
    
    logger = logging.getLogger(name)
    logger.setLevel(log_levels.get(level, logging.INFO))
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_levels.get(level, logging.INFO))
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_levels.get(level, logging.INFO))
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logger()

def export_to_csv(df, filename=None):
    if filename is None:
        csv_dir = DATA_DIR / "exports"
        csv_dir.mkdir(exist_ok=True)
        filename = csv_dir / f"garmin_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    df.to_csv(filename, index=False)
    logger.info(f"Données exportées vers {filename}")
    return filename

def load_json_file(file_path):
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Erreur lors du chargement du fichier JSON {file_path}: {e}")
        return None

def calculate_statistics(df):
    stats = {
        "total_activities": len(df),
        "activity_types": df["activity_type"].value_counts().to_dict(),
        "total_distance": df["distance_meters"].sum(),
        "total_duration": df["duration_seconds"].sum(),
        "avg_speed": df["average_speed"].mean(),
        "total_calories": df["calories"].sum(),
        "avg_heart_rate": df["average_hr"].mean()
    }
    
    stats["stats_by_type"] = {}
    for activity_type in df["activity_type"].unique():
        type_df = df[df["activity_type"] == activity_type]
        stats["stats_by_type"][activity_type] = {
            "count": len(type_df),
            "total_distance": type_df["distance_meters"].sum(),
            "total_duration": type_df["duration_seconds"].sum(),
            "avg_speed": type_df["average_speed"].mean(),
            "total_calories": type_df["calories"].sum(),
        }
    
    return stats

def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

def format_distance(meters):
    return f"{meters / 1000:.2f} km"

def format_speed(speed):
    return f"{speed * 3.6:.2f} km/h"

def format_activity_summary(activity):
    return {
        "name": activity["activity_name"],
        "type": activity["activity_type"],
        "date": activity["start_time"],
        "distance": format_distance(activity["distance_meters"]),
        "duration": format_duration(activity["duration_seconds"]),
        "speed": format_speed(activity["average_speed"]),
        "calories": activity["calories"]
    }

def summarize_activities(activities):
    return [format_activity_summary(activity) for activity in activities]