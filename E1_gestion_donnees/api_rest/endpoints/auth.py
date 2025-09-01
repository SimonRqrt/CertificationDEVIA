"""
Endpoints d'authentification
"""

from fastapi import APIRouter, HTTPException
from E1_gestion_donnees.api_rest.utils.models import LoginRequest, Token
from E1_gestion_donnees.api_rest.utils.auth import verify_credentials, create_jwt_token

router = APIRouter(prefix="/auth", tags=["Authentification"])

@router.post("/login", response_model=Token)
def login(credentials: LoginRequest):
    """Connexion utilisateur avec JWT"""
    user_info = verify_credentials(credentials.username, credentials.password)
    
    token = create_jwt_token(
        username=user_info["username"],
        role=user_info["role"]
    )
    
    return {"access_token": token}