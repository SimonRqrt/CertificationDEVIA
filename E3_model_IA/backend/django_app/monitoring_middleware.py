import time
import logging
from django.utils.deprecation import MiddlewareMixin
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from django.http import HttpResponse
from django.conf import settings

logger = logging.getLogger(__name__)

# Métriques Prometheus pour Django
django_requests_total = Counter(
    'django_http_requests_total', 
    'Total HTTP requests', 
    ['method', 'endpoint', 'status']
)

django_request_duration = Histogram(
    'django_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

django_active_requests = Gauge(
    'django_active_requests',
    'Number of active HTTP requests'
)

django_auth_failures = Counter(
    'django_auth_failures_total',
    'Total authentication failures',
    ['reason']
)

django_db_connections = Gauge(
    'django_db_connections_active',
    'Active database connections'
)

django_db_connections_max = Gauge(
    'django_db_connections_max', 
    'Maximum database connections'
)

class PrometheusMiddleware(MiddlewareMixin):
    """Middleware pour collecter les métriques Django avec Prometheus"""
    
    def process_request(self, request):
        request.start_time = time.time()
        django_active_requests.inc()
        return None
    
    def process_response(self, request, response):
        # Durée de la requête
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Extraction de l'endpoint depuis l'URL
            endpoint = self._get_endpoint(request)
            method = request.method
            status = str(response.status_code)
            
            # Enregistrement des métriques
            django_requests_total.labels(
                method=method, 
                endpoint=endpoint, 
                status=status
            ).inc()
            
            django_request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            django_active_requests.dec()
            
            # Log des requêtes lentes
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {method} {endpoint} took {duration:.2f}s"
                )
        
        return response
    
    def _get_endpoint(self, request):
        """Extrait l'endpoint de la requête"""
        path = request.path
        
        # Simplification des endpoints avec paramètres
        if '/api/v1/activities/' in path and path.count('/') > 4:
            return '/api/v1/activities/{id}/'
        elif '/api/v1/coaching/' in path and path.count('/') > 4:
            return '/api/v1/coaching/{endpoint}/'
        elif '/admin/' in path:
            return '/admin/*'
        else:
            return path[:50]  # Truncate long paths


def metrics_view(request):
    """Endpoint pour exposer les métriques Prometheus"""
    if request.method == 'GET':
        # Mise à jour des métriques DB
        try:
            from django.db import connection
            django_db_connections.set(len(connection.queries))
            django_db_connections_max.set(getattr(settings, 'DATABASES', {}).get('default', {}).get('CONN_MAX_AGE', 100))
        except Exception as e:
            logger.error(f"Error collecting DB metrics: {e}")
        
        return HttpResponse(
            generate_latest(),
            content_type='text/plain; charset=utf-8'
        )
    return HttpResponse(status=405)


class AuthFailureMiddleware(MiddlewareMixin):
    """Middleware pour traquer les échecs d'authentification"""
    
    def process_response(self, request, response):
        # Échecs d'authentification JWT
        if response.status_code == 401:
            reason = 'jwt_invalid'
            if 'token' not in request.headers.get('Authorization', ''):
                reason = 'no_token'
            elif 'expired' in str(response.content).lower():
                reason = 'token_expired'
            
            django_auth_failures.labels(reason=reason).inc()
            
            logger.warning(
                f"Auth failure: {reason} from {request.META.get('REMOTE_ADDR', 'unknown')}"
            )
        
        return response