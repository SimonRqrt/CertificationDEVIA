"""
Configuration centralisée de l'API Coach AI
"""

import os

try:
    from src.config import API_HOST, API_PORT, API_DEBUG, DATABASE_URL
except ImportError:
    # Fallback to environment variables if config file not available
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    API_DEBUG = os.getenv('API_DEBUG', 'False').lower() == 'true'
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/garmin_data.db')

# Configuration API
API_TITLE = "Coach running AI API"
API_DESCRIPTION = "API pour accéder aux données Garmin et interagir avec l'assistant de coaching IA."
API_VERSION = "2.0.0"

# Configuration sécurité
EXPECTED_API_KEY = os.getenv("API_KEY", "coach_ai_secure_key_2025")
API_KEY_NAME = "X-API-Key"

# Configuration CORS
CORS_ORIGINS = ["http://localhost:8502", "http://localhost:8002"]

# Configuration rate limiting OWASP
RATE_LIMIT_COACHING = "10/minute"
RATE_LIMIT_LEGACY = "5/minute"

# Configuration métriques
METRICS_PORT = 8080

# Configuration logging
SECURITY_LOG_FILE = "security.log"

# Tags OpenAPI pour conformité C9
OPENAPI_TAGS = [
    {"name": "Coaching IA", "description": "Endpoints du modèle d'intelligence artificielle"},
    {"name": "Données", "description": "Endpoints d'accès aux données utilisateur"},
    {"name": "Santé", "description": "Endpoints de monitoring et santé"},
    {"name": "Analytics E1", "description": "Endpoints d'analytics avancés"},
    {"name": "Système", "description": "Endpoints système et statut"}
]