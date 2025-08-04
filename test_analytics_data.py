#!/usr/bin/env python3
"""
Script pour insérer des données de test dans E1 pour démontrer les capacités analytics.
Solution minimale pour Phase 1 - Démonstration des endpoints analytics.
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3

# Ajouter le chemin du projet
project_root = Path(__file__).resolve().parent
sys.path.append(str(project_root))

from E1_gestion_donnees.db_manager import create_db_engine, create_tables

def insert_sample_activities():
    """Insère des activités d'exemple pour tester les analytics"""
    
    engine = create_db_engine()
    tables = create_tables(engine)
    
    # Données d'exemple réalistes pour 3 mois d'activités
    base_date = datetime.now() - timedelta(days=90)
    sample_activities = []
    
    # Simuler 30 activités sur 3 mois pour user_id=1
    for i in range(30):
        # Progression réaliste sur 3 mois
        days_offset = i * 3  # Une activité tous les 3 jours
        activity_date = base_date + timedelta(days=days_offset)
        
        # Progression dans la performance (pace qui s'améliore)
        base_pace_kmh = 11.0 + (i * 0.1)  # De 11 à 14 km/h sur 3 mois
        distance_km = 5.0 + (i * 0.2)    # De 5 à 11 km
        duration_min = (distance_km / base_pace_kmh) * 60
        
        # HR zones variées (120-180 bpm)
        avg_hr = 140 + (i % 20)  # Variabilité
        max_hr = avg_hr + 20
        
        # Training load progressif
        training_load = 50 + (i * 2)  # De 50 à 110
        
        activity = {
            'user_id': 1,
            'activity_id': 1000000 + i,
            'activity_name': f'Course matinale #{i+1}',
            'activity_type': 'running',
            'start_time': activity_date.isoformat(),
            'distance_meters': distance_km * 1000,
            'duration_seconds': duration_min * 60,
            'average_speed': base_pace_kmh / 3.6,  # m/s
            'max_speed': (base_pace_kmh + 2) / 3.6,  # m/s
            'calories': int(distance_km * 60),  # ~60 cal/km
            'average_hr': avg_hr,
            'max_hr': max_hr,
            'elevation_gain': 20 + (i % 50),  # Variabilité d'élévation
            'elevation_loss': 15 + (i % 40),
            'training_load': training_load,
            'created_timestamp': datetime.now().isoformat()
        }
        sample_activities.append(activity)
    
    # Insérer les données
    activities_table = tables['activities']
    
    print(f"Insertion de {len(sample_activities)} activités d'exemple...")
    
    with engine.begin() as conn:
        # Nettoyer les données existantes pour user_id=1
        conn.execute(activities_table.delete().where(activities_table.c.user_id == 1))
        
        # Insérer les nouvelles données
        conn.execute(activities_table.insert(), sample_activities)
    
    print(f"✅ {len(sample_activities)} activités insérées avec succès pour l'utilisateur 1")
    print(f"📊 Plage de dates: {sample_activities[0]['start_time'][:10]} à {sample_activities[-1]['start_time'][:10]}")
    print(f"🏃 Progression pace: {11.0:.1f} km/h → {base_pace_kmh:.1f} km/h")
    print(f"📏 Distance: 5.0 km → {distance_km:.1f} km")
    
    return len(sample_activities)

if __name__ == "__main__":
    insert_sample_activities()