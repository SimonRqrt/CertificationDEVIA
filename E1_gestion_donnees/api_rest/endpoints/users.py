"""
Endpoints utilisateurs
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from utils.models import User
from utils.auth import verify_jwt_token
from utils.database import get_db_connection

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["Utilisateurs"])

@router.get("/", response_model=List[User])
def get_users(current_user: dict = Depends(verify_jwt_token)):
    """Récupérer tous les utilisateurs"""
    try:
        engine = get_db_connection()
        
        query = """
        SELECT user_id, nom, prenom, age 
        FROM users 
        ORDER BY user_id
        """
        
        with engine.connect() as conn:
            result = conn.execute(query)
            users = []
            
            for row in result:
                users.append({
                    "user_id": row[0],
                    "nom": row[1],
                    "prenom": row[2], 
                    "age": row[3]
                })
        
        log.info(f"Récupération de {len(users)} utilisateurs")
        return users
        
    except Exception as e:
        log.error(f"Erreur récupération utilisateurs: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération des utilisateurs"
        )

@router.get("/{user_id}", response_model=User)
def get_user(user_id: int, current_user: dict = Depends(verify_jwt_token)):
    """Récupérer un utilisateur par ID"""
    try:
        engine = get_db_connection()
        
        query = """
        SELECT user_id, nom, prenom, age 
        FROM users 
        WHERE user_id = ?
        """
        
        with engine.connect() as conn:
            result = conn.execute(query, (user_id,))
            row = result.fetchone()
            
            if not row:
                log.warning(f"Utilisateur {user_id} non trouvé")
                raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
            
            log.info(f"Récupération utilisateur {user_id}")
            return {
                "user_id": row[0],
                "nom": row[1],
                "prenom": row[2],
                "age": row[3]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Erreur récupération utilisateur {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erreur lors de la récupération de l'utilisateur"
        )