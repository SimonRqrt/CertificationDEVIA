from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Activity


class ActivityForm(forms.ModelForm):
    """Formulaire pour créer/modifier une activité"""
    
    class Meta:
        model = Activity
        fields = [
            'activity_name', 'activity_type', 'start_time',
            'duration_seconds', 'distance_meters',
            'average_hr', 'max_hr', 'calories',
            'perceived_exertion', 'notes',
            'is_race', 'is_workout'
        ]
        widgets = {
            'start_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'activity_name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ex: Course matinale'}
            ),
            'activity_type': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'duration_seconds': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Durée en secondes'}
            ),
            'distance_meters': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Distance en mètres'}
            ),
            'average_hr': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'FC moyenne'}
            ),
            'max_hr': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'FC maximale'}
            ),
            'calories': forms.NumberInput(
                attrs={'class': 'form-control', 'placeholder': 'Calories brûlées'}
            ),
            'perceived_exertion': forms.Select(
                choices=[(i, f"{i}/10") for i in range(1, 11)],
                attrs={'class': 'form-select'}
            ),
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control', 
                    'rows': 3,
                    'placeholder': 'Notes sur la séance...'
                }
            ),
            'is_race': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_workout': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'activity_name': _('Nom de l\'activité'),
            'activity_type': _('Type d\'activité'),
            'start_time': _('Heure de début'),
            'duration_seconds': _('Durée (secondes)'),
            'distance_meters': _('Distance (mètres)'),
            'average_hr': _('FC moyenne (bpm)'),
            'max_hr': _('FC maximale (bpm)'),
            'calories': _('Calories'),
            'perceived_exertion': _('Effort perçu'),
            'notes': _('Notes'),
            'is_race': _('Course/Compétition'),
            'is_workout': _('Séance d\'entraînement'),
        }
    
    # Champs helper pour saisie plus facile
    duration_hours = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Heures'}),
        label=_('Heures')
    )
    duration_minutes = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minutes'}),
        label=_('Minutes')
    )
    distance_km = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Distance en km'}),
        label=_('Distance (km)')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Préremplir les champs helper si on édite
        if self.instance.pk:
            if self.instance.duration_seconds:
                hours = self.instance.duration_seconds // 3600
                minutes = (self.instance.duration_seconds % 3600) // 60
                self.fields['duration_hours'].initial = hours
                self.fields['duration_minutes'].initial = minutes
            
            if self.instance.distance_meters:
                self.fields['distance_km'].initial = self.instance.distance_meters / 1000
        
        # Définir l'heure par défaut à maintenant
        if not self.instance.pk:
            self.fields['start_time'].initial = timezone.now().strftime('%Y-%m-%dT%H:%M')
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Conversion durée helper -> secondes
        hours = cleaned_data.get('duration_hours', 0) or 0
        minutes = cleaned_data.get('duration_minutes', 0) or 0
        
        if hours or minutes:
            cleaned_data['duration_seconds'] = (hours * 3600) + (minutes * 60)
        
        # Conversion distance helper -> mètres
        distance_km = cleaned_data.get('distance_km')
        if distance_km:
            cleaned_data['distance_meters'] = distance_km * 1000
        
        # Validations
        self._validate_duration(cleaned_data)
        self._validate_distance(cleaned_data)
        self._validate_heart_rate(cleaned_data)
        self._validate_start_time(cleaned_data)
        
        return cleaned_data
    
    def _validate_duration(self, cleaned_data):
        """Validation de la durée"""
        duration = cleaned_data.get('duration_seconds', 0)
        if duration <= 0:
            raise ValidationError(_('La durée doit être positive'))
        if duration > 86400:  # 24h
            raise ValidationError(_('La durée ne peut pas dépasser 24 heures'))
    
    def _validate_distance(self, cleaned_data):
        """Validation de la distance"""
        distance = cleaned_data.get('distance_meters', 0)
        if distance <= 0:
            raise ValidationError(_('La distance doit être positive'))
        if distance > 300000:  # 300km
            raise ValidationError(_('La distance ne peut pas dépasser 300km'))
    
    def _validate_heart_rate(self, cleaned_data):
        """Validation de la fréquence cardiaque"""
        avg_hr = cleaned_data.get('average_hr')
        max_hr = cleaned_data.get('max_hr')
        
        if avg_hr and (avg_hr < 30 or avg_hr > 250):
            raise ValidationError(_('FC moyenne invalide (30-250 bpm)'))
        
        if max_hr and (max_hr < 30 or max_hr > 250):
            raise ValidationError(_('FC maximale invalide (30-250 bpm)'))
        
        if avg_hr and max_hr and max_hr < avg_hr:
            raise ValidationError(_('La FC max ne peut pas être inférieure à la FC moyenne'))
    
    def _validate_start_time(self, cleaned_data):
        """Validation de l'heure de début"""
        start_time = cleaned_data.get('start_time')
        if start_time and start_time > timezone.now():
            raise ValidationError(_('L\'activité ne peut pas être dans le futur'))


class ActivityFilterForm(forms.Form):
    """Formulaire de filtrage des activités"""
    
    ACTIVITY_CHOICES = [
        ('', _('Tous les types')),
        ('running', _('Course à pied')),
        ('cycling', _('Vélo')),
        ('swimming', _('Natation')),
        ('walking', _('Marche')),
        ('hiking', _('Randonnée')),
        ('strength_training', _('Musculation')),
        ('yoga', _('Yoga')),
        ('other', _('Autre')),
    ]
    
    PERIOD_CHOICES = [
        ('', _('Période personnalisée')),
        ('7', _('7 derniers jours')),
        ('30', _('30 derniers jours')),
        ('90', _('3 derniers mois')),
        ('365', _('12 derniers mois')),
    ]
    
    activity_type = forms.ChoiceField(
        choices=ACTIVITY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Type d\'activité')
    )
    
    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Période')
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label=_('Du')
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label=_('Au')
    )
    
    min_distance = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'km'}),
        label=_('Distance min (km)')
    )
    
    max_distance = forms.FloatField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'km'}),
        label=_('Distance max (km)')
    )
    
    is_race = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Courses seulement')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Gérer les dates automatiques selon la période
        period = self.data.get('period')
        if period:
            try:
                days = int(period)
                date_to = timezone.now().date()
                date_from = date_to - timedelta(days=days)
                self.fields['date_from'].initial = date_from
                self.fields['date_to'].initial = date_to
            except ValueError:
                pass
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Validation des dates
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError(_('La date de début ne peut pas être postérieure à la date de fin'))
        
        # Validation des distances
        min_distance = cleaned_data.get('min_distance')
        max_distance = cleaned_data.get('max_distance')
        
        if min_distance and max_distance and min_distance > max_distance:
            raise ValidationError(_('La distance min ne peut pas être supérieure à la distance max'))
        
        return cleaned_data


class QuickActivityForm(forms.Form):
    """Formulaire rapide pour saisie d'activité"""
    
    activity_type = forms.ChoiceField(
        choices=Activity._meta.get_field('activity_type').choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Type')
    )
    
    duration_minutes = forms.IntegerField(
        min_value=1,
        max_value=1440,  # 24h
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minutes'}),
        label=_('Durée (min)')
    )
    
    distance_km = forms.FloatField(
        min_value=0.1,
        max_value=300,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'km'}),
        label=_('Distance (km)')
    )
    
    effort = forms.IntegerField(
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '1-10'}),
        label=_('Effort ressenti')
    )
    
    def save(self, user):
        """Créer l'activité à partir du formulaire rapide"""
        data = self.cleaned_data
        
        activity = Activity.objects.create(
            user=user,
            activity_name=f"{data['activity_type'].title()} - {timezone.now().strftime('%d/%m/%Y')}",
            activity_type=data['activity_type'],
            start_time=timezone.now() - timedelta(minutes=data['duration_minutes']),
            end_time=timezone.now(),
            duration_seconds=data['duration_minutes'] * 60,
            distance_meters=data['distance_km'] * 1000,
            perceived_exertion=data['effort'],
            is_manual=True
        )
        
        return activity