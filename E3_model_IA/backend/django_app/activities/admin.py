from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Activity, ActivitySplit, GPSPoint


class ActivitySplitInline(admin.TabularInline):
    """Inline pour les splits d'activité"""
    model = ActivitySplit
    extra = 0
    readonly_fields = ('pace_per_km',)
    fields = [
        'split_index', 'distance_meters', 'duration_seconds',
        'average_speed', 'average_hr', 'pace_per_km'
    ]


class GPSPointInline(admin.TabularInline):
    """Inline pour les points GPS (limité)"""
    model = GPSPoint
    extra = 0
    max_num = 5  # Limiter l'affichage
    readonly_fields = ('timestamp', 'elapsed_time')
    fields = ['latitude', 'longitude', 'altitude', 'timestamp', 'elapsed_time', 'heart_rate']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """Administration des activités"""
    
    list_display = [
        'activity_name', 'user', 'activity_type', 'start_time',
        'distance_display', 'duration_display', 'pace_display',
        'average_hr', 'is_race', 'is_manual'
    ]
    
    list_filter = [
        'activity_type', 'is_race', 'is_workout', 'is_manual',
        'start_time', 'user'
    ]
    
    search_fields = [
        'activity_name', 'user__username', 'user__email',
        'notes', 'device_name'
    ]
    
    readonly_fields = [
        'duration_formatted', 'distance_km', 'average_speed_kmh',
        'pace_per_km', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Informations de base', {
            'fields': (
                ('user', 'activity_name', 'activity_type'),
                ('start_time', 'end_time'),
                ('duration_seconds', 'duration_formatted'),
                ('distance_meters', 'distance_km'),
            )
        }),
        ('Identifiants externes', {
            'fields': (
                ('activity_id', 'garmin_id', 'strava_id'),
            ),
            'classes': ('collapse',),
        }),
        ('Performance', {
            'fields': (
                ('average_speed', 'max_speed', 'average_speed_kmh'),
                ('average_pace', 'pace_per_km'),
                ('average_hr', 'max_hr'),
                ('calories', 'training_load'),
            )
        }),
        ('Zones de fréquence cardiaque', {
            'fields': (
                ('hr_zone_1_time', 'hr_zone_2_time'),
                ('hr_zone_3_time', 'hr_zone_4_time'),
                ('hr_zone_5_time',),
            ),
            'classes': ('collapse',),
        }),
        ('Données running', {
            'fields': (
                ('steps', 'average_cadence', 'max_cadence'),
                ('stride_length',),
            ),
            'classes': ('collapse',),
        }),
        ('Performances spéciales', {
            'fields': (
                ('vo2_max',),
                ('fastest_1k', 'fastest_5k', 'fastest_10k'),
                ('aerobic_effect', 'anaerobic_effect'),
            ),
            'classes': ('collapse',),
        }),
        ('Position et élévation', {
            'fields': (
                ('start_latitude', 'start_longitude'),
                ('end_latitude', 'end_longitude'),
                ('elevation_gain', 'elevation_loss'),
            ),
            'classes': ('collapse',),
        }),
        ('Conditions météo', {
            'fields': (
                ('temperature', 'humidity', 'wind_speed'),
            ),
            'classes': ('collapse',),
        }),
        ('Ressenti et notes', {
            'fields': (
                ('perceived_exertion', 'device_name'),
                ('notes',),
            )
        }),
        ('Statut', {
            'fields': (
                ('is_race', 'is_workout', 'is_manual'),
            )
        }),
        ('Métadonnées', {
            'fields': (
                ('created_at', 'updated_at', 'synced_at'),
            ),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [ActivitySplitInline, GPSPointInline]
    
    def distance_display(self, obj):
        """Affichage formaté de la distance"""
        if obj.distance_meters:
            return f"{obj.distance_km} km"
        return "-"
    distance_display.short_description = "Distance"
    distance_display.admin_order_field = 'distance_meters'
    
    def duration_display(self, obj):
        """Affichage formaté de la durée"""
        return obj.duration_formatted
    duration_display.short_description = "Durée"
    duration_display.admin_order_field = 'duration_seconds'
    
    def pace_display(self, obj):
        """Affichage de l'allure"""
        pace = obj.pace_per_km
        return pace if pace else "-"
    pace_display.short_description = "Allure"
    pace_display.admin_order_field = 'average_pace'
    
    def get_queryset(self, request):
        """Optimiser les requêtes"""
        return super().get_queryset(request).select_related('user')
    
    def save_model(self, request, obj, form, change):
        """Actions personnalisées à la sauvegarde"""
        if not change:  # Création
            obj.is_manual = True
        super().save_model(request, obj, form, change)


@admin.register(ActivitySplit)
class ActivitySplitAdmin(admin.ModelAdmin):
    """Administration des splits"""
    
    list_display = [
        'activity', 'split_index', 'distance_meters',
        'duration_seconds', 'pace_display', 'average_hr'
    ]
    
    list_filter = ['split_type', 'activity__activity_type']
    search_fields = ['activity__activity_name', 'activity__user__username']
    
    readonly_fields = ['pace_per_km']
    
    def pace_display(self, obj):
        return obj.pace_per_km
    pace_display.short_description = "Allure"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('activity', 'activity__user')


@admin.register(GPSPoint)
class GPSPointAdmin(admin.ModelAdmin):
    """Administration des points GPS"""
    
    list_display = [
        'activity', 'timestamp', 'latitude', 'longitude',
        'altitude', 'heart_rate', 'speed'
    ]
    
    list_filter = ['activity__activity_type', 'timestamp']
    search_fields = ['activity__activity_name', 'activity__user__username']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('activity', 'activity__user')
    
    def has_add_permission(self, request):
        """Empêcher l'ajout manuel de points GPS"""
        return False


# Personnalisation du site admin
admin.site.site_header = "Coach AI Administration"
admin.site.site_title = "Coach AI Admin"
admin.site.index_title = "Gestion de la plateforme Coach AI"
