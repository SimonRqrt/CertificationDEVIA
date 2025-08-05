from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # ===== HEALTH CHECK =====
    path('health/', views.health_check, name='health_check'),
    
    # ===== DASHBOARD UTILISATEUR =====
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('dashboard/stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    
    # ===== VUES RAPIDES =====
    path('quick-stats/', views.QuickStatsView.as_view(), name='quick_stats'),
]