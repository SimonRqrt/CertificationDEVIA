"""
Service d'authentification réutilisable
"""

from config.security import get_api_key

class AuthService:
    """Service centralisé pour l'authentification"""
    
    @staticmethod
    async def verify_api_key(request, key):
        """Wrapper pour la vérification de clé API"""
        return await get_api_key(request, key)