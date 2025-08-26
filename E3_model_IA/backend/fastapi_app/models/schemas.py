"""
Modèles Pydantic pour l'API Coach AI
"""

from pydantic import BaseModel, validator, Field
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Message utilisateur (1-2000 caractères)")
    thread_id: Optional[str] = Field(None, max_length=100, description="ID de conversation existante")
    user_id: Optional[int] = Field(None, ge=1, le=999999, description="ID utilisateur valide")
    
    @validator('message')
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError('Le message ne peut pas être vide')
        # Protection contre injection de prompts
        dangerous_patterns = ['system:', 'assistant:', '```python', '<script>', 'DROP TABLE']
        for pattern in dangerous_patterns:
            if pattern.lower() in v.lower():
                raise ValueError('Contenu potentiellement dangereux détecté')
        return v.strip()

class SimpleTrainingPlanRequest(BaseModel):
    """Modèle simplifié pour Django - approche objectif-centrée"""
    user_id: int
    user_email: str
    goal: str
    level: str
    sessions_per_week: int
    target_time: Optional[str] = Field(None, description="Temps objectif (ex: 45:00 pour 10k, 1:45:00 pour semi)")
    duration_weeks: int = Field(default=0, ge=0, le=20, description="Durée en semaines (0=agent détermine automatiquement)")
    target_date: Optional[str] = None
    additional_notes: Optional[str] = None
    user_activities_analysis: Optional[Dict[str, Any]] = None
    use_advanced_agent: bool = True

class TrainingPlanRequest(BaseModel):
    """Modèle pour la demande de génération de plan d'entraînement"""
    user_id: int
    user_email: str
    personal_info: Dict[str, Any]
    running_goal: Dict[str, Any]
    training_preferences: Dict[str, Any]
    recent_activities: Optional[Dict[str, Any]] = None
    user_context: Optional[Dict[str, Any]] = None

class TrainingPlanResponse(BaseModel):
    """Modèle pour la réponse de plan d'entraînement généré"""
    name: str
    description: str
    duration_weeks: int
    sessions: List[Dict[str, Any]]
    recommendations: List[str]
    generation_time: float