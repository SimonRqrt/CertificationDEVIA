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
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        return limiter
    else:
        app.state.limiter = None
        return None