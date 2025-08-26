"""
Configuration sécurité et authentification
"""

import logging
from fastapi import HTTPException, Depends, Request, Security
from fastapi.security.api_key import APIKeyHeader

from config.settings import EXPECTED_API_KEY, API_KEY_NAME, SECURITY_LOG_FILE

# Import conditionnel de slowapi
try:
    from slowapi.util import get_remote_address
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False
    def get_remote_address(request: Request):
        return request.client.host if request.client else "unknown"

# Configuration logging sécurité
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)
security_handler = logging.FileHandler(SECURITY_LOG_FILE)
security_formatter = logging.Formatter('%(asctime)s - SECURITY - %(levelname)s - %(message)s')
security_handler.setFormatter(security_formatter)
security_logger.addHandler(security_handler)

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(request: Request, key: str = Security(api_key_header)):
    """Vérifie la clé API fournie dans les en-têtes avec logging sécurité."""
    client_ip = get_remote_address(request)
    
    if key == EXPECTED_API_KEY:
        security_logger.info(f"Authentification API réussie - IP: {client_ip}")
        return key
    else:
        security_logger.warning(f"Tentative d'authentification échouée - IP: {client_ip}, Key: {key}")
        raise HTTPException(status_code=403, detail="Clé API invalide ou manquante.")