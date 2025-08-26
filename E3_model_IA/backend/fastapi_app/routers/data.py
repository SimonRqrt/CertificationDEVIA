"""
Router pour les endpoints de données utilisateur
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Optional

router = APIRouter(prefix="/v1", tags=["Données"])

@router.get("/activities/{user_id}")
async def get_user_activities(
    user_id: int,
    limit: Optional[int] = 20,
    request: Request = None
):
    """Récupérer les activités d'un utilisateur depuis PostgreSQL Django"""
    try:
        db_connector = request.app.state.db_connector
        activities = db_connector.get_user_activities(user_id, limit=limit)
        
        return {
            "user_id": user_id,
            "total_returned": len(activities),
            "activities": activities
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération activités: {str(e)}")

@router.get("/stats/{user_id}") 
async def get_user_stats(
    user_id: int,
    request: Request = None
):
    """Obtenir les statistiques d'un utilisateur depuis PostgreSQL Django"""
    try:
        db_connector = request.app.state.db_connector
        stats = db_connector.get_user_stats(user_id)
        
        return {
            "user_id": user_id,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur calcul statistiques: {str(e)}")

@router.get("/database/status", tags=["Système"])
async def database_status(request: Request = None):
    """Vérifier le statut de la connexion PostgreSQL Django"""
    try:
        db_connector = request.app.state.db_connector
        status = db_connector.test_connection()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur test connexion: {str(e)}")