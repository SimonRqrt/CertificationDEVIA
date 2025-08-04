"""
API FastAPI avec monitoring complet Coach AI
"""
import os
import time
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import openai
from prometheus_client import generate_latest

# Import des métriques personnalisées
from coach_metrics import (
    monitor_openai_call, monitor_training_plan_generation, monitor_coaching_session,
    update_active_users, update_knowledge_base_size, record_database_query,
    get_metrics_summary
)

app = FastAPI(
    title="Coach AI API - Monitored",
    description="API avec monitoring complet OpenAI et Agent IA",
    version="2.0.0"
)

# Configuration OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Modèles de données
class ChatRequest(BaseModel):
    message: str
    objective: Optional[str] = "general"
    level: Optional[str] = "intermediate"
    user_id: Optional[int] = 1

class TrainingPlanRequest(BaseModel):
    objective: str  # 5K, 10K, semi, marathon
    level: str     # debutant, intermediate, avance
    weeks: int = 8
    user_id: Optional[int] = 1

# ========== ENDPOINTS PRINCIPAUX ==========

@app.get("/")
def root():
    return {
        "message": "Coach AI API avec monitoring complet",
        "endpoints": ["/chat", "/generate-plan", "/metrics", "/health", "/metrics-summary"]
    }

@app.get("/metrics")
def metrics():
    """Endpoint Prometheus pour les métriques"""
    return Response(generate_latest(), media_type="text/plain")

@app.get("/health")
def health():
    return {"status": "healthy", "service": "coach-ai-monitored"}

@app.get("/metrics-summary")
def metrics_summary():
    """Résumé des métriques pour debug"""
    return get_metrics_summary()

# ========== AGENT IA AVEC MÉTRIQUES ==========

@monitor_openai_call(model='gpt-3.5-turbo')
def call_openai_agent(messages, model='gpt-3.5-turbo'):
    """Appel OpenAI instrumenté avec métriques"""
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=messages
    )
    return response

@app.post("/chat")
@monitor_coaching_session(session_type='conversation')
def chat_with_agent(request: ChatRequest):
    """Chat conversationnel avec l'agent IA"""
    try:
        record_database_query('user_context', 'success')
        
        messages = [
            {"role": "system", "content": "Tu es Michael, un coach running expert. Réponds de manière concise et personnalisée."},
            {"role": "user", "content": request.message}
        ]
        
        response = call_openai_agent(messages)
        
        return {
            "response": response.choices[0].message.content,
            "user_id": request.user_id,
            "timestamp": time.time()
        }
        
    except Exception as e:
        record_database_query('user_context', 'error')
        raise HTTPException(status_code=500, detail=f"Erreur agent IA: {str(e)}")

@app.post("/generate-plan")
@monitor_training_plan_generation(objective="dynamic", level="dynamic")  
def generate_training_plan(request: TrainingPlanRequest):
    """Génération de plan d'entraînement avec métriques"""
    try:
        # Simulation analyse données utilisateur
        record_database_query('activities_analysis', 'success')
        time.sleep(0.1)  # Simule le temps d'analyse
        
        # Contexte pour l'IA
        context = f"""
        Génère un plan d'entraînement pour {request.objective} sur {request.weeks} semaines.
        Niveau: {request.level}
        Format: Tableau markdown avec colonnes Semaine|Séances|Distance|Objectif
        """
        
        messages = [
            {"role": "system", "content": "Tu es un expert en plans d'entraînement running. Génère des plans structurés et progressifs."},
            {"role": "user", "content": context}
        ]
        
        response = call_openai_agent(messages, model='gpt-3.5-turbo')
        
        # Mise à jour métriques spécifiques  
        from coach_metrics import training_plans_generated
        training_plans_generated.labels(
            objective=request.objective, 
            level=request.level
        ).inc()
        
        return {
            "plan": response.choices[0].message.content,
            "objective": request.objective,
            "level": request.level,
            "weeks": request.weeks,
            "generated_at": time.time()
        }
        
    except Exception as e:
        record_database_query('activities_analysis', 'error')
        raise HTTPException(status_code=500, detail=f"Erreur génération plan: {str(e)}")

# ========== SIMULATION DONNÉES TEMPS RÉEL ==========

@app.get("/simulate-activity")
def simulate_user_activity():
    """Simule de l'activité utilisateur pour tester les métriques"""
    
    # Simule des utilisateurs actifs
    import random
    active_count = random.randint(5, 25)
    update_active_users(active_count)
    
    # Simule base de connaissances
    update_knowledge_base_size(42)
    
    # Simule quelques requêtes DB
    for _ in range(random.randint(1, 5)):
        record_database_query('user_query', 'success')
    
    return {
        "message": "Activité simulée",
        "active_users": active_count,
        "knowledge_base_docs": 42
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Démarrage Coach AI API avec monitoring complet...")
    print("📊 Métriques disponibles sur: http://localhost:8000/metrics")
    print("💬 Chat IA: POST http://localhost:8000/chat")
    print("🏃 Plans: POST http://localhost:8000/generate-plan")
    uvicorn.run(app, host="0.0.0.0", port=8000)