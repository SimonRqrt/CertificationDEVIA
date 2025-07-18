from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class TrainingPlan(models.Model):
    """Modèle pour les plans d'entraînement"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='training_plans')
    
    # Informations de base
    name = models.CharField(_('Plan name'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    
    # Objectif du plan
    goal = models.CharField(
        _('Goal'),
        max_length=100,
        choices=[
            ('5k', _('5K Race')),
            ('10k', _('10K Race')),
            ('half_marathon', _('Half Marathon')),
            ('marathon', _('Marathon')),
            ('weight_loss', _('Weight Loss')),
            ('endurance', _('Endurance')),
            ('speed', _('Speed')),
            ('general_fitness', _('General Fitness')),
        ]
    )
    
    # Durée et dates
    duration_weeks = models.IntegerField(_('Duration (weeks)'), validators=[MinValueValidator(1)])
    start_date = models.DateField(_('Start date'))
    end_date = models.DateField(_('End date'))
    
    # Niveau et fréquence
    level = models.CharField(
        _('Level'),
        max_length=50,
        choices=[
            ('beginner', _('Beginner')),
            ('intermediate', _('Intermediate')),
            ('advanced', _('Advanced')),
        ]
    )
    
    sessions_per_week = models.IntegerField(
        _('Sessions per week'), 
        validators=[MinValueValidator(1), MaxValueValidator(7)]
    )
    
    # Statut
    is_active = models.BooleanField(_('Is active'), default=False)
    is_completed = models.BooleanField(_('Is completed'), default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Training Plan')
        verbose_name_plural = _('Training Plans')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.user.email}"


class WorkoutSession(models.Model):
    """Modèle pour les séances d'entraînement"""
    
    training_plan = models.ForeignKey(
        TrainingPlan, 
        on_delete=models.CASCADE, 
        related_name='sessions',
        null=True,
        blank=True
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_sessions')
    
    # Informations de base
    name = models.CharField(_('Session name'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    
    # Type de séance
    session_type = models.CharField(
        _('Session type'),
        max_length=50,
        choices=[
            ('easy_run', _('Easy Run')),
            ('long_run', _('Long Run')),
            ('tempo_run', _('Tempo Run')),
            ('interval_training', _('Interval Training')),
            ('fartlek', _('Fartlek')),
            ('hill_training', _('Hill Training')),
            ('recovery_run', _('Recovery Run')),
            ('race_pace', _('Race Pace')),
            ('cross_training', _('Cross Training')),
            ('rest', _('Rest')),
        ]
    )
    
    # Planification
    planned_date = models.DateField(_('Planned date'))
    planned_duration = models.IntegerField(_('Planned duration (minutes)'))
    planned_distance = models.FloatField(_('Planned distance (km)'), null=True, blank=True)
    
    # Zones cibles
    target_hr_zone = models.IntegerField(
        _('Target HR zone'),
        choices=[(i, f'Zone {i}') for i in range(1, 6)],
        null=True,
        blank=True
    )
    target_pace_min = models.FloatField(_('Target pace min (s/km)'), null=True, blank=True)
    target_pace_max = models.FloatField(_('Target pace max (s/km)'), null=True, blank=True)
    
    # Statut
    status = models.CharField(
        _('Status'),
        max_length=50,
        choices=[
            ('planned', _('Planned')),
            ('in_progress', _('In Progress')),
            ('completed', _('Completed')),
            ('skipped', _('Skipped')),
            ('rescheduled', _('Rescheduled')),
        ],
        default='planned'
    )
    
    # Résultats (après réalisation)
    actual_date = models.DateField(_('Actual date'), null=True, blank=True)
    actual_duration = models.IntegerField(_('Actual duration (minutes)'), null=True, blank=True)
    actual_distance = models.FloatField(_('Actual distance (km)'), null=True, blank=True)
    
    # Relation avec l'activité réalisée
    activity = models.OneToOneField(
        'activities.Activity',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='planned_session'
    )
    
    # Feedback
    perceived_exertion = models.IntegerField(
        _('Perceived exertion (1-10)'), 
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    notes = models.TextField(_('Notes'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Workout Session')
        verbose_name_plural = _('Workout Sessions')
        ordering = ['planned_date']
        indexes = [
            models.Index(fields=['user', 'planned_date']),
            models.Index(fields=['training_plan', 'planned_date']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.planned_date}"


class CoachingSession(models.Model):
    """Modèle pour les sessions de coaching IA"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coaching_sessions')
    
    # Informations de la session
    session_id = models.CharField(_('Session ID'), max_length=100, unique=True)
    title = models.CharField(_('Title'), max_length=200, blank=True)
    
    # Contenu
    user_message = models.TextField(_('User message'))
    ai_response = models.TextField(_('AI response'))
    
    # Contexte
    context_data = models.JSONField(_('Context data'), default=dict, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    response_time = models.FloatField(_('Response time (seconds)'), null=True, blank=True)
    
    # Qualité de la réponse
    user_rating = models.IntegerField(
        _('User rating (1-5)'),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    user_feedback = models.TextField(_('User feedback'), blank=True)
    
    class Meta:
        verbose_name = _('Coaching Session')
        verbose_name_plural = _('Coaching Sessions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"Session {self.session_id} - {self.user.email}"


class PerformanceMetrics(models.Model):
    """Modèle pour les métriques de performance calculées"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_metrics')
    
    # Date de calcul
    calculation_date = models.DateField(_('Calculation date'))
    
    # Métriques de performance
    vma = models.FloatField(_('VMA (km/h)'), null=True, blank=True)
    vo2_max = models.FloatField(_('VO2 Max'), null=True, blank=True)
    
    # Charge d'entraînement
    fitness_7d = models.FloatField(_('Fitness 7 days'), null=True, blank=True)
    fitness_28d = models.FloatField(_('Fitness 28 days'), null=True, blank=True)
    fatigue_7d = models.FloatField(_('Fatigue 7 days'), null=True, blank=True)
    form = models.FloatField(_('Form'), null=True, blank=True)
    
    # Prédictions de performance
    prediction_5k = models.TimeField(_('5K prediction'), null=True, blank=True)
    prediction_10k = models.TimeField(_('10K prediction'), null=True, blank=True)
    prediction_half_marathon = models.TimeField(_('Half marathon prediction'), null=True, blank=True)
    prediction_marathon = models.TimeField(_('Marathon prediction'), null=True, blank=True)
    
    # Profil d'endurance
    endurance_ratio = models.FloatField(_('Endurance ratio'), null=True, blank=True)
    
    # Recommandations
    recommendation = models.TextField(_('Recommendation'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Performance Metrics')
        verbose_name_plural = _('Performance Metrics')
        ordering = ['-calculation_date']
        unique_together = ['user', 'calculation_date']
        indexes = [
            models.Index(fields=['user', 'calculation_date']),
        ]
    
    def __str__(self):
        return f"Metrics {self.user.email} - {self.calculation_date}"


class Goal(models.Model):
    """Modèle pour les objectifs utilisateur"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    
    # Informations de base
    name = models.CharField(_('Goal name'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    
    # Type d'objectif
    goal_type = models.CharField(
        _('Goal type'),
        max_length=50,
        choices=[
            ('time_goal', _('Time Goal')),
            ('distance_goal', _('Distance Goal')),
            ('frequency_goal', _('Frequency Goal')),
            ('weight_goal', _('Weight Goal')),
            ('fitness_goal', _('Fitness Goal')),
        ]
    )
    
    # Valeurs cibles
    target_value = models.FloatField(_('Target value'))
    target_unit = models.CharField(_('Target unit'), max_length=50)
    
    # Dates
    target_date = models.DateField(_('Target date'))
    created_date = models.DateField(_('Created date'), auto_now_add=True)
    
    # Statut
    is_active = models.BooleanField(_('Is active'), default=True)
    is_achieved = models.BooleanField(_('Is achieved'), default=False)
    achievement_date = models.DateField(_('Achievement date'), null=True, blank=True)
    
    # Valeur actuelle
    current_value = models.FloatField(_('Current value'), null=True, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Goal')
        verbose_name_plural = _('Goals')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'target_date']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.user.email}"
    
    @property
    def progress_percentage(self):
        """Calcul du pourcentage de progression"""
        if self.current_value is not None and self.target_value:
            return min(100, (self.current_value / self.target_value) * 100)
        return 0