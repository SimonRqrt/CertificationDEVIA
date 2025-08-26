"""
CallbackHandler Prometheus pour LangChain - Solution finale
Collecte les métriques OpenAI directement dans le service FastAPI
"""

import time
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import LLMResult
from typing import Dict, Any

# 🔧 SOLUTION: Créer les métriques ici pour éviter import circulaire
from prometheus_client import Counter, Histogram

# Métriques OpenAI redéfinies localement
ai_requests_total = Counter(
    "ai_requests_total", "Total des requêtes IA",
    ["endpoint", "model", "status"]
)

ai_tokens_total = Counter(
    "ai_tokens_total", "Tokens consommés", 
    ["endpoint", "model", "type"]
)

ai_cost_usd_total = Counter(
    "ai_cost_usd_total", "Coût cumulé (USD)",
    ["endpoint", "model"]
)

ai_request_duration_seconds = Histogram(
    "ai_request_duration_seconds", "Durée des requêtes IA (s)",
    ["endpoint", "model"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 15, 20, 30, 45, 60]
)

# Prix OpenAI (par 1M tokens)
OPENAI_PRICING = {
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4": {"input": 3.00, "output": 12.00}
}

def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calcule le coût réel basé sur les prix OpenAI"""
    pricing = OPENAI_PRICING.get(model, {"input": 0.50, "output": 1.50})
    return (prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]) / 1_000_000

class FastAPIPrometheusCallback(BaseCallbackHandler):
    """CallbackHandler qui collecte les métriques directement dans FastAPI"""
    
    def __init__(self):
        super().__init__()
        self.call_start_times = {}
        print("🔧 FastAPIPrometheusCallback initialisé")
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: list, **kwargs) -> None:
        """Début d'appel LLM"""
        run_id = kwargs.get('run_id')
        if run_id:
            self.call_start_times[str(run_id)] = time.time()
    
    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """Fin d'appel LLM - Collecte des métriques"""
        run_id = kwargs.get('run_id')
        if not run_id or str(run_id) not in self.call_start_times:
            return
        
        # Calculer durée
        start_time = self.call_start_times.pop(str(run_id))
        duration = time.time() - start_time
        
        # Extraire informations
        endpoint = "/agent/fastapi"
        model = "gpt-3.5-turbo"  # Default
        
        try:
            if response.generations and response.generations[0]:
                # Extraire tokens réels depuis llm_output
                if hasattr(response, 'llm_output') and response.llm_output:
                    usage = response.llm_output.get('token_usage', {})
                    prompt_tokens = usage.get('prompt_tokens', 0)
                    completion_tokens = usage.get('completion_tokens', 0)
                    total_tokens = usage.get('total_tokens', prompt_tokens + completion_tokens)
                    
                    # Modèle réel
                    if 'model_name' in response.llm_output:
                        model = response.llm_output['model_name']
                        
                    # 📊 COLLECTER MÉTRIQUES PROMETHEUS
                    ai_requests_total.labels(endpoint=endpoint, model=model, status="200").inc()
                    ai_request_duration_seconds.labels(endpoint=endpoint, model=model).observe(duration)
                    
                    ai_tokens_total.labels(endpoint=endpoint, model=model, type="prompt").inc(prompt_tokens)
                    ai_tokens_total.labels(endpoint=endpoint, model=model, type="completion").inc(completion_tokens)
                    ai_tokens_total.labels(endpoint=endpoint, model=model, type="total").inc(total_tokens)
                    
                    # Coût réel
                    cost = calculate_cost(model, prompt_tokens, completion_tokens)
                    ai_cost_usd_total.labels(endpoint=endpoint, model=model).inc(cost)
                    
                    print(f"✅ Métriques collectées: {model} - {duration:.2f}s - ${cost:.4f} - {total_tokens} tokens")
                
                else:
                    # Fallback : estimation basique
                    ai_requests_total.labels(endpoint=endpoint, model=model, status="200").inc()
                    ai_request_duration_seconds.labels(endpoint=endpoint, model=model).observe(duration)
                    print(f"⚠️ Métriques basiques: {model} - {duration:.2f}s")
                    
        except Exception as e:
            # En cas d'erreur, au minimum collecter la requête
            ai_requests_total.labels(endpoint=endpoint, model=model, status="200").inc()
            ai_request_duration_seconds.labels(endpoint=endpoint, model=model).observe(duration)
            print(f"❌ Erreur collecte métriques: {e}")
    
    def on_llm_error(self, error: Exception, **kwargs) -> None:
        """Gestion des erreurs LLM"""
        run_id = kwargs.get('run_id')
        if run_id and str(run_id) in self.call_start_times:
            start_time = self.call_start_times.pop(str(run_id))
            duration = time.time() - start_time
            
            endpoint = "/agent/fastapi"
            model = "gpt-3.5-turbo"
            
            ai_requests_total.labels(endpoint=endpoint, model=model, status="500").inc()
            ai_request_duration_seconds.labels(endpoint=endpoint, model=model).observe(duration)
            
            print(f"❌ Erreur OpenAI collectée: {duration:.2f}s - {str(error)[:50]}")

# Instance globale
prometheus_callback = FastAPIPrometheusCallback()