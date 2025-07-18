from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Activity(models.Model):
    """Modèle pour les activités sportives"""
    
    # Relations
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    
    # Identifiants externes
    activity_id = models.BigIntegerField(_('Activity ID'), unique=True, null=True, blank=True)
    garmin_id = models.BigIntegerField(_('Garmin ID'), null=True, blank=True)
    strava_id = models.BigIntegerField(_('Strava ID'), null=True, blank=True)
    
    # Informations de base
    activity_name = models.CharField(_('Activity name'), max_length=200)
    activity_type = models.CharField(
        _('Activity type'),
        max_length=50,
        choices=[
            ('running', _('Running')),
            ('cycling', _('Cycling')),
            ('swimming', _('Swimming')),
            ('walking', _('Walking')),
            ('hiking', _('Hiking')),
            ('strength_training', _('Strength Training')),
            ('yoga', _('Yoga')),
            ('other', _('Other')),
        ],
        default='running'
    )
    
    # Temps et distance
    start_time = models.DateTimeField(_('Start time'))
    end_time = models.DateTimeField(_('End time'), null=True, blank=True)
    duration_seconds = models.IntegerField(_('Duration (seconds)'), default=0)
    distance_meters = models.FloatField(_('Distance (meters)'), default=0.0)
    
    # Vitesse et allure
    average_speed = models.FloatField(_('Average speed (m/s)'), null=True, blank=True)
    max_speed = models.FloatField(_('Max speed (m/s)'), null=True, blank=True)
    average_pace = models.FloatField(_('Average pace (s/km)'), null=True, blank=True)
    
    # Fréquence cardiaque
    average_hr = models.IntegerField(
        _('Average heart rate'), 
        null=True, 
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(250)]
    )
    max_hr = models.IntegerField(
        _('Max heart rate'), 
        null=True, 
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(250)]
    )
    
    # Temps dans les zones de FC
    hr_zone_1_time = models.IntegerField(_('HR Zone 1 time (seconds)'), null=True, blank=True)
    hr_zone_2_time = models.IntegerField(_('HR Zone 2 time (seconds)'), null=True, blank=True)
    hr_zone_3_time = models.IntegerField(_('HR Zone 3 time (seconds)'), null=True, blank=True)
    hr_zone_4_time = models.IntegerField(_('HR Zone 4 time (seconds)'), null=True, blank=True)
    hr_zone_5_time = models.IntegerField(_('HR Zone 5 time (seconds)'), null=True, blank=True)
    
    # Élévation
    elevation_gain = models.FloatField(_('Elevation gain (m)'), null=True, blank=True)
    elevation_loss = models.FloatField(_('Elevation loss (m)'), null=True, blank=True)
    
    # Position GPS
    start_latitude = models.FloatField(_('Start latitude'), null=True, blank=True)
    start_longitude = models.FloatField(_('Start longitude'), null=True, blank=True)
    end_latitude = models.FloatField(_('End latitude'), null=True, blank=True)
    end_longitude = models.FloatField(_('End longitude'), null=True, blank=True)
    
    # Calories et effort
    calories = models.IntegerField(_('Calories burned'), null=True, blank=True)
    training_load = models.FloatField(_('Training load'), null=True, blank=True)
    aerobic_effect = models.FloatField(_('Aerobic training effect'), null=True, blank=True)
    anaerobic_effect = models.FloatField(_('Anaerobic training effect'), null=True, blank=True)
    
    # Données spécifiques course à pied
    steps = models.IntegerField(_('Steps'), null=True, blank=True)
    average_cadence = models.IntegerField(_('Average cadence (steps/min)'), null=True, blank=True)
    max_cadence = models.IntegerField(_('Max cadence (steps/min)'), null=True, blank=True)
    stride_length = models.FloatField(_('Average stride length (m)'), null=True, blank=True)
    
    # Performances
    vo2_max = models.FloatField(_('VO2 Max estimate'), null=True, blank=True)
    fastest_1k = models.FloatField(_('Fastest 1K (seconds)'), null=True, blank=True)
    fastest_5k = models.FloatField(_('Fastest 5K (seconds)'), null=True, blank=True)
    fastest_10k = models.FloatField(_('Fastest 10K (seconds)'), null=True, blank=True)
    
    # Conditions météo
    temperature = models.FloatField(_('Temperature (°C)'), null=True, blank=True)
    humidity = models.IntegerField(_('Humidity (%)'), null=True, blank=True)
    wind_speed = models.FloatField(_('Wind speed (km/h)'), null=True, blank=True)
    
    # Équipement
    device_name = models.CharField(_('Device name'), max_length=100, blank=True)
    
    # Ressenti et notes
    perceived_exertion = models.IntegerField(
        _('Perceived exertion (1-10)'), 
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    notes = models.TextField(_('Notes'), blank=True)
    
    # Statut
    is_race = models.BooleanField(_('Is race'), default=False)
    is_workout = models.BooleanField(_('Is workout'), default=False)
    is_manual = models.BooleanField(_('Manual entry'), default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    synced_at = models.DateTimeField(_('Last sync'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Activity')
        verbose_name_plural = _('Activities')
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['user', 'start_time']),
            models.Index(fields=['activity_type', 'start_time']),
            models.Index(fields=['user', 'activity_type']),
        ]
    
    def __str__(self):
        return f"{self.activity_name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def duration_formatted(self):
        """Durée formatée en HH:MM:SS"""
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    @property
    def distance_km(self):
        """Distance en kilomètres"""
        return round(self.distance_meters / 1000, 2) if self.distance_meters else 0
    
    @property
    def average_speed_kmh(self):
        """Vitesse moyenne en km/h"""
        if self.average_speed:
            return round(self.average_speed * 3.6, 2)
        return None
    
    @property
    def pace_per_km(self):
        """Allure en minutes par kilomètre"""
        if self.distance_meters > 0 and self.duration_seconds > 0:
            pace_seconds = (self.duration_seconds / self.distance_meters) * 1000
            minutes = int(pace_seconds // 60)
            seconds = int(pace_seconds % 60)
            return f"{minutes}:{seconds:02d}"
        return None


class ActivitySplit(models.Model):
    """Modèle pour les splits/segments d'activité"""
    
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='splits')
    
    # Informations du split
    split_index = models.IntegerField(_('Split index'))
    split_type = models.CharField(_('Split type'), max_length=50, default='kilometer')
    
    # Données du split
    distance_meters = models.FloatField(_('Distance (meters)'))
    duration_seconds = models.IntegerField(_('Duration (seconds)'))
    average_speed = models.FloatField(_('Average speed (m/s)'), null=True, blank=True)
    max_speed = models.FloatField(_('Max speed (m/s)'), null=True, blank=True)
    
    # Fréquence cardiaque
    average_hr = models.IntegerField(_('Average heart rate'), null=True, blank=True)
    max_hr = models.IntegerField(_('Max heart rate'), null=True, blank=True)
    
    # Élévation
    elevation_gain = models.FloatField(_('Elevation gain (m)'), null=True, blank=True)
    elevation_loss = models.FloatField(_('Elevation loss (m)'), null=True, blank=True)
    
    # Cadence
    average_cadence = models.IntegerField(_('Average cadence'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Activity Split')
        verbose_name_plural = _('Activity Splits')
        ordering = ['activity', 'split_index']
        unique_together = ['activity', 'split_index']
    
    def __str__(self):
        return f"{self.activity.activity_name} - Split {self.split_index}"
    
    @property
    def pace_per_km(self):
        """Allure du split en minutes par kilomètre"""
        if self.distance_meters > 0 and self.duration_seconds > 0:
            pace_seconds = (self.duration_seconds / self.distance_meters) * 1000
            minutes = int(pace_seconds // 60)
            seconds = int(pace_seconds % 60)
            return f"{minutes}:{seconds:02d}"
        return None


class GPSPoint(models.Model):
    """Modèle pour les points GPS d'une activité"""
    
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='gps_points')
    
    # Position
    latitude = models.FloatField(_('Latitude'))
    longitude = models.FloatField(_('Longitude'))
    altitude = models.FloatField(_('Altitude (m)'), null=True, blank=True)
    
    # Temps
    timestamp = models.DateTimeField(_('Timestamp'))
    elapsed_time = models.IntegerField(_('Elapsed time (seconds)'))
    
    # Données instantanées
    speed = models.FloatField(_('Speed (m/s)'), null=True, blank=True)
    heart_rate = models.IntegerField(_('Heart rate'), null=True, blank=True)
    cadence = models.IntegerField(_('Cadence'), null=True, blank=True)
    
    # Distance cumulée
    distance = models.FloatField(_('Cumulative distance (m)'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('GPS Point')
        verbose_name_plural = _('GPS Points')
        ordering = ['activity', 'timestamp']
        indexes = [
            models.Index(fields=['activity', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.activity.activity_name} - {self.timestamp}"