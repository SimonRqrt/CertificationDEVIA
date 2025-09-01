"""
Endpoints activités
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from E1_gestion_donnees.api_rest.utils.models import Activity, ActivityResponse, PaginatedResponse
from E1_gestion_donnees.api_rest.utils.auth import verify_jwt_token
from E1_gestion_donnees.api_rest.utils.database import get_db_connection

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/activities", tags=["Activités"])

@router.get("/", response_model=PaginatedResponse)
def get_activities(
    page: int = 1,
    per_page: int = 10,
    user_id: int = None,
    activity_type: str = None,
    current_user: dict = Depends(verify_jwt_token)
):
    """Récupérer les activités avec pagination"""
    try:
        engine = get_db_connection()
        offset = (page - 1) * per_page
        
        # Construction de la requête avec filtres
        where_conditions = []
        params = []
        
        if user_id:
            where_conditions.append("user_id = ?")
            params.append(user_id)
        
        if activity_type:
            where_conditions.append("activity_type = ?")
            params.append(activity_type)
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Compter le total
        count_query = f"SELECT COUNT(*) FROM activities{where_clause}"
        
        # Récupérer les données
        query = f"""
        SELECT id, user_id, activity_name, activity_type, start_time,
               duration_seconds, distance_meters, average_hr, calories
        FROM activities{where_clause}
        ORDER BY start_time DESC
        LIMIT ? OFFSET ?
        """
        
        params.extend([per_page, offset])
        
        with engine.connect() as conn:
            # Total
            total = conn.execute(count_query, params[:-2] if where_conditions else []).scalar()
            
            # Données
            result = conn.execute(query, params)
            activities = []
            
            for row in result:
                activities.append({
                    "id": row[0],
                    "user_id": row[1],
                    "activity_name": row[2],
                    "activity_type": row[3],
                    "start_time": row[4],
                    "duration_seconds": row[5],
                    "distance_meters": row[6],
                    "average_hr": row[7],
                    "calories": row[8],
                    "distance_km": round(row[6] / 1000, 2),
                    "duration_formatted": f"{row[5] // 3600:02d}:{(row[5] % 3600) // 60:02d}:{row[5] % 60:02d}"
                })
        
        log.info(f"Récupération de {len(activities)} activités (page {page})")
        return {
            "items": activities,
            "total": total,
            "page": page,
            "per_page": per_page
        }
        
    except Exception as e:
        log.error(f"Erreur récupération activités: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération des activités"
        )

@router.post("/", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(
    activity: Activity,
    current_user: dict = Depends(verify_jwt_token)
):
    """Créer une nouvelle activité"""
    try:
        engine = get_db_connection()
        
        query = """
        INSERT INTO activities (
            user_id, activity_name, activity_type, start_time,
            duration_seconds, distance_meters, average_hr, calories
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        values = (
            activity.user_id,
            activity.activity_name,
            activity.activity_type,
            activity.start_time,
            activity.duration_seconds,
            activity.distance_meters,
            activity.average_hr,
            activity.calories
        )
        
        with engine.connect() as conn:
            trans = conn.begin()
            try:
                result = conn.execute(query, values)
                trans.commit()
            except Exception:
                trans.rollback()
                raise
            
            new_id = result.lastrowid
            
            # Retourner l'activité créée
            log.info(f"Activité créée avec ID {new_id} pour utilisateur {activity.user_id}")
            return {
                "id": new_id,
                "user_id": activity.user_id,
                "activity_name": activity.activity_name,
                "activity_type": activity.activity_type,
                "start_time": activity.start_time,
                "duration_seconds": activity.duration_seconds,
                "distance_meters": activity.distance_meters,
                "average_hr": activity.average_hr,
                "calories": activity.calories,
                "distance_km": round(activity.distance_meters / 1000, 2),
                "duration_formatted": f"{activity.duration_seconds // 3600:02d}:{(activity.duration_seconds % 3600) // 60:02d}:{activity.duration_seconds % 60:02d}"
            }
        
    except Exception as e:
        log.error(f"Erreur création activité: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la création de l'activité"
        )

@router.get("/{activity_id}", response_model=ActivityResponse)
def get_activity(
    activity_id: int,
    current_user: dict = Depends(verify_jwt_token)
):
    """Récupérer une activité par ID"""
    try:
        engine = get_db_connection()
        
        query = """
        SELECT id, user_id, activity_name, activity_type, start_time,
               duration_seconds, distance_meters, average_hr, calories
        FROM activities
        WHERE id = ?
        """
        
        with engine.connect() as conn:
            result = conn.execute(query, (activity_id,))
            row = result.fetchone()
            
            if not row:
                log.warning(f"Activité {activity_id} non trouvée")
                raise HTTPException(status_code=404, detail="Activité non trouvée")
            
            log.info(f"Récupération activité {activity_id}")
            return {
                "id": row[0],
                "user_id": row[1],
                "activity_name": row[2],
                "activity_type": row[3],
                "start_time": row[4],
                "duration_seconds": row[5],
                "distance_meters": row[6],
                "average_hr": row[7],
                "calories": row[8],
                "distance_km": round(row[6] / 1000, 2),
                "duration_formatted": f"{row[5] // 3600:02d}:{(row[5] % 3600) // 60:02d}:{row[5] % 60:02d}"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Erreur récupération activité {activity_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération de l'activité"
        )