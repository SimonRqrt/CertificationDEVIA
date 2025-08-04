import time
import logging
from fastapi import Request, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import httpx

logger = logging.getLogger(__name__)

# Métriques Prometheus pour FastAPI
fastapi_requests_total = Counter(
    'fastapi_http_requests_total',
    'Total HTTP requests', 
    ['method', 'endpoint', 'status']
)

fastapi_request_duration = Histogram(
    'fastapi_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

fastapi_active_requests = Gauge(
    'fastapi_active_requests',
    'Number of active HTTP requests'
)

# Métriques spécifiques IA
openai_requests_total = Counter(
    'openai_requests_total',
    'Total OpenAI API requests',
    ['model', 'status']
)

openai_request_duration = Histogram(
    'openai_request_duration_seconds', 
    'OpenAI API request duration in seconds',
    ['model']
)

openai_tokens_total = Counter(
    'openai_tokens_total',
    'Total OpenAI tokens consumed',
    ['model', 'type']  # type: prompt, completion
)

openai_cost_total = Counter(
    'openai_cost_total_usd',
    'Total OpenAI API cost in USD',
    ['model']
)

# Métriques coaching
coaching_sessions_total = Counter(
    'coaching_sessions_total',
    'Total coaching sessions created',
    ['user_type']
)

coaching_session_duration = Histogram(
    'coaching_session_duration_seconds',
    'Coaching session duration in seconds'
)

rag_queries_total = Counter(
    'rag_queries_total',
    'Total RAG queries processed',
    ['status']
)

rag_query_duration = Histogram(
    'rag_query_duration_seconds',
    'RAG query processing time in seconds'
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware FastAPI pour métriques Prometheus"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        fastapi_active_requests.inc()
        
        try:
            response = await call_next(request)
            
            # Calcul de la durée
            duration = time.time() - start_time
            
            # Extraction des labels
            method = request.method
            endpoint = self._get_endpoint_pattern(request.url.path)
            status = str(response.status_code)
            
            # Enregistrement métriques
            fastapi_requests_total.labels(
                method=method,
                endpoint=endpoint, 
                status=status
            ).inc()
            
            fastapi_request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            # Log requêtes lentes
            if duration > 2.0:
                logger.warning(
                    f"Slow FastAPI request: {method} {endpoint} took {duration:.2f}s"
                )
            
            return response
            
        except Exception as e:
            # Erreur interne
            fastapi_requests_total.labels(
                method=request.method,
                endpoint=self._get_endpoint_pattern(request.url.path),
                status="500"
            ).inc()
            raise
        finally:
            fastapi_active_requests.dec()
    
    def _get_endpoint_pattern(self, path: str) -> str:
        """Normalise le path pour grouper les métriques"""
        if path.startswith('/v1/coaching/'):
            if 'chat' in path:
                return '/v1/coaching/chat'
            elif 'training-plan' in path:
                return '/v1/coaching/training-plan'
            else:
                return '/v1/coaching/*'
        elif path.startswith('/docs') or path.startswith('/openapi'):
            return '/docs'
        elif path == '/metrics':
            return '/metrics'
        else:
            return path[:30]


def track_openai_request(model: str, prompt_tokens: int, completion_tokens: int, 
                        duration: float, success: bool):
    """Enregistre les métriques d'une requête OpenAI"""
    status = "success" if success else "error"
    
    openai_requests_total.labels(model=model, status=status).inc()
    openai_request_duration.labels(model=model).observe(duration)
    
    if success:
        openai_tokens_total.labels(model=model, type="prompt").inc(prompt_tokens)
        openai_tokens_total.labels(model=model, type="completion").inc(completion_tokens)
        
        # Calcul coût approximatif (GPT-3.5-turbo)
        cost_per_1k_tokens = 0.002 if 'gpt-3.5' in model else 0.03
        total_cost = ((prompt_tokens + completion_tokens) / 1000) * cost_per_1k_tokens
        openai_cost_total.labels(model=model).inc(total_cost)


def track_coaching_session(user_type: str, duration: float):
    """Enregistre les métriques d'une session de coaching"""
    coaching_sessions_total.labels(user_type=user_type).inc()
    coaching_session_duration.observe(duration)


def track_rag_query(duration: float, success: bool):
    """Enregistre les métriques d'une requête RAG"""
    status = "success" if success else "error"
    rag_queries_total.labels(status=status).inc()
    rag_query_duration.observe(duration)


async def metrics_endpoint():
    """Endpoint pour exposer les métriques Prometheus"""
    return StarletteResponse(
        generate_latest(),
        media_type="text/plain; charset=utf-8"
    )


class OpenAIClientWrapper:
    """Wrapper pour tracker automatiquement les requêtes OpenAI"""
    
    def __init__(self, openai_client):
        self.client = openai_client
    
    async def chat_completions_create(self, **kwargs):
        """Wrapper pour openai.chat.completions.create avec tracking"""
        model = kwargs.get('model', 'unknown')
        start_time = time.time()
        
        try:
            response = await self.client.chat.completions.create(**kwargs)
            duration = time.time() - start_time
            
            # Extraction des tokens usage
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            
            track_openai_request(
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                duration=duration,
                success=True
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            track_openai_request(
                model=model,
                prompt_tokens=0,
                completion_tokens=0, 
                duration=duration,
                success=False
            )
            
            logger.error(f"OpenAI API error: {e}")
            raise