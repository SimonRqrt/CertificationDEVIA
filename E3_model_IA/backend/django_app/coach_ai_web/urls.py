"""
URL configuration for coach_ai_web project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.shortcuts import redirect
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

def home_view(request):
    """Vue d'accueil avec design Pawatech"""
    from django.shortcuts import render
    
    context = {
        'company': {
            'name': 'Coach AI',
            'tagline': 'Plateforme IA pour coaching sportif',
            'description': 'Solution complète d\'analyse et de coaching sportif personnalisé. Intégration données Garmin, IA conversationnelle et analyses de performances avancées.'
        },
        'statistics': [
            {'label': 'Analyses IA', 'value': '24/7'},
            {'label': 'Données Garmin', 'value': 'Temps réel'},
            {'label': 'Coaching', 'value': 'Personnalisé'},
            {'label': 'API', 'value': 'REST + JWT'}
        ],
        'features': [
            {'title': 'Authentification JWT', 'description': 'Système d\'authentification sécurisé avec tokens JWT et gestion des utilisateurs.'},
            {'title': 'Intégration Garmin', 'description': 'Extraction automatique des données d\'activités sportives depuis Garmin Connect.'},
            {'title': 'Agent IA Conversationnel', 'description': 'Coaching personnalisé basé sur LangGraph et RAG avec base de connaissances.'},
            {'title': 'API FastAPI', 'description': 'API moderne et performante pour l\'intégration avec les applications tierces.'},
            {'title': 'Interface Streamlit', 'description': 'Interface utilisateur intuitive pour l\'interaction avec l\'IA de coaching.'},
            {'title': 'Base de données Azure', 'description': 'Stockage sécurisé et scalable des données utilisateurs et d\'activités.'}
        ],
        'services': [
            {'name': 'Administration Django', 'url': '/admin/', 'description': 'Gestion complète des utilisateurs et données'},
            {'name': 'API Authentification', 'url': '/api/v1/auth/', 'description': 'Endpoints de connexion et gestion profil'},
            {'name': 'API Activités', 'url': '/api/v1/activities/', 'description': 'Accès aux données d\'activités sportives'},
            {'name': 'API Coaching', 'url': '/api/v1/coaching/', 'description': 'IA conversationnelle et coaching personnalisé'},
            {'name': 'Documentation Swagger', 'url': '/swagger/', 'description': 'Documentation interactive des APIs'},
            {'name': 'FastAPI (Port 8000)', 'url': 'http://localhost:8000', 'description': 'Service IA et APIs'},
            {'name': 'Streamlit (Port 8501)', 'url': 'http://localhost:8501', 'description': 'Interface utilisateur'}
        ]
    }
    
    return render(request, 'core/home.html', context)

# Configuration Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Coach AI API",
        default_version='v1',
        description="API pour l'application Coach AI - Gestion des données sportives et coaching IA",
        contact=openapi.Contact(email="contact@coach-ai.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Page d'accueil
    path('', home_view, name='home'),
    
    # Administration Django
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/schema/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    # API Endpoints
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/activities/', include('activities.urls')),
    path('api/v1/coaching/', include('coaching.urls')),
    path('api/v1/core/', include('core.urls')),
    
    # Route directe de test pour dashboard
    path('dashboard-test/', lambda r: HttpResponse('<h1>Test Dashboard</h1><a href="/admin/">Admin</a>')),
]

# Servir les fichiers statiques et médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
