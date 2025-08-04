from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Avg, Sum, Max, Min, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Activity, ActivitySplit, GPSPoint
from .serializers import ActivitySerializer, ActivitySplitSerializer, GPSPointSerializer
from .forms import ActivityForm, ActivityFilterForm
import json


# ===== VUES BASÉES SUR LES CLASSES =====

class ActivityListView(LoginRequiredMixin, ListView):
    """Liste des activités de l'utilisateur connecté"""
    model = Activity
    template_name = 'activities/activity_list.html'
    context_object_name = 'activities'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Activity.objects.filter(user=self.request.user)
        
        # Filtres
        activity_type = self.request.GET.get('activity_type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(start_time__date__gte=date_from)
            
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(start_time__date__lte=date_to)
        
        return queryset.order_by('-start_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ActivityFilterForm(self.request.GET)
        context['activity_types'] = Activity.objects.filter(
            user=self.request.user
        ).values_list('activity_type', flat=True).distinct()
        return context


class ActivityDetailView(LoginRequiredMixin, DetailView):
    """Détail d'une activité avec splits et GPS"""
    model = Activity
    template_name = 'activities/activity_detail.html'
    context_object_name = 'activity'
    
    def get_queryset(self):
        return Activity.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activity = self.get_object()
        
        # Récupérer les splits
        context['splits'] = activity.splits.all()
        
        # Points GPS pour la carte (limités pour les performances)
        gps_points = activity.gps_points.all()[::10]  # Un point sur 10
        context['gps_data'] = [
            {
                'lat': point.latitude,
                'lng': point.longitude,
                'time': point.elapsed_time,
                'hr': point.heart_rate,
                'speed': point.speed
            } for point in gps_points if point.latitude and point.longitude
        ]
        
        return context


class ActivityCreateView(LoginRequiredMixin, CreateView):
    """Création d'une nouvelle activité"""
    model = Activity
    form_class = ActivityForm
    template_name = 'activities/activity_form.html'
    success_url = reverse_lazy('activities:list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.is_manual = True
        messages.success(self.request, 'Activité créée avec succès!')
        return super().form_valid(form)


class ActivityUpdateView(LoginRequiredMixin, UpdateView):
    """Modification d'une activité"""
    model = Activity
    form_class = ActivityForm
    template_name = 'activities/activity_form.html'
    
    def get_queryset(self):
        return Activity.objects.filter(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Activité modifiée avec succès!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('activities:detail', kwargs={'pk': self.object.pk})


class ActivityDeleteView(LoginRequiredMixin, DeleteView):
    """Suppression d'une activité"""
    model = Activity
    template_name = 'activities/activity_confirm_delete.html'
    success_url = reverse_lazy('activities:list')
    
    def get_queryset(self):
        return Activity.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Activité supprimée avec succès!')
        return super().delete(request, *args, **kwargs)


# ===== VUES FONCTIONNELLES =====

@login_required
def dashboard_view(request):
    """Dashboard avec statistiques des activités"""
    user = request.user
    
    # Période par défaut : 30 derniers jours
    date_from = timezone.now() - timedelta(days=30)
    activities = Activity.objects.filter(user=user, start_time__gte=date_from)
    
    # Statistiques générales
    stats = activities.aggregate(
        total_activities=Count('id'),
        total_distance=Sum('distance_meters'),
        total_duration=Sum('duration_seconds'),
        avg_pace=Avg('average_pace'),
        avg_hr=Avg('average_hr'),
        max_distance=Max('distance_meters'),
        max_duration=Max('duration_seconds')
    )
    
    # Conversion des unités
    if stats['total_distance']:
        stats['total_distance_km'] = round(stats['total_distance'] / 1000, 1)
    if stats['total_duration']:
        hours = stats['total_duration'] // 3600
        minutes = (stats['total_duration'] % 3600) // 60
        stats['total_duration_formatted'] = f"{hours}h {minutes}min"
    if stats['max_distance']:
        stats['max_distance_km'] = round(stats['max_distance'] / 1000, 1)
    
    # Activités par type
    activity_types = activities.values('activity_type').annotate(
        count=Count('id'),
        distance=Sum('distance_meters')
    ).order_by('-count')
    
    # Activités récentes
    recent_activities = activities.order_by('-start_time')[:5]
    
    # Records personnels (sur toute la période)
    all_activities = Activity.objects.filter(user=user)
    records = {
        'fastest_5k': all_activities.filter(
            distance_meters__gte=4900, 
            distance_meters__lte=5100
        ).order_by('duration_seconds').first(),
        'fastest_10k': all_activities.filter(
            distance_meters__gte=9900, 
            distance_meters__lte=10100
        ).order_by('duration_seconds').first(),
        'longest_distance': all_activities.order_by('-distance_meters').first(),
        'longest_duration': all_activities.order_by('-duration_seconds').first(),
    }
    
    context = {
        'stats': stats,
        'activity_types': activity_types,
        'recent_activities': recent_activities,
        'records': records,
        'period_days': 30,
    }
    
    return render(request, 'activities/dashboard.html', context)


@login_required
def activity_stats_json(request):
    """API JSON pour les graphiques du dashboard"""
    user = request.user
    period = request.GET.get('period', '30')  # jours
    
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    date_from = timezone.now() - timedelta(days=days)
    activities = Activity.objects.filter(
        user=user, 
        start_time__gte=date_from
    ).order_by('start_time')
    
    # Données pour graphiques
    data = {
        'daily_distance': [],
        'weekly_summary': [],
        'hr_zones': [],
        'pace_evolution': []
    }
    
    # Distance quotidienne
    daily_data = {}
    for activity in activities:
        date_str = activity.start_time.strftime('%Y-%m-%d')
        if date_str not in daily_data:
            daily_data[date_str] = 0
        daily_data[date_str] += activity.distance_km
    
    for date_str, distance in sorted(daily_data.items()):
        data['daily_distance'].append({
            'date': date_str,
            'distance': round(distance, 2)
        })
    
    # Évolution de l'allure
    for activity in activities.filter(average_pace__isnull=False):
        if activity.average_pace and activity.distance_km > 1:  # Minimum 1km
            pace_min_per_km = activity.average_pace / 60
            data['pace_evolution'].append({
                'date': activity.start_time.strftime('%Y-%m-%d'),
                'pace': round(pace_min_per_km, 2),
                'distance': activity.distance_km
            })
    
    return JsonResponse(data)


# ===== API REST =====

class ActivityViewSet(viewsets.ModelViewSet):
    """ViewSet API pour les activités"""
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Activity.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Statistiques des activités de l'utilisateur"""
        activities = self.get_queryset()
        
        stats = activities.aggregate(
            total_count=Count('id'),
            total_distance=Sum('distance_meters'),
            total_duration=Sum('duration_seconds'),
            avg_pace=Avg('average_pace'),
            avg_hr=Avg('average_hr')
        )
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Activités groupées par type"""
        activities_by_type = self.get_queryset().values('activity_type').annotate(
            count=Count('id'),
            total_distance=Sum('distance_meters'),
            avg_duration=Avg('duration_seconds')
        )
        
        return Response(list(activities_by_type))


class ActivitySplitViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet API pour les splits d'activités"""
    serializer_class = ActivitySplitSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ActivitySplit.objects.filter(activity__user=self.request.user)


class GPSPointViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet API pour les points GPS"""
    serializer_class = GPSPointSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = GPSPoint.objects.filter(activity__user=self.request.user)
        
        # Limiter les points pour les performances
        activity_id = self.request.query_params.get('activity_id')
        if activity_id:
            queryset = queryset.filter(activity_id=activity_id)
            step = int(self.request.query_params.get('step', 10))
            # Prendre un point sur 'step' pour réduire la charge
            ids = list(queryset.values_list('id', flat=True)[::step])
            queryset = queryset.filter(id__in=ids)
        
        return queryset
