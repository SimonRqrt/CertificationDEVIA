
import os
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from starlette.responses import StreamingResponse

from E3_model_IA.scripts.advanced_agent import get_coaching_graph
from langchain_core.messages import HumanMessage
import json

import sqlalchemy as sa
from E1_gestion_donnees.db_manager import create_db_engine, create_tables, get_activities_from_db, get_activity_by_id
from src.config import API_HOST, API_PORT, API_DEBUG


# On récupère la clé API attendue depuis les variables d'environnement
API_KEY = os.environ.get("API_KEY", "une-cle-secrete-par-defaut") 
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

engine = create_db_engine()
tables = create_tables(engine)

# Initialisation de la base de données
coaching_agent = get_coaching_graph()

async def get_api_key(key: str = Security(api_key_header)):
    """Vérifie la clé API fournie dans les en-têtes."""
    if key == API_KEY:
        return key
    else:
        raise HTTPException(status_code=403, detail="Clé API invalide ou manquante.")

class ChatRequest(BaseModel):
    user_id: int
    message: str
    thread_id: Optional[str] = None # Pour suivre une conversation existante

# Modèle Pydantic pour les activités
class Activity(BaseModel):
    activity_id: int
    activity_name: str
    activity_type: Optional[str] = None
    start_time: str
    distance_meters: Optional[float] = None
    duration_seconds: Optional[float] = None
    average_speed: Optional[float] = None
    max_speed: Optional[float] = None
    calories: Optional[int] = None
    average_hr: Optional[float] = None
    max_hr: Optional[int] = None
    elevation_gain: Optional[float] = None
    elevation_loss: Optional[float] = None
    
    class Config:
        from_attributes = True

class GPSData(BaseModel):
    id: int
    activity_id: int
    latitude: float
    longitude: float
    timestamp: str  

    class Config:
        from_attributes = True


# Création de l'application FastAPI
app = FastAPI(
    title="Coach running AI API",
    description="API pour accéder aux données Garmin et interagir avec l'assistant de coaching IA.",
    version="1.0.0"
)


@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API Coach AI Garmin Data"}


@app.get("/activities/", response_model=List[Activity], tags=["Données"])
def get_activities(skip: int = 0, limit: int = 10):
    """Récupérer la liste des activités"""
    results = get_activities_from_db(engine, tables, limit, skip)
    return [dict(row._mapping) for row in results]

@app.get("/activities/{activity_id}", response_model=dict, tags=["Données"])
def get_activity(activity_id: int):
    """Récupérer une activité spécifique par son ID"""
    result = get_activity_by_id(engine, tables, activity_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Activité non trouvée")
    return dict(result)

@app.get("/activities/type/{activity_type}", response_model=List[dict])
def get_activities_by_type(activity_type: str, skip: int = 0, limit: int = 10):
    """Récupérer les activités par type"""
    with engine.connect() as conn:
        select_stmt = sa.select(tables["activities"]).where(
            tables["activities"].c.activity_type == activity_type
        ).limit(limit).offset(skip)
        results = conn.execute(select_stmt).fetchall()
    return [dict(row._mapping) for row in results]

@app.get("/gps_data/{activity_id}/gps", response_model=List[GPSData])
def get_activity_gps(activity_id: int):
    """Récupérer les données GPS d'une activité spécifique"""
    with engine.connect() as conn:
        select_stmt = sa.select(tables["gps_data"]).where(
            tables["gps_data"].c.activity_id == activity_id
        )
        results = conn.execute(select_stmt).fetchall()
    
    if not results:
        raise HTTPException(status_code=404, detail="Données GPS non trouvées pour cette activité")

    return [dict(row._mapping) for row in results]

@app.post("/v1/coaching/chat", tags=["Coaching IA"])
async def chat_with_coach(
    request: ChatRequest, 
    api_key: str = Depends(get_api_key) # Sécurisation de l'endpoint
):
    """
    Communique avec l'agent de coaching IA.
    Cet endpoint utilise le streaming pour renvoyer la réponse mot par mot.
    """
    # On construit le prompt pour l'agent
    full_input = f"Je suis l'utilisateur {request.user_id}. {request.message}"
    
    # On définit un ID de conversation unique par utilisateur pour garder l'historique
    thread_id = request.thread_id or f"user-thread-{request.user_id}"
    config = {"configurable": {"thread_id": thread_id}}
    
    async def stream_response():
        """Générateur qui produit les morceaux de la réponse de l'IA."""
        # `astream` est la version asynchrone de `stream`
        async for event in coaching_agent.astream(
            {"messages": [HumanMessage(content=full_input)]},
            config=config
        ):
            for step in event.values():
                message = step["messages"][-1]
                if hasattr(message, 'content') and message.content:
                    # On envoie chaque morceau de contenu dès qu'il est disponible
                    yield json.dumps({"type": "content", "data": message.content})
        # On peut envoyer un message de fin si on veut
        yield json.dumps({"type": "end", "data": "Stream finished."})

    return StreamingResponse(stream_response(), media_type="application/x-ndjson")



def start_api():
    """Démarrer le serveur API"""
    uvicorn.run(app, host=API_HOST, port=API_PORT)

if __name__ == "__main__":
    start_api()