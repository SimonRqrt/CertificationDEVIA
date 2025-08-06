#!/usr/bin/env python3
"""
API REST Coach IA - Architecture Modulaire Simple
Conforme aux exigences de certification C5
"""

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import des modules
from utils.database import init_database, get_database_status
from endpoints.auth import router as auth_router
from endpoints.users import router as users_router  
from endpoints.activities import router as activities_router

# Configuration logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Application FastAPI
app = FastAPI(
    title="Coach IA - API REST Simple",
    description="API REST de données sportives (Certification C5)",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - Configuration sécurisée
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Enregistrement des routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(activities_router)

@app.on_event("startup")
def startup_event():
    """Initialisation de l'application"""
    log.info("🚀 Démarrage API REST Coach IA")
    
    if init_database():
        log.info("✅ Base de données initialisée")
    else:
        log.error("❌ Erreur initialisation base de données")

@app.get("/health")
def health_check():
    """Point de contrôle santé de l'API"""
    return {
        "status": "healthy",
        "service": "Coach IA API REST",
        "version": "2.0.0",
        "database": get_database_status()
    }

@app.get("/")
def root():
    """Page d'accueil de l'API"""
    return {
        "message": "🏃‍♂️ Coach IA - API REST Simple",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    log.info("🏁 Lancement du serveur sur http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)