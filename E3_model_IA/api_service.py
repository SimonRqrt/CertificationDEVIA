
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Request, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from rich import print as rprint
from starlette.responses import StreamingResponse

from E1_gestion_donnees.db_manager import create_db_engine, create_tables, get_activities_from_db, get_activity_by_id
from E3_model_IA.scripts.advanced_agent import get_coaching_graph
from langchain_core.messages import HumanMessage
import json

from src.config import API_HOST, API_PORT, API_DEBUG, API_KEY, API_KEY_NAME, DATABASE_URL

@asynccontextmanager
async def lifespan(app: FastAPI):

    rprint("[yellow]Démarrage de l'application et des services...[/yellow]")

    app.state.db_engine = create_db_engine()
    app.state.db_tables = create_tables(app.state.db_engine)
    rprint("[green]✅ Moteur de base de données Azure SQLpour les données d'activité initialisé.[/green]")

    coaching_agent = get_coaching_graph()
    app.state.coaching_agent = coaching_agent

    rprint("[bold green]✅ Application démarrée. L'agent est prêt.[/bold green]")

    yield

    rprint("[yellow]Arrêt de l'application...[/yellow]")



# On récupère la clé API attendue depuis les variables d'environnement
app = FastAPI(
    title="Coach running AI API",
    description="API pour accéder aux données Garmin et interagir avec l'assistant de coaching IA.",
    version="1.1.0",
    lifespan=lifespan
)

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)



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


@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API Coach AI Garmin Data"}


@app.get("/activities/", response_model=List[Activity], tags=["Données"])
def list_activities(request: Request, skip: int = 0, limit: int = 10):
    engine = request.app.state.db_engine
    tables = request.app.state.db_tables
    results = get_activities_from_db(engine, tables, limit, skip)
    return [dict(row._mapping) for row in results]

@app.get("/activities/{activity_id}", response_model=dict, tags=["Données"])
def get_activity(activity_id: int, request: Request):
    engine = request.app.state.db_engine
    tables = request.app.state.db_tables
    result = get_activity_by_id(engine, tables, activity_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Activité non trouvée")
    return dict(result._mapping)

# \== Endpoint d'IA (Bloc E3) ==

@app.post("/v1/coaching/chat", tags=["Coaching IA"])
async def chat_with_coach(
    chat_request: ChatRequest,
    fastapi_request: Request,
    api_key: str = Depends(get_api_key)
):
    coaching_agent = fastapi_request.app.state.coaching_agent
    full_input = f"Je suis l'utilisateur {chat_request.user_id}. {chat_request.message}"
    thread_id = chat_request.thread_id or f"user-thread-{chat_request.user_id}"
    config = {"configurable": {"thread_id": thread_id}}

    async def stream_response():
        async for event in coaching_agent.astream({"messages": [HumanMessage(content=full_input)]}, config=config):
            for step in event.values():
                message = step["messages"][-1]
                if hasattr(message, 'content') and message.content:
                    yield json.dumps({"type": "content", "data": message.content}) + "\n"
        yield json.dumps({"type": "end", "data": "Stream finished."}) + "\n"

    return StreamingResponse(stream_response(), media_type="application/x-ndjson")


def start_api():
    """Démarrer le serveur API"""
    uvicorn.run(app, host=API_HOST, port=API_PORT)

if __name__ == "__main__":
    start_api()