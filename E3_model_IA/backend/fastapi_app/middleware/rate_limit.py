"""
Configuration du rate limiting OWASP
"""

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    
    limiter = Limiter(key_func=get_remote_address)
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    limiter = None
    RateLimitExceeded = Exception
    RATE_LIMITING_AVAILABLE = False
    print("slowapi non disponible - Rate limiting désactivé")

def setup_rate_limiting(app):
    if RATE_LIMITING_AVAILABLE and limiter:
        app.state.limiter = limiter
        # Intercepte 429 pour incrémenter la métrique RATE_LIMIT_HITS
        from E3_model_IA.backend.fastapi_app.src.metrics import RATE_LIMIT_HITS

        def rate_limit_handler(request, exc):
            try:
                endpoint = request.url.path
                RATE_LIMIT_HITS.labels(endpoint).inc()
            except Exception:
                pass
            return _rate_limit_exceeded_handler(request, exc)

        app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
        return limiter
    else:
        app.state.limiter = None
        return None