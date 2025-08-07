from django.urls import path, include
from . import views, api_views

app_name = 'coaching'

urlpatterns = [
    # ===== DASHBOARD COACHING =====
    path('', views.dashboard_coaching_view, name='dashboard'),
    path('dashboard/', views.dashboard_coaching_view, name='dashboard_alt'),
    
    # ===== GÉNÉRATEUR SIMPLIFIÉ =====
    # Interface simplifiée pour générer un plan
    path('simple-plan/', views.simple_plan_generator, name='simple_plan_generator'),
    
    # ===== ASSISTANT OBJECTIFS RUNNING (DÉSACTIVÉ) =====
    # Interface guidée principale - désactivée car trop complexe
    # path('running-wizard/', views.RunningGoalWizardView.as_view(), name='running_wizard'),
    
    # Objectifs rapides
    path('quick-goal/', views.quick_goal_view, name='quick_goal'),
    
    # ===== GESTION DES PLANS D'ENTRAÎNEMENT (LECTURE SEULE) =====
    path('plans/', views.TrainingPlanListView.as_view(), name='plan_list'),
    # Détails des plans désactivés - utilise simple_plan_result.html à la place
    # path('plans/<int:pk>/', views.TrainingPlanDetailView.as_view(), name='plan_detail'),
    
    # ===== API ENDPOINTS AGENT IA =====
    path('api/chat/', api_views.chat_with_coach, name='api_chat'),
    path('api/generate-plan/', api_views.generate_training_plan, name='api_generate_plan'),
    path('api/context/', api_views.user_coaching_context, name='api_context'),
    path('api/sessions/', api_views.coaching_sessions_history, name='api_sessions'),
]