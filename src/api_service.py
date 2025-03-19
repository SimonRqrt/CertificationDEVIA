from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import sqlalchemy as sa
from .db_manager import create_db_engine, create_tables, get_activities_from_db, get_activity_by_id
from .config import API_HOST, API_PORT, API_DEBUG

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
    title="Garmin Data API",
    description="API pour accéder aux données d'activités Garmin",
    version="0.1.0"
)

# Initialisation de la base de données
engine = create_db_engine()
tables = create_tables(engine)

@app.get("/")
def root():
    return {"message": "Bienvenue sur l'API Garmin Data"}


@app.get("/activities/", response_model=List[Activity])
def get_activities(skip: int = 0, limit: int = 10):
    """Récupérer la liste des activités"""
    results = get_activities_from_db(engine, tables, limit, skip)
    return [dict(row._mapping) for row in results]

@app.get("/activities/{activity_id}", response_model=dict)
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


def start_api():
    """Démarrer le serveur API"""
    uvicorn.run(app, host=API_HOST, port=API_PORT)

if __name__ == "__main__":
    start_api()