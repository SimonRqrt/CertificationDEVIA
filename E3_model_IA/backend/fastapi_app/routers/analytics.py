"""
Router pour les endpoints d'analytics avancés
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime
from config.security import get_api_key

router = APIRouter(prefix="/v1/analytics", tags=["Analytics E1"])

def get_performance_trends_data(engine, user_id: int, period_weeks: int = 12):
    """Analyse des tendances de performance avec moyennes mobiles"""
    from sqlalchemy import text
    
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
        COALESCE(training_load, 0) as training_load
    FROM activities 
    WHERE user_id = :user_id 
      AND start_time >= datetime('now', '-' || :weeks || ' days')
      AND duration_seconds > 600  -- Au moins 10 minutes
    ORDER BY start_time DESC
    LIMIT 50
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query, {'user_id': user_id, 'weeks': period_weeks * 7})
        trends = [dict(row._mapping) for row in result]
    
    return {
        'user_id': user_id,
        'period_weeks': period_weeks,
        'trends_count': len(trends),
        'trends': trends
    }

def get_zones_analysis_data(engine, user_id: int):
    """Analyse des zones d'entraînement basée sur la FC"""
    from sqlalchemy import text
    
    # D'abord, récupérer la FC max
    max_hr_query = text("""
    SELECT MAX(max_hr) as max_hr_recorded,
           COUNT(*) as activities_with_hr
    FROM activities 
    WHERE user_id = :user_id AND max_hr IS NOT NULL
    """)
    
    zones_query = text("""
    SELECT 
        CASE 
            WHEN average_hr <= (SELECT MAX(max_hr) * 0.7 FROM activities WHERE user_id = :user_id AND max_hr IS NOT NULL) 
                THEN 'Zone 1-2 - Endurance'
            WHEN average_hr <= (SELECT MAX(max_hr) * 0.85 FROM activities WHERE user_id = :user_id AND max_hr IS NOT NULL) 
                THEN 'Zone 3-4 - Tempo/Seuil'
            ELSE 'Zone 5 - VO2max'
        END as hr_zone,
        COUNT(*) as activities_count,
        ROUND(AVG(duration_seconds)/60.0, 1) as avg_duration_min,
        ROUND(AVG(average_hr), 0) as avg_hr
    FROM activities 
    WHERE user_id = :user_id 
      AND average_hr IS NOT NULL 
      AND duration_seconds > 300
    GROUP BY 1
    ORDER BY avg_hr
    """)
    
    with engine.connect() as conn:
        max_hr_result = conn.execute(max_hr_query, {'user_id': user_id}).fetchone()
        zones_result = conn.execute(zones_query, {'user_id': user_id})
        zones = [dict(row._mapping) for row in zones_result]
    
    max_hr_info = dict(max_hr_result._mapping) if max_hr_result else {}
    
    return {
        'user_id': user_id,
        'max_hr_info': max_hr_info,
        'zones_analysis': zones
    }

@router.get("/trends/{user_id}")
async def get_performance_trends(
    user_id: int,
    request: Request,
    period_weeks: int = 12,
    api_key: str = Depends(get_api_key)
):
    """Analyse des tendances de performance (SQLAlchemy E1)"""
    
    engine = request.app.state.analytics_engine
    if not engine:
        raise HTTPException(status_code=503, detail="Moteur analytics non disponible")
    
    try:
        trends = get_performance_trends_data(engine, user_id, period_weeks)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analytics trends: {str(e)}")

@router.get("/zones/{user_id}")
async def get_training_zones_analysis(
    user_id: int,
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """Analyse des zones d'entraînement FC (SQLAlchemy E1)"""
    
    engine = request.app.state.analytics_engine
    if not engine:
        raise HTTPException(status_code=503, detail="Moteur analytics non disponible")
    
    try:
        zones_analysis = get_zones_analysis_data(engine, user_id)
        return zones_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analytics zones: {str(e)}")

@router.get("/dashboard/{user_id}")
async def get_analytics_dashboard(
    user_id: int,
    request: Request,
    period_weeks: int = 12,
    api_key: str = Depends(get_api_key)
):
    """Dashboard complet analytics (SQLAlchemy E1)"""
    
    engine = request.app.state.analytics_engine
    if not engine:
        raise HTTPException(status_code=503, detail="Moteur analytics non disponible")
    
    try:
        dashboard_data = {
            'user_id': user_id,
            'period_weeks': period_weeks,
            'generated_at': datetime.now().isoformat(),
        }
        
        # Récupérer les analyses
        try:
            dashboard_data['trends'] = get_performance_trends_data(engine, user_id, period_weeks)
        except Exception as e:
            dashboard_data['trends'] = {'error': str(e)}
            
        try:
            dashboard_data['zones'] = get_zones_analysis_data(engine, user_id)
        except Exception as e:
            dashboard_data['zones'] = {'error': str(e)}
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur dashboard analytics: {str(e)}")