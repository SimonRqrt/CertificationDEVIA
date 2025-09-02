"""
Modèles flexibles pour l'évolution du schéma de données
Démonstration d'une approche hybride : relationnel + JSON
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class FlexibleActivity(models.Model):
    """
    Modèle d'activité flexible - Approche hybride pour évolutivité
    
    Objectifs :
    - Préserver la compatibilité avec le schéma relationnel existant
    - Permettre l'ingestion de données sources complètes
    - Faciliter les évolutions futures sans migration complexe
    """
    
    # === CHAMPS ESSENTIELS (Indexés pour performance) ===
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flexible_activities')
    activity_id = models.BigIntegerField(_('Activity ID'), unique=True)
    activity_name = models.CharField(_('Activity name'), max_length=200)
    activity_type = models.CharField(_('Activity type'), max_length=50, default='running')
    start_time = models.DateTimeField(_('Start time'))
    
    # === DONNÉES SOURCES COMPLÈTES (Flexibilité) ===
    garmin_raw_data = models.JSONField(
        _('Garmin raw data'),
        default=dict,
        help_text="Données complètes de l'API Garmin (format JSON)"
    )
    
    strava_raw_data = models.JSONField(
        _('Strava raw data'), 
        default=dict,
        help_text="Données complètes de l'API Strava (format JSON)"
    )
    
    # === MÉTRIQUES CALCULÉES (Extensible) ===
    computed_metrics = models.JSONField(
        _('Computed metrics'),
        default=dict,
        help_text="Métriques calculées par l'application (VMA, charge, etc.)"
    )
    
    # === MÉTADONNÉES ===
    schema_version = models.CharField(
        _('Schema version'),
        max_length=10,
        default='1.0',
        help_text="Version du schéma de données pour compatibilité"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    synced_at = models.DateTimeField(_('Last sync'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Flexible Activity')
        verbose_name_plural = _('Flexible Activities')
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['user', 'start_time']),
            models.Index(fields=['activity_type', 'start_time']),
            models.Index(fields=['user', 'activity_id']),
            # Index GIN pour requêtes JSON (PostgreSQL)
            models.Index(fields=['garmin_raw_data'], name='idx_garmin_data_gin'),
        ]
    
    def __str__(self):
        return f"{self.activity_name} - {self.start_time.strftime('%Y-%m-%d')}"
    
    # === PROPRIÉTÉS CALCULÉES (Rétro-compatibilité) ===
    
    @property
    def duration_seconds(self):
        """Durée extraite des données JSON"""
        return (
            self.garmin_raw_data.get('duration') or
            self.strava_raw_data.get('elapsed_time') or
            0
        )
    
    @property
    def distance_meters(self):
        """Distance extraite des données JSON"""
        return (
            self.garmin_raw_data.get('distance') or
            self.strava_raw_data.get('distance') or
            0.0
        )
    
    @property 
    def average_speed(self):
        """Vitesse moyenne extraite des données JSON"""
        return (
            self.garmin_raw_data.get('averageSpeed') or
            self.computed_metrics.get('average_speed') or
            None
        )
    
    @property
    def average_hr(self):
        """FC moyenne extraite des données JSON"""
        return (
            self.garmin_raw_data.get('averageHR') or
            self.strava_raw_data.get('average_heartrate') or
            None
        )
    
    # === MÉTHODES D'AGRÉGATION (Démonstration SQL) ===
    
    @classmethod
    def get_monthly_stats(cls, user_id, year, month):
        """
        Statistiques mensuelles avec requêtes JSON natives PostgreSQL
        Démonstration : SQL avancé + JSON flexible
        """
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_activities,
                    SUM((garmin_raw_data->>'distance')::float) as total_distance,
                    AVG((garmin_raw_data->>'duration')::integer) as avg_duration,
                    AVG((garmin_raw_data->>'averageHR')::integer) as avg_hr
                FROM activities_flexibleactivity 
                WHERE user_id = %s 
                AND EXTRACT(YEAR FROM start_time) = %s
                AND EXTRACT(MONTH FROM start_time) = %s
                AND garmin_raw_data ? 'distance'
            """, [user_id, year, month])
            
            return cursor.fetchone()
    
    @classmethod
    def get_performance_evolution(cls, user_id, activity_type='running'):
        """
        Évolution des performances avec requêtes JSON avancées
        Démonstration : Analyse temporelle + JSON
        """
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    DATE_TRUNC('week', start_time) as week,
                    AVG((garmin_raw_data->>'averageSpeed')::float) as avg_speed,
                    AVG((garmin_raw_data->>'vO2MaxValue')::float) as avg_vo2max,
                    COUNT(*) as activity_count
                FROM activities_flexibleactivity
                WHERE user_id = %s 
                AND activity_type = %s
                AND garmin_raw_data ? 'averageSpeed'
                GROUP BY DATE_TRUNC('week', start_time)
                ORDER BY week DESC
                LIMIT 12
            """, [user_id, activity_type])
            
            return cursor.fetchall()


class DataMigrationLog(models.Model):
    """
    Log des migrations entre ancien et nouveau schéma
    Démonstration : Traçabilité et gestion des versions
    """
    
    old_activity_id = models.IntegerField(_('Old Activity ID'))
    new_activity_id = models.IntegerField(_('New Activity ID'))
    migration_type = models.CharField(
        _('Migration type'),
        max_length=50,
        choices=[
            ('initial', _('Initial migration')),
            ('update', _('Data update')),
            ('enrichment', _('Data enrichment')),
        ]
    )
    
    data_differences = models.JSONField(
        _('Data differences'),
        default=dict,
        help_text="Différences détectées lors de la migration"
    )
    
    migration_date = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    class Meta:
        verbose_name = _('Data Migration Log')
        verbose_name_plural = _('Data Migration Logs')
        ordering = ['-migration_date']


class SchemaEvolution(models.Model):
    """
    Suivi de l'évolution du schéma pour compatibilité
    Démonstration : Gestion des versions et rétrocompatibilité
    """
    
    version = models.CharField(_('Schema version'), max_length=10, unique=True)
    description = models.TextField(_('Description'))
    migration_script = models.TextField(
        _('Migration script'),
        help_text="Script SQL/Python pour migration automatique"
    )
    
    fields_added = models.JSONField(
        _('Fields added'),
        default=list,
        help_text="Nouveaux champs ajoutés dans cette version"
    )
    
    fields_deprecated = models.JSONField(
        _('Fields deprecated'), 
        default=list,
        help_text="Champs dépréciés dans cette version"
    )
    
    release_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _('Schema Evolution')
        verbose_name_plural = _('Schema Evolutions')
        ordering = ['-release_date']
    
    def __str__(self):
        return f"Schema v{self.version} - {self.description}"