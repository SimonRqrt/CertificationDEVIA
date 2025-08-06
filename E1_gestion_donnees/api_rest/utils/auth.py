"""
Authentification JWT avec python-jose
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from .database import get_db_connection

# Configuration logging
log = logging.getLogger(__name__)

# Configuration JWT
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    log.warning("JWT_SECRET non défini, utilisation d'une clé par défaut (NON SÉCURISÉ)")
    JWT_SECRET = "coach_ia_secret_key_dev"

JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Configuration hachage mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = HTTPBearer()

def create_jwt_token(username: str, role: str) -> str:
    """Créer un token JWT"""
    payload = {
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def hash_password(password: str) -> str:
    """Hacher un mot de passe"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifier un mot de passe"""
    return pwd_context.verify(plain_password, hashed_password)

def get_user_from_db(username: str) -> Optional[Dict]:
    """Récupérer un utilisateur depuis la base de données"""
    try:
        engine = get_db_connection()
        query = "SELECT username, password_hash, role FROM auth_users WHERE username = ?"
        
        with engine.connect() as conn:
            result = conn.execute(query, (username,))
            row = result.fetchone()
            
            if row:
                return {
                    "username": row[0],
                    "password_hash": row[1], 
                    "role": row[2]
                }
        return None
    except Exception as e:
        log.error(f"Erreur récupération utilisateur {username}: {e}")
        return None

def verify_credentials(username: str, password: str) -> Dict[str, str]:
    """Vérifier les identifiants utilisateur"""
    user = get_user_from_db(username)
    
    if not user or not verify_password(password, user["password_hash"]):
        log.warning(f"Tentative de connexion échouée pour: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects"
        )
    
    log.info(f"Connexion réussie pour: {username}")
    return {"username": username, "role": user["role"]}

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, str]:
    """Vérifier et décoder le token JWT"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("username")
        role = payload.get("role")
        exp = payload.get("exp")
        
        if username is None or role is None:
            log.warning("Token JWT invalide - données manquantes")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
        
        # Vérification expiration
        if exp and datetime.utcnow().timestamp() > exp:
            log.warning(f"Token expiré pour {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expiré"
            )
        
        return {"username": username, "role": role}
        
    except JWTError as e:
        log.error(f"Erreur validation JWT: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )