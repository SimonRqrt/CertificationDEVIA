"""
Service Analytics utilisant SQLAlchemy E1 pour des requêtes complexes
impossible avec Django ORM seul
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import text, func, case, and_, or_
from fastapi import HTTPException
import logging

# Ajouter le chemin vers E1
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.append(str(project_root))

from E1_gestion_donnees.db_manager import create_db_engine, create_tables

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service d'analytics avancées utilisant SQLAlchemy E1"""
    
    def __init__(self):
        self.engine = create_db_engine()
        self.tables = create_tables(self.engine)
        
    def get_performance_trends(self, user_id: int, period_weeks: int = 12) -> Dict[str, Any]:
        """
        Analyse des tendances de performance avec moyennes mobiles
        Impossible avec Django ORM - Nécessite des window functions
        """
        
        # Adapter la requête selon le type de base de données
        query = text("""
        SELECT 
            start_time,
            distance_meters/1000.0 as distance_km,
            duration_seconds/60.0 as duration_min,
            CASE 
                WHEN duration_seconds > 0 THEN (distance_meters/duration_seconds) * 3.6 
                ELSE 0 
            END as pace_kmh,
            average_hr,
            COALESCE(training_load, 0) as training_load,
            -- Moyennes mobiles sur 7 activités (compatible SQLite)
            AVG(CASE 
                WHEN duration_seconds > 0 THEN (distance_meters/duration_seconds) * 3.6 
                ELSE 0 
            END) OVER (
                ORDER BY start_time 
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) as pace_trend_7_activities,
            -- Charge d'entraînement cumulative
            SUM(COALESCE(training_load, 0)) OVER (
                ORDER BY start_time 
                ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
            ) as cumulative_load_7_activities,
            -- Évolution de la FC au repos (estimation)
            MIN(COALESCE(average_hr, 0)) OVER (
                ORDER BY start_time 
                ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
            ) as min_hr_14_activities
        FROM activities 
        WHERE user_id = :user_id 
          AND start_time >= datetime('now', '-' || :weeks || ' days')
          AND duration_seconds > 600  -- Au moins 10 minutes
        ORDER BY start_time DESC
        LIMIT 50
        """)
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute(query, {'user_id': user_id, 'weeks': period_weeks})
                trends = [dict(row._mapping) for row in result]
                
            return {
                'user_id': user_id,
                'period_weeks': period_weeks,
                'trends_count': len(trends),
                'trends': trends,
                'analysis': self._analyze_trends(trends) if trends else {}
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des tendances pour user {user_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Erreur analytics: {str(e)}")
    
    def get_training_zones_analysis(self, user_id: int) -> Dict[str, Any]:
        """
        Analyse sophistiquée des zones d'entraînement basée sur la FC
        Utilise des CASE complexes impossibles avec Django ORM
        """
        
        # D'abord, récupérer la FC max estimée
        max_hr_query = text("""
        SELECT MAX(max_hr) as max_hr_recorded,
               AVG(max_hr) as avg_max_hr,
               COUNT(*) as activities_with_hr
        FROM activities 
        WHERE user_id = :user_id AND max_hr IS NOT NULL
        """)
        
        zones_query = text("""
        WITH hr_zones AS (
            SELECT 
                *,
                -- Définition des zones basée sur FC max estimée
                CASE 
                    WHEN average_hr <= (SELECT MAX(max_hr) * 0.6 FROM activities WHERE user_id = :user_id AND max_hr IS NOT NULL) 
                        THEN 'Zone 1 - Récupération active'
                    WHEN average_hr <= (SELECT MAX(max_hr) * 0.7 FROM activities WHERE user_id = :user_id AND max_hr IS NOT NULL) 
                        THEN 'Zone 2 - Endurance fondamentale'
                    WHEN average_hr <= (SELECT MAX(max_hr) * 0.8 FROM activities WHERE user_id = :user_id AND max_hr IS NOT NULL) 
                        THEN 'Zone 3 - Tempo/Seuil aérobie'
                    WHEN average_hr <= (SELECT MAX(max_hr) * 0.9 FROM activities WHERE user_id = :user_id AND max_hr IS NOT NULL) 
                        THEN 'Zone 4 - Seuil anaérobie'
                    ELSE 'Zone 5 - Puissance/VO2max'
                END as hr_zone,
                (distance_meters/duration_seconds) * 3.6 as pace_kmh
            FROM activities 
            WHERE user_id = :user_id 
              AND average_hr IS NOT NULL 
              AND duration_seconds > 300
        )
        SELECT 
            hr_zone,
            COUNT(*) as activities_count,
            ROUND(AVG(duration_seconds)/60.0, 1) as avg_duration_min,
            ROUND(SUM(duration_seconds)/3600.0, 1) as total_hours,
            ROUND(AVG(training_load), 1) as avg_training_load,
            ROUND(AVG(pace_kmh), 2) as avg_pace_kmh,
            ROUND(MIN(average_hr), 0) as min_hr,
            ROUND(MAX(average_hr), 0) as max_hr,
            ROUND(AVG(average_hr), 0) as avg_hr
        FROM hr_zones
        GROUP BY hr_zone
        ORDER BY 
            CASE hr_zone
                WHEN 'Zone 1 - Récupération active' THEN 1
                WHEN 'Zone 2 - Endurance fondamentale' THEN 2  
                WHEN 'Zone 3 - Tempo/Seuil aérobie' THEN 3
                WHEN 'Zone 4 - Seuil anaérobie' THEN 4
                WHEN 'Zone 5 - Puissance/VO2max' THEN 5
            END
        """)
        
        try:
            with self.engine.connect() as conn:
                # FC max info
                max_hr_result = conn.execute(max_hr_query, {'user_id': user_id}).fetchone()
                
                # Analyse des zones
                zones_result = conn.execute(zones_query, {'user_id': user_id})
                zones = [dict(row._mapping) for row in zones_result]
                
            max_hr_info = dict(max_hr_result._mapping) if max_hr_result else {}
            
            return {
                'user_id': user_id,
                'max_hr_info': max_hr_info,
                'zones_analysis': zones,
                'recommendations': self._generate_zone_recommendations(zones)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des zones pour user {user_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Erreur analytics zones: {str(e)}")
    
    def get_performance_predictions(self, user_id: int) -> Dict[str, Any]:
        """
        Prédictions de performance basées sur l'historique
        Utilise des calculs complexes avec pandas impossible avec Django ORM
        """
        
        # Récupérer les données via SQLAlchemy pour pandas
        query = text("""
        SELECT 
            distance_meters/1000.0 as distance_km,
            duration_seconds/60.0 as duration_min,
            (distance_meters/duration_seconds) * 3.6 as pace_kmh,
            average_hr,
            max_hr,
            training_load,
            start_time
        FROM activities 
        WHERE user_id = :user_id 
          AND distance_meters >= 3000  -- Au moins 3km
          AND duration_seconds > 600
        ORDER BY start_time DESC
        LIMIT 100
        """)
        
        try:
            # Utiliser pandas pour des calculs avancés
            df = pd.read_sql(query, self.engine, params={'user_id': user_id})
            
            if df.empty:
                return {'error': 'Pas assez de données pour les prédictions'}
            
            # Calculs prédictifs complexes
            predictions = self._calculate_predictions(df)
            
            return {
                'user_id': user_id,
                'data_points': len(df),
                'predictions': predictions,
                'confidence_metrics': self._calculate_confidence(df)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors des prédictions pour user {user_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Erreur prédictions: {str(e)}")
    
    def _analyze_trends(self, trends: List[Dict]) -> Dict[str, Any]:
        """Analyse les tendances pour donner des insights"""
        if not trends:
            return {}
            
        # Analyse de la progression
        recent_pace = sum(t['pace_kmh'] for t in trends[:5]) / 5  # 5 dernières
        older_pace = sum(t['pace_kmh'] for t in trends[-5:]) / 5  # 5 plus anciennes
        
        pace_improvement = ((recent_pace - older_pace) / older_pace * 100) if older_pace > 0 else 0
        
        return {
            'pace_improvement_percent': round(pace_improvement, 2),
            'recent_avg_pace_kmh': round(recent_pace, 2),
            'trend': 'improving' if pace_improvement > 2 else 'stable' if pace_improvement > -2 else 'declining'
        }
    
    def _generate_zone_recommendations(self, zones: List[Dict]) -> List[str]:
        """Génère des recommandations basées sur la répartition des zones"""
        if not zones:
            return ["Pas assez de données pour des recommandations"]
            
        recommendations = []
        
        # Calculer répartition
        total_hours = sum(z['total_hours'] for z in zones)
        
        for zone in zones:
            zone_percentage = (zone['total_hours'] / total_hours * 100) if total_hours > 0 else 0
            
            if 'Zone 1' in zone['hr_zone'] and zone_percentage < 20:
                recommendations.append("Augmentez le volume en Zone 1 (récupération) pour améliorer l'endurance de base")
            elif 'Zone 5' in zone['hr_zone'] and zone_percentage > 15:
                recommendations.append("Réduisez le temps en Zone 5 (haute intensité) pour éviter le surentraînement")
                
        if not recommendations:
            recommendations.append("Répartition des zones d'entraînement équilibrée ✅")
            
        return recommendations
    
    def _calculate_predictions(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calcule les prédictions de performance avec pandas"""
        
        # VMA estimation (meilleur km/h sur 6+ minutes)
        long_runs = df[df['duration_min'] >= 6]
        vma_kmh = long_runs['pace_kmh'].max() if not long_runs.empty else df['pace_kmh'].max()
        
        # Prédictions Riegel (formule classique)
        predictions = {}
        for distance, name in [(5, '5K'), (10, '10K'), (21.1, 'Semi-Marathon'), (42.2, 'Marathon')]:
            if vma_kmh and vma_kmh > 0:
                # Temps de référence (estimé sur 10K à 85% VMA)
                ref_time_10k = (10 / (vma_kmh * 0.85)) * 60  # en minutes
                
                # Formule de Riegel adaptée
                predicted_time = ref_time_10k * ((distance / 10) ** 1.06)
                
                predictions[name] = {
                    'predicted_time_minutes': round(predicted_time, 1),
                    'predicted_time_formatted': f"{int(predicted_time//60)}:{int(predicted_time%60):02d}",
                    'target_pace_kmh': round(distance / (predicted_time / 60), 2)
                }
        
        return {
            'estimated_vma_kmh': round(vma_kmh, 2) if vma_kmh else None,
            'race_predictions': predictions
        }
    
    def _calculate_confidence(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calcule des métriques de confiance pour les prédictions"""
        
        return {
            'data_consistency': float(1 - df['pace_kmh'].std() / df['pace_kmh'].mean()) if df['pace_kmh'].mean() > 0 else 0,
            'recent_activity_score': min(1.0, len(df) / 50),  # Score basé sur le nombre d'activités
            'pace_stability': float(1 - df['pace_kmh'].rolling(5).std().mean() / df['pace_kmh'].mean()) if len(df) >= 5 else 0.5
        }