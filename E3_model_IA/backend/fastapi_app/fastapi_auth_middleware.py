from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging
import os
from django_auth_service import django_auth_service, UserInfo

logger = logging.getLogger(__name__)

# Configuration du schéma de sécurité
security = HTTPBearer()


class FastAPIAuthMiddleware:
    """Middleware d'authentification FastAPI avec Django"""
    
    def __init__(self):
        self.auth_service = django_auth_service
    
    async def get_current_user(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> UserInfo:
        """Récupérer l'utilisateur actuel depuis le token JWT"""
        
        if not credentials or not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token d'authentification manquant",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = credentials.credentials
        user_info = self.auth_service.authenticate_token(token)
        
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide ou utilisateur inactif",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_info
    
    async def get_current_user_optional(
        self, 
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
    ) -> Optional[UserInfo]:
        """Récupérer l'utilisateur actuel (optionnel)"""
        
        if not credentials or not credentials.credentials:
            return None
        
        token = credentials.credentials
        return self.auth_service.authenticate_token(token)
    
    async def get_current_premium_user(
        self, 
        current_user: UserInfo = Depends(lambda: auth_middleware.get_current_user)
    ) -> UserInfo:
        """Récupérer l'utilisateur actuel (premium uniquement)"""
        
        if not current_user.is_premium:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès réservé aux utilisateurs premium",
            )
        
        return current_user
    
    async def get_user_context(
        self, 
        current_user: UserInfo = Depends(lambda: auth_middleware.get_current_user)
    ) -> Dict[str, Any]:
        """Récupérer le contexte utilisateur pour le coaching"""
        
        context = self.auth_service.get_user_context_for_coaching(current_user.id)
        
        if not context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Impossible de récupérer le contexte utilisateur",
            )
        
        return context
    
    def create_coaching_session(
        self, 
        user_id: int, 
        session_data: Dict[str, Any]
    ) -> Optional[int]:
        """Créer une session de coaching"""
        
        try:
            session_id = self.auth_service.create_coaching_session(user_id, session_data)
            return session_id
        except Exception as e:
            logger.error(f"Erreur lors de la création de la session: {e}")
            return None


# Instance globale du middleware
auth_middleware = FastAPIAuthMiddleware()

# Dépendances réutilisables - Export des fonctions directement
# Pour utiliser avec Depends() dans les endpoints
get_current_user = auth_middleware.get_current_user

get_current_user_optional = auth_middleware.get_current_user_optional
get_current_premium_user = Depends(auth_middleware.get_current_premium_user)
get_user_context = Depends(auth_middleware.get_user_context)


# Fonctions utilitaires
def extract_user_id_from_request(request) -> Optional[int]:
    """Extraire l'ID utilisateur depuis une requête FastAPI"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        user_info = django_auth_service.authenticate_token(token)
        
        return user_info.id if user_info else None
        
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction de l'ID utilisateur: {e}")
        return None


def validate_api_key_fallback(api_key: str) -> bool:
    """Validation de clé API en fallback (pour compatibilité)"""
    expected_api_key = os.getenv("API_KEY", "default_key")
    return api_key == expected_api_key