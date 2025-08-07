#!/usr/bin/env python3
"""
Connecteur PostgreSQL Django pour FastAPI
Remplace E1_gestion_donnees.db_manager pour utiliser la base unifiée
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

# Configuration logging
log = logging.getLogger(__name__)

class DjangoDBConnector:
    """Connecteur à la base PostgreSQL Django depuis FastAPI"""
    
    def __init__(self):
        # Configuration PostgreSQL (même que Django)
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'coach_ia_db'),
            'user': os.getenv('DB_USER', 'coach_user'),
            'password': os.getenv('DB_PASSWORD', 'coach_password')
        }
        
        self.database_url = f"postgresql://{self.db_config['user']}:{self.db_config['password']}@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
        self.engine = None
        self.SessionLocal = None
        
    def get_engine(self):
        """Créer ou récupérer l'engine SQLAlchemy"""
        if self.engine is None:
            try:
                self.engine = sa.create_engine(
                    self.database_url,
                    pool_pre_ping=True,
                    pool_timeout=30,
                    pool_recycle=3600,
                    connect_args={'application_name': 'fastapi_coach_ai'}
                )
                
                # Test de connexion
                with self.engine.connect() as conn:
                    conn.execute(sa.text("SELECT 1"))
                
                log.info("✅ Connexion PostgreSQL Django établie depuis FastAPI")
                
                # Créer session maker
                self.SessionLocal = sessionmaker(bind=self.engine)
                
            except Exception as e:
                log.error(f"❌ Erreur connexion PostgreSQL: {e}")
                raise
        
        return self.engine

    def get_session(self) -> Session:
        """Obtenir une session SQLAlchemy"""
        if self.SessionLocal is None:
            self.get_engine()
        return self.SessionLocal()

    def get_user_activities(self, user_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Récupérer les activités d'un utilisateur depuis PostgreSQL Django"""
        try:
            with self.get_session() as session:
                query = sa.text("""
                    SELECT 
                        a.id,
                        a.activity_id as garmin_id,
                        a.activity_name,
                        a.activity_type,
                        a.start_time,
                        a.duration_seconds,
                        a.distance_meters,
                        a.average_speed,
                        a.max_speed,
                        a.calories,
                        a.average_hr,
                        a.max_hr,
                        a.elevation_gain,
                        a.elevation_loss,
                        a.steps,
                        a.average_cadence,
                        a.vo2_max,
                        a.training_load,
                        a.aerobic_effect,
                        a.anaerobic_effect
                    FROM activities_activity a
                    WHERE a.user_id = :user_id
                    ORDER BY a.start_time DESC
                """ + (f" LIMIT {limit}" if limit else ""))
                
                result = session.execute(query, {"user_id": user_id})
                
                activities = []
                for row in result:
                    activity = {
                        'id': row.id,
                        'garmin_id': row.garmin_id,
                        'activity_name': row.activity_name,
                        'activity_type': row.activity_type,
                        'start_time': row.start_time,
                        'duration_seconds': row.duration_seconds,
                        'distance_meters': row.distance_meters,
                        'distance_km': round(row.distance_meters / 1000, 2) if row.distance_meters else 0,
                        'average_speed': row.average_speed,
                        'max_speed': row.max_speed,
                        'calories': row.calories,
                        'average_hr': row.average_hr,
                        'max_hr': row.max_hr,
                        'elevation_gain': row.elevation_gain,
                        'elevation_loss': row.elevation_loss,
                        'steps': row.steps,
                        'average_cadence': row.average_cadence,
                        'vo2_max': row.vo2_max,
                        'training_load': row.training_load,
                        'aerobic_effect': row.aerobic_effect,
                        'anaerobic_effect': row.anaerobic_effect,
                        'pace_per_km': self._calculate_pace(row.duration_seconds, row.distance_meters)
                    }
                    activities.append(activity)
                
                log.info(f"✅ Récupération {len(activities)} activités pour utilisateur {user_id}")
                return activities
                
        except Exception as e:
            log.error(f"❌ Erreur récupération activités: {e}")
            return []

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Calculer statistiques utilisateur depuis PostgreSQL Django"""
        try:
            with self.get_session() as session:
                # Statistiques générales
                stats_query = sa.text("""
                    SELECT 
                        COUNT(*) as total_activities,
                        SUM(distance_meters) as total_distance_meters,
                        SUM(duration_seconds) as total_duration_seconds,
                        SUM(calories) as total_calories,
                        AVG(average_hr) as avg_heart_rate,
                        MAX(distance_meters) as max_distance_meters,
                        MAX(duration_seconds) as max_duration_seconds
                    FROM activities_activity 
                    WHERE user_id = :user_id
                """)
                
                result = session.execute(stats_query, {"user_id": user_id}).fetchone()
                
                if result.total_activities == 0:
                    return {
                        'total_activities': 0,
                        'message': 'Aucune activité trouvée'
                    }
                
                # Répartition par type d'activité
                type_query = sa.text("""
                    SELECT 
                        activity_type,
                        COUNT(*) as count,
                        SUM(distance_meters) as total_distance
                    FROM activities_activity 
                    WHERE user_id = :user_id
                    GROUP BY activity_type
                    ORDER BY count DESC
                """)
                
                type_result = session.execute(type_query, {"user_id": user_id})
                activity_types = {
                    row.activity_type: {
                        'count': row.count,
                        'total_distance_km': round(row.total_distance / 1000, 2) if row.total_distance else 0
                    }
                    for row in type_result
                }
                
                stats = {
                    'total_activities': result.total_activities,
                    'total_distance_km': round(result.total_distance_meters / 1000, 2) if result.total_distance_meters else 0,
                    'total_duration_hours': round(result.total_duration_seconds / 3600, 1) if result.total_duration_seconds else 0,
                    'total_calories': result.total_calories or 0,
                    'avg_heart_rate': round(result.avg_heart_rate) if result.avg_heart_rate else None,
                    'max_distance_km': round(result.max_distance_meters / 1000, 2) if result.max_distance_meters else 0,
                    'max_duration_hours': round(result.max_duration_seconds / 3600, 1) if result.max_duration_seconds else 0,
                    'activity_types': activity_types
                }
                
                log.info(f"✅ Statistiques calculées pour utilisateur {user_id}")
                return stats
                
        except Exception as e:
            log.error(f"❌ Erreur calcul statistiques: {e}")
            return {'error': str(e)}

    def _calculate_pace(self, duration_seconds: Optional[float], distance_meters: Optional[float]) -> Optional[str]:
        """Calculer l'allure en min/km"""
        if not duration_seconds or not distance_meters or distance_meters <= 0:
            return None
        
        pace_seconds = (duration_seconds / distance_meters) * 1000
        minutes = int(pace_seconds // 60)
        seconds = int(pace_seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def test_connection(self) -> Dict[str, Any]:
        """Tester la connexion et retourner des informations"""
        try:
            with self.get_session() as session:
                # Test basique
                result = session.execute(sa.text("SELECT COUNT(*) as total FROM activities_activity")).fetchone()
                
                # Info base
                db_info = session.execute(sa.text("SELECT version()")).fetchone()
                
                return {
                    'status': 'connected',
                    'database_url': self.database_url.replace(self.db_config['password'], '***'),
                    'total_activities': result.total,
                    'database_version': db_info.version,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Instance globale
db_connector = DjangoDBConnector()