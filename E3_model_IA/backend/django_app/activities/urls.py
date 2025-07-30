from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import pipeline_views

# Router API REST
router = DefaultRouter()
router.register('activities', views.ActivityViewSet, basename='activity-api')
router.register('splits', views.ActivitySplitViewSet, basename='split-api')
router.register('gps-points', views.GPSPointViewSet, basename='gps-api')

app_name = 'activities'

urlpatterns = [
    # ===== VUES WEB =====
    # Dashboard et statistiques
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard_alt'),
    
    # Liste et gestion des activités
    path('list/', views.ActivityListView.as_view(), name='list'),
    path('create/', views.ActivityCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ActivityDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ActivityUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ActivityDeleteView.as_view(), name='delete'),
    
    # ===== API JSON =====
    # API pour graphiques et statistiques
    path('api/stats/', views.activity_stats_json, name='stats_json'),
    
    # ===== PIPELINE GARMIN =====
    # Interface de synchronisation des données
    path('pipeline/', pipeline_views.pipeline_dashboard, name='pipeline_dashboard'),
    path('pipeline/trigger/', pipeline_views.trigger_pipeline, name='trigger_pipeline'),
    path('pipeline/logs/', pipeline_views.pipeline_logs, name='pipeline_logs'),
    path('pipeline/status/', pipeline_views.pipeline_status, name='pipeline_status'),
    
    # ===== API REST =====
    # APIs REST complètes
    path('', include(router.urls)),
]