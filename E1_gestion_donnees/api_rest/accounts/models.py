from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Modèle utilisateur personnalisé pour l'application Coach AI"""
    
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    
    # Informations sportives
    birth_date = models.DateField(_('birth date'), null=True, blank=True)
    weight = models.FloatField(_('weight (kg)'), null=True, blank=True)
    height = models.FloatField(_('height (cm)'), null=True, blank=True)
    
    # Préférences d'entraînement
    preferred_activity = models.CharField(
        _('preferred activity'),
        max_length=50,
        choices=[
            ('running', _('Running')),
            ('cycling', _('Cycling')),
            ('swimming', _('Swimming')),
            ('triathlon', _('Triathlon')),
            ('other', _('Other')),
        ],
        default='running'
    )
    
    # Objectifs
    main_goal = models.CharField(
        _('main goal'),
        max_length=100,
        choices=[
            ('weight_loss', _('Weight Loss')),
            ('endurance', _('Endurance')),
            ('speed', _('Speed')),
            ('strength', _('Strength')),
            ('general_fitness', _('General Fitness')),
            ('competition', _('Competition')),
        ],
        default='general_fitness'
    )
    
    # Connexions externes
    garmin_email = models.EmailField(_('Garmin email'), blank=True)
    strava_connected = models.BooleanField(_('Strava connected'), default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_premium = models.BooleanField(_('Premium user'), default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        
    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"
        
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def bmi(self):
        """Calcul de l'IMC si poids et taille disponibles"""
        if self.weight and self.height:
            return round(self.weight / ((self.height / 100) ** 2), 2)
        return None


class UserProfile(models.Model):
    """Profil utilisateur étendu avec données de performance"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Métriques de performance
    vma = models.FloatField(_('VMA (km/h)'), null=True, blank=True)
    resting_heart_rate = models.IntegerField(_('Resting heart rate'), null=True, blank=True)
    max_heart_rate = models.IntegerField(_('Max heart rate'), null=True, blank=True)
    vo2_max = models.FloatField(_('VO2 Max'), null=True, blank=True)
    
    # Zones de fréquence cardiaque
    hr_zone_1_min = models.IntegerField(_('HR Zone 1 Min'), null=True, blank=True)
    hr_zone_1_max = models.IntegerField(_('HR Zone 1 Max'), null=True, blank=True)
    hr_zone_2_min = models.IntegerField(_('HR Zone 2 Min'), null=True, blank=True)
    hr_zone_2_max = models.IntegerField(_('HR Zone 2 Max'), null=True, blank=True)
    hr_zone_3_min = models.IntegerField(_('HR Zone 3 Min'), null=True, blank=True)
    hr_zone_3_max = models.IntegerField(_('HR Zone 3 Max'), null=True, blank=True)
    hr_zone_4_min = models.IntegerField(_('HR Zone 4 Min'), null=True, blank=True)
    hr_zone_4_max = models.IntegerField(_('HR Zone 4 Max'), null=True, blank=True)
    hr_zone_5_min = models.IntegerField(_('HR Zone 5 Min'), null=True, blank=True)
    hr_zone_5_max = models.IntegerField(_('HR Zone 5 Max'), null=True, blank=True)
    
    # Prédictions de performance
    prediction_5k = models.TimeField(_('5K prediction'), null=True, blank=True)
    prediction_10k = models.TimeField(_('10K prediction'), null=True, blank=True)
    prediction_half_marathon = models.TimeField(_('Half marathon prediction'), null=True, blank=True)
    prediction_marathon = models.TimeField(_('Marathon prediction'), null=True, blank=True)
    
    # Charge d'entraînement
    current_fitness = models.FloatField(_('Current fitness'), null=True, blank=True)
    current_fatigue = models.FloatField(_('Current fatigue'), null=True, blank=True)
    current_form = models.FloatField(_('Current form'), null=True, blank=True)
    
    # Métadonnées
    last_sync = models.DateTimeField(_('Last sync'), null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
        
    def __str__(self):
        return f"Profile de {self.user.email}"