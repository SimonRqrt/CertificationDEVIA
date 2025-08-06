"""
Modèles Pydantic simples pour l'API REST
"""

from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel

# ===== AUTHENTIFICATION =====

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ===== UTILISATEURS =====

class User(BaseModel):
    user_id: int
    nom: str
    prenom: str
    age: Optional[int] = None

# ===== ACTIVITÉS =====

class ActivityBase(BaseModel):
    user_id: int
    activity_name: str
    activity_type: str = "running"
    start_time: datetime
    duration_seconds: int
    distance_meters: float
    average_hr: Optional[int] = None
    calories: Optional[int] = None

class Activity(ActivityBase):
    """Modèle pour création d'activité"""
    pass

class ActivityResponse(ActivityBase):
    """Modèle de réponse avec champs calculés"""
    id: int
    distance_km: float
    duration_formatted: str

# ===== PAGINATION =====

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int