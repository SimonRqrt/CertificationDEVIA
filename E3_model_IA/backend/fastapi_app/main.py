"""
Application FastAPI modulaire - Point d'entrée principal
"""

import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from prometheus_client import generate_latest, Counter
from rich import print as rprint

# Add project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

# Configuration
from config.settings import (
    API_TITLE, API_DESCRIPTION, API_VERSION, OPENAPI_TAGS, 
    CORS_ORIGINS
)

# Middleware
from middleware.rate_limit import setup_rate_limiting

# Routers
from routers import data, coaching, analytics

# Services externes
from django_db_connector import db_connector
from E3_model_IA.scripts.advanced_agent import get_coaching_graph

# SOLUTION DÉFINITIVE: Métriques AI intégrées dans FastAPI (registre séparé)
from prometheus_client import Counter, Histogram, CollectorRegistry

# Registre séparé pour éviter les conflits avec l'agent IA
app_registry = CollectorRegistry()

# Métriques OpenAI pour dashboards C11, C20, C21
ai_requests_total = Counter(
    "app_ai_requests_total", "Total des requêtes IA (App)",
    ["endpoint", "model", "status"],
    registry=app_registry
)

ai_tokens_total = Counter(
    "app_ai_tokens_total", "Tokens consommés (App)", 
    ["endpoint", "model", "type"],
    registry=app_registry
)

ai_cost_usd_total = Counter(
    "app_ai_cost_usd_total", "Coût cumulé (USD) (App)",
    ["endpoint", "model"],
    registry=app_registry
)

ai_request_duration_seconds = Histogram(
    "app_ai_request_duration_seconds", "Durée des requêtes IA (s) (App)",
    ["endpoint", "model"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 15, 20, 30, 45, 60],
    registry=app_registry
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire du cycle de vie de l'application"""
    
    rprint("[yellow]Démarrage de l'application modulaire...[/yellow]")

    # Métriques Prometheus disponibles via /metrics endpoint
    rprint("[green]Endpoint /metrics configuré pour Prometheus[/green]")

    # Connexion à PostgreSQL Django
    app.state.db_connector = db_connector
    connection_test = db_connector.test_connection()
    if connection_test['status'] == 'connected':
        rprint(f"[green]PostgreSQL Django connectée: {connection_test['total_activities']} activités[/green]")
    else:
        rprint(f"[red]Erreur connexion PostgreSQL: {connection_test['error']}[/red]")

    # Initialisation de l'agent IA
    coaching_agent = await get_coaching_graph()
    app.state.coaching_agent = coaching_agent
    
    # Service analytics utilise le connecteur PostgreSQL
    app.state.analytics_db = db_connector
    rprint("[green]Service Analytics PostgreSQL Django prêt.[/green]")

    rprint("[bold green]Application modulaire démarrée. L'agent et analytics sont prêts.[/bold green]")

    yield

    rprint("[yellow]Arrêt de l'application modulaire...[/yellow]")

def create_app() -> FastAPI:
    """Factory pour créer l'application FastAPI"""
    
    # Création de l'application
    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION,
        lifespan=lifespan,
        docs_url=None,         # désactive la page Swagger par défaut
        redoc_url=None,        # désactive la page ReDoc par défaut
        openapi_url="/openapi.json",
        openapi_tags=OPENAPI_TAGS
    )

    # Configuration du rate limiting OWASP
    setup_rate_limiting(app)

    # CORS middleware pour sécurité
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # Servir les assets statiques pour accessibilité
    import os
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Enregistrement des routers
    app.include_router(data.router)
    app.include_router(coaching.router)
    app.include_router(analytics.router)

    # Endpoints racine
    @app.get("/")
    def root():
        return {"message": "Bienvenue sur l'API Coach AI Garmin Data (Architecture Modulaire)"}

    @app.get("/metrics")
    def metrics():
        """Endpoint Prometheus pour les vraies métriques OpenAI"""
        try:
            # Expose toutes les métriques Prometheus collectées
            return Response(generate_latest(), media_type="text/plain")
        except Exception as e:
            rprint(f"[red]Erreur exposition métriques: {e}[/red]")
            return Response(
                f"# Prometheus metrics endpoint error: {str(e)}\n", 
                media_type="text/plain"
            )

    # Route Swagger UI personnalisée pour accessibilité
    @app.get("/docs", include_in_schema=False)
    def custom_swagger_ui() -> HTMLResponse:
        html = get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Documentation",
            swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="/static/a11y/custom-swagger.css",   # notre CSS fusionne les overrides
            oauth2_redirect_url=None
        ).body.decode("utf-8")

        # Injecter le script a11y juste avant </body>
        inject = '<script src="/static/a11y/a11y.js"></script>\n'
        html = html.replace("</body>", f"{inject}</body>")
        return HTMLResponse(html)

    # Route ReDoc personnalisée pour accessibilité
    @app.get("/redoc", include_in_schema=False)
    def custom_redoc() -> HTMLResponse:
        html = get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - ReDoc",
            redoc_js_url="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js",
            with_google_fonts=False
        ).body.decode("utf-8")

        # Injecter notre CSS ReDoc + JS a11y
        inject_css = '<link rel="stylesheet" href="/static/a11y/custom-redoc.css" />\n'
        inject_js  = '<script src="/static/a11y/a11y.js"></script>\n'
        html = html.replace("</head>", f"{inject_css}</head>").replace("</body>", f"{inject_js}</body>")
        return HTMLResponse(html)

    return app

# Création de l'instance de l'application
app = create_app()