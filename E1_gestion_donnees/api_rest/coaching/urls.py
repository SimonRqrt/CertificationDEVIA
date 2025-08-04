from django.urls import path, include
from . import views

app_name = 'coaching'

urlpatterns = [
    # ===== DASHBOARD COACHING =====
    path('', views.dashboard_coaching_view, name='dashboard'),
    path('dashboard/', views.dashboard_coaching_view, name='dashboard_alt'),
    
    # ===== GÉNÉRATEUR SIMPLIFIÉ =====
    # Interface simplifiée pour générer un plan
    path('simple-plan/', views.simple_plan_generator, name='simple_plan_generator'),
    
    # ===== ASSISTANT OBJECTIFS RUNNING =====
    # Interface guidée principale
    path('running-wizard/', views.RunningGoalWizardView.as_view(), name='running_wizard'),
    
    # Objectifs rapides
    path('quick-goal/', views.quick_goal_view, name='quick_goal'),
    
    # ===== GESTION DES PLANS D'ENTRAÎNEMENT =====
    path('plans/', views.TrainingPlanListView.as_view(), name='plan_list'),
    path('plans/<int:pk>/', views.TrainingPlanDetailView.as_view(), name='plan_detail'),
    
    # ===== API ENDPOINTS (pour intégration future) =====
    # Ces endpoints pourront être développés plus tard
    # path('api/generate-plan/', views.api_generate_plan, name='api_generate_plan'),
    # path('api/update-session/', views.api_update_session, name='api_update_session'),
]