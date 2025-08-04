"""
API FastAPI minimale pour tests Grafana
"""
from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import generate_latest, Counter, Histogram

app = FastAPI(title="Coach AI API - Minimal")

# Métriques de base
requests_total = Counter('requests_total', 'Total requests')
response_time = Histogram('response_time_seconds', 'Response time')

@app.get("/")
def root():
    requests_total.inc()
    return {"message": "Coach AI API - Version minimale pour tests"}

@app.get("/metrics")
def metrics():
    """Endpoint Prometheus pour les métriques"""
    return Response(generate_latest(), media_type="text/plain")

@app.get("/health")
def health():
    return {"status": "healthy", "service": "fastapi-minimal"}
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)