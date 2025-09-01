from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Max, Min, Q
from datetime import datetime, timedelta
from django.http import JsonResponse, HttpResponse

from activities.models import Activity
from coaching.models import TrainingPlan, WorkoutSession, Goal, PerformanceMetrics


def health_check(request):
    """Endpoint de santé pour le monitoring Docker"""
    return HttpResponse("OK", content_type="text/plain")



def user_dashboard(request):
    """Dashboard principal utilisateur - Vue d'ensemble complète"""
    if not request.user.is_authenticated:
        return redirect('/admin/login/')
    
    user = request.user
    
    # Période d'analyse (30 derniers jours par défaut)
    period_days = int(request.GET.get('period', 30))
    date_from = timezone.now() - timedelta(days=period_days)
    
    # ===== DONNÉES ACTIVITÉS =====
    recent_activities = Activity.objects.filter(
        user=user,
        start_time__gte=date_from
    ).order_by('-start_time')
    
    # Statistiques activités
    activity_stats = recent_activities.aggregate(
        total_count=Count('id'),
        total_distance=Sum('distance_meters'),
        total_duration=Sum('duration_seconds'),
        avg_pace=Avg('average_pace'),
        avg_hr=Avg('average_hr'),
        max_distance=Max('distance_meters'),
        longest_duration=Max('duration_seconds')
    )
    
    # Conversion des unités
    if activity_stats['total_distance']:
        activity_stats['total_distance_km'] = round(activity_stats['total_distance'] / 1000, 1)
    if activity_stats['total_duration']:
        hours = activity_stats['total_duration'] // 3600
        minutes = (activity_stats['total_duration'] % 3600) // 60
        activity_stats['total_duration_formatted'] = f"{hours}h {minutes}min"
    
    # Activités par type
    activity_by_type = recent_activities.values('activity_type').annotate(
        count=Count('id'),
        total_distance=Sum('distance_meters')
    ).order_by('-count')
    
    # ===== DONNÉES COACHING =====
    
    # Plans d'entraînement
    active_plans = TrainingPlan.objects.filter(user=user, is_active=True)
    completed_plans = TrainingPlan.objects.filter(user=user, is_completed=True).count()
    
    # Objectifs
    active_goals = Goal.objects.filter(user=user, is_active=True)
    achieved_goals = Goal.objects.filter(user=user, is_achieved=True).count()
    
    # Sessions d'entraînement
    upcoming_sessions = WorkoutSession.objects.filter(
        user=user,
        planned_date__gte=timezone.now().date(),
        status='planned'
    ).order_by('planned_date')[:5]
    
    recent_sessions = WorkoutSession.objects.filter(
        user=user,
        updated_at__gte=date_from
    ).order_by('-updated_at')[:10]
    
    # Statistiques sessions
    session_stats = WorkoutSession.objects.filter(
        user=user,
        planned_date__gte=date_from.date()
    ).aggregate(
        total_planned=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        skipped=Count('id', filter=Q(status='skipped'))
    )
    
    if session_stats['total_planned'] > 0:
        session_stats['completion_rate'] = round(
            (session_stats['completed'] / session_stats['total_planned']) * 100, 1
        )
    else:
        session_stats['completion_rate'] = 0
    
    # ===== MÉTRIQUES DE PERFORMANCE =====
    latest_metrics = PerformanceMetrics.objects.filter(
        user=user
    ).order_by('-calculation_date').first()
    
    # ===== DONNÉES POUR GRAPHIQUES =====
    
    # Évolution distance quotidienne (14 derniers jours)
    chart_period = timezone.now() - timedelta(days=14)
    daily_activities = Activity.objects.filter(
        user=user,
        start_time__gte=chart_period
    ).order_by('start_time')
    
    # Grouper par jour
    daily_data = {}
    for activity in daily_activities:
        date_str = activity.start_time.strftime('%Y-%m-%d')
        if date_str not in daily_data:
            daily_data[date_str] = {'distance': 0, 'duration': 0, 'count': 0}
        daily_data[date_str]['distance'] += activity.distance_km
        daily_data[date_str]['duration'] += activity.duration_seconds / 3600  # en heures
        daily_data[date_str]['count'] += 1
    
    # Données progression objectifs
    goals_progress = []
    for goal in active_goals:
        progress = {
            'name': goal.name,
            'progress_percentage': goal.progress_percentage,
            'target_date': goal.target_date,
            'current_value': goal.current_value,
            'target_value': goal.target_value,
            'target_unit': goal.target_unit
        }
        goals_progress.append(progress)
    
    # ===== RECOMMANDATIONS =====
    recommendations = []
    
    # Recommandation basée sur l'activité récente
    if activity_stats['total_count'] == 0:
        recommendations.append({
            'type': 'activity',
            'title': 'Commencez votre parcours fitness',
            'message': 'Créez un plan d\'entraînement personnalisé pour débuter.',
            'action': 'Créer un plan',
            'url': '/api/v1/coaching/simple-plan/'
        })
    elif activity_stats['total_count'] < period_days / 7 * 3:  # Moins de 3 séances/semaine
        recommendations.append({
            'type': 'frequency',
            'title': 'Augmentez votre fréquence',
            'message': f"Vous n'avez fait que {activity_stats['total_count']} activités en {period_days} jours.",
            'action': 'Créer un plan',
            'url': '/api/v1/coaching/simple-plan/'
        })
    
    # Recommandation objectifs - supprimée car intégrée dans les plans
    # Les objectifs sont maintenant gérés directement dans la création de plans
    
    # Recommandation plan d'entraînement
    if not active_plans.exists():
        recommendations.append({
            'type': 'plan',
            'title': 'Structurez votre entraînement',
            'message': 'Un plan personnalisé vous aidera à progresser efficacement.',
            'action': 'Créer un plan',
            'url': '/api/v1/coaching/simple-plan/'
        })
    
    context = {
        # Données générales
        'period_days': period_days,
        'date_from': date_from.date(),
        
        # Activités
        'activity_stats': activity_stats,
        'activity_by_type': activity_by_type,
        'recent_activities': recent_activities[:5],
        
        # Coaching
        'active_plans': active_plans,
        'completed_plans': completed_plans,
        'active_goals': active_goals,
        'achieved_goals': achieved_goals,
        'upcoming_sessions': upcoming_sessions,
        'recent_sessions': recent_sessions[:5],
        'session_stats': session_stats,
        
        # Métriques
        'latest_metrics': latest_metrics,
        
        # Données graphiques (JSON pour JavaScript)
        'daily_data_json': daily_data,
        'goals_progress_json': goals_progress,
        
        # Recommandations
        'recommendations': recommendations[:3],  # Limiter à 3 recommandations
    }
    
    return render(request, 'core/user_dashboard.html', context)


@login_required

def dashboard_stats_api(request):
    """API pour récupérer les données de dashboard en JSON"""
    user = request.user
    period_days = int(request.GET.get('period', 30))
    date_from = timezone.now() - timedelta(days=period_days)
    
    # Évolution quotidienne des activités
    daily_activities = Activity.objects.filter(
        user=user,
        start_time__gte=date_from
    ).order_by('start_time')
    
    daily_stats = {}
    for activity in daily_activities:
        date_str = activity.start_time.strftime('%Y-%m-%d')
        if date_str not in daily_stats:
            daily_stats[date_str] = {
                'distance': 0,
                'duration': 0,
                'count': 0,
                'avg_hr': []
            }
        daily_stats[date_str]['distance'] += activity.distance_km or 0
        daily_stats[date_str]['duration'] += (activity.duration_seconds or 0) / 3600
        daily_stats[date_str]['count'] += 1
        if activity.average_hr:
            daily_stats[date_str]['avg_hr'].append(activity.average_hr)
    
    # Calculer moyennes FC
    for date, stats in daily_stats.items():
        if stats['avg_hr']:
            stats['avg_hr'] = round(sum(stats['avg_hr']) / len(stats['avg_hr']), 0)
        else:
            stats['avg_hr'] = None
    
    # Progression des objectifs
    goals = Goal.objects.filter(user=user, is_active=True)
    goals_data = []
    for goal in goals:
        goals_data.append({
            'id': goal.id,
            'name': goal.name,
            'progress': goal.progress_percentage,
            'current': goal.current_value,
            'target': goal.target_value,
            'unit': goal.target_unit,
            'target_date': goal.target_date.isoformat() if goal.target_date else None
        })
    
    # Sessions de la semaine
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_sessions = WorkoutSession.objects.filter(
        user=user,
        planned_date__gte=week_start,
        planned_date__lt=week_start + timedelta(days=7)
    ).order_by('planned_date')
    
    sessions_data = []
    for session in week_sessions:
        sessions_data.append({
            'id': session.id,
            'name': session.name,
            'date': session.planned_date.isoformat(),
            'status': session.status,
            'type': session.session_type,
            'duration': session.planned_duration,
            'distance': session.planned_distance
        })
    
    return JsonResponse({
        'daily_stats': daily_stats,
        'goals_progress': goals_data,
        'week_sessions': sessions_data,
        'period_days': period_days
    })


class QuickStatsView(LoginRequiredMixin, TemplateView):
    """Vue pour affichage rapide des statistiques (widget/modal)"""
    template_name = 'core/quick_stats.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Stats rapides (7 derniers jours)
        week_ago = timezone.now() - timedelta(days=7)
        
        week_activities = Activity.objects.filter(
            user=user,
            start_time__gte=week_ago
        )
        
        week_stats = week_activities.aggregate(
            count=Count('id'),
            distance=Sum('distance_meters'),
            duration=Sum('duration_seconds')
        )
        
        context.update({
            'week_activities_count': week_stats['count'] or 0,
            'week_distance_km': round((week_stats['distance'] or 0) / 1000, 1),
            'week_duration_hours': round((week_stats['duration'] or 0) / 3600, 1),
            'active_plans': TrainingPlan.objects.filter(user=user, is_active=True).count(),
            'active_goals': Goal.objects.filter(user=user, is_active=True).count(),
        })
        
        return context