from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta, date
from .models import TrainingPlan, WorkoutSession, Goal


class PersonalInfoForm(forms.Form):
    """Étape 1 : Informations personnelles de l'utilisateur"""
    
    age = forms.IntegerField(
        label=_('Âge'),
        min_value=16,
        max_value=100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Votre âge'
        })
    )
    
    weight = forms.FloatField(
        label=_('Poids (kg)'),
        min_value=30.0,
        max_value=200.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Poids en kg',
            'step': 0.1
        })
    )
    
    height = forms.IntegerField(
        label=_('Taille (cm)'),
        min_value=120,
        max_value=250,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Taille en cm'
        })
    )
    
    gender = forms.ChoiceField(
        label=_('Sexe'),
        choices=[
            ('M', _('Homme')),
            ('F', _('Femme')),
            ('Other', _('Autre'))
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    experience_level = forms.ChoiceField(
        label=_('Niveau d\'expérience en course à pied'),
        choices=[
            ('beginner', _('Débutant (moins de 6 mois)')),
            ('novice', _('Novice (6 mois - 2 ans)')),
            ('intermediate', _('Intermédiaire (2-5 ans)')),
            ('advanced', _('Avancé (5+ ans)')),
            ('elite', _('Élite/Compétition'))
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    current_weekly_km = forms.FloatField(
        label=_('Kilométrage hebdomadaire actuel'),
        min_value=0.0,
        max_value=200.0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'km par semaine',
            'step': 1
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Préremplir avec les données du profil utilisateur si disponible
        if self.user and hasattr(self.user, 'profile'):
            profile = self.user.profile
            if profile.weight:
                self.fields['weight'].initial = profile.weight
            if profile.height:
                self.fields['height'].initial = profile.height
            if profile.birth_date:
                age = timezone.now().year - profile.birth_date.year
                self.fields['age'].initial = age


class RunningGoalWizardForm(forms.Form):
    """Étape 2 : Définition de l'objectif running"""
    
    race_type = forms.ChoiceField(
        label=_('Type d\'objectif'),
        choices=[
            ('5k', _('5 kilomètres')),
            ('10k', _('10 kilomètres')),
            ('half_marathon', _('Semi-marathon (21,1 km)')),
            ('marathon', _('Marathon (42,2 km)')),
            ('general_fitness', _('Forme générale')),
            ('weight_loss', _('Perte de poids')),
            ('endurance', _('Améliorer l\'endurance')),
            ('speed', _('Améliorer la vitesse'))
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    target_date = forms.DateField(
        label=_('Date cible (optionnel)'),
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    target_time = forms.CharField(
        label=_('Temps objectif (HH:MM:SS)'),
        required=False,
        max_length=8,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '01:45:00',
            'pattern': '[0-9]{1,2}:[0-9]{2}:[0-9]{2}'
        })
    )
    
    current_best_time = forms.CharField(
        label=_('Meilleur temps actuel (HH:MM:SS)'),
        required=False,
        max_length=8,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '02:00:00',
            'pattern': '[0-9]{1,2}:[0-9]{2}:[0-9]{2}'
        })
    )
    
    priority = forms.ChoiceField(
        label=_('Priorité de cet objectif'),
        choices=[
            ('low', _('Basse - Un objectif parmi d\'autres')),
            ('medium', _('Moyenne - Important mais pas critique')),
            ('high', _('Haute - Objectif principal')),
            ('critical', _('Critique - Mon focus principal'))
        ],
        initial='medium',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    motivation = forms.CharField(
        label=_('Pourquoi ce défi vous motive-t-il ?'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Décrivez vos motivations, vos raisons personnelles...'
        })
    )
    
    def clean_target_date(self):
        target_date = self.cleaned_data.get('target_date')
        if target_date and target_date <= timezone.now().date():
            raise ValidationError('La date cible doit être dans le futur.')
        return target_date
    
    def clean_target_time(self):
        target_time = self.cleaned_data.get('target_time')
        if target_time:
            try:
                # Valider le format HH:MM:SS
                parts = target_time.split(':')
                if len(parts) != 3:
                    raise ValueError
                h, m, s = map(int, parts)
                if h < 0 or h > 23 or m < 0 or m > 59 or s < 0 or s > 59:
                    raise ValueError
            except ValueError:
                raise ValidationError('Format invalide. Utilisez HH:MM:SS (ex: 01:45:30)')
        return target_time
    
    def clean_current_best_time(self):
        current_best = self.cleaned_data.get('current_best_time')
        if current_best:
            try:
                parts = current_best.split(':')
                if len(parts) != 3:
                    raise ValueError
                h, m, s = map(int, parts)
                if h < 0 or h > 23 or m < 0 or m > 59 or s < 0 or s > 59:
                    raise ValueError
            except ValueError:
                raise ValidationError('Format invalide. Utilisez HH:MM:SS (ex: 02:00:15)')
        return current_best


class TrainingPreferencesForm(forms.Form):
    """Étape 3 : Préférences d'entraînement"""
    
    sessions_per_week = forms.IntegerField(
        label=_('Nombre de séances par semaine'),
        min_value=2,
        max_value=7,
        initial=3,
        widget=forms.Select(
            choices=[(i, f'{i} séance{"s" if i > 1 else ""}') for i in range(2, 8)],
            attrs={'class': 'form-select'}
        )
    )
    
    available_days = forms.MultipleChoiceField(
        label=_('Jours disponibles pour l\'entraînement'),
        choices=[
            ('monday', _('Lundi')),
            ('tuesday', _('Mardi')),
            ('wednesday', _('Mercredi')),
            ('thursday', _('Jeudi')),
            ('friday', _('Vendredi')),
            ('saturday', _('Samedi')),
            ('sunday', _('Dimanche'))
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True
    )
    
    preferred_duration = forms.ChoiceField(
        label=_('Durée préférée par séance'),
        choices=[
            ('short', _('Court (20-40 min)')),
            ('medium', _('Moyen (40-60 min)')),
            ('long', _('Long (60-90 min)')),
            ('variable', _('Variable selon le type de séance'))
        ],
        initial='medium',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    training_environment = forms.MultipleChoiceField(
        label=_('Où préférez-vous vous entraîner ?'),
        choices=[
            ('outdoor', _('En extérieur')),
            ('treadmill', _('Tapis de course')),
            ('track', _('Piste d\'athlétisme')),
            ('trail', _('Sentiers/trails')),
            ('gym', _('Salle de sport'))
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True
    )
    
    current_level = forms.ChoiceField(
        label=_('Comment évaluez-vous votre niveau actuel ?'),
        choices=[
            ('beginner', _('Débutant - Je commence la course à pied')),
            ('intermediate', _('Intermédiaire - Je cours régulièrement')),
            ('advanced', _('Avancé - J\'ai de l\'expérience en compétition')),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    injury_history = forms.BooleanField(
        label=_('Avez-vous des antécédents de blessures ?'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    injury_details = forms.CharField(
        label=_('Détails sur les blessures (optionnel)'),
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Type de blessures, zones sensibles...'
        })
    )
    
    cross_training = forms.MultipleChoiceField(
        label=_('Activités complémentaires que vous pratiquez'),
        choices=[
            ('cycling', _('Vélo')),
            ('swimming', _('Natation')),
            ('yoga', _('Yoga')),
            ('strength_training', _('Musculation')),
            ('hiking', _('Randonnée')),
            ('none', _('Aucune autre activité'))
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    
    def clean_available_days(self):
        days = self.cleaned_data.get('available_days')
        sessions = self.data.get('sessions_per_week')
        
        if days and sessions and len(days) < int(sessions):
            raise ValidationError(
                f'Vous devez sélectionner au moins {sessions} jours '
                f'pour {sessions} séances par semaine.'
            )
        return days


class PlanGenerationForm(forms.Form):
    """Étape 4 : Options de génération du plan"""
    
    plan_name = forms.CharField(
        label=_('Nom du plan'),
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sera généré automatiquement si vide'
        })
    )
    
    include_strength = forms.BooleanField(
        label=_('Inclure des séances de renforcement musculaire'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_recovery = forms.BooleanField(
        label=_('Inclure des séances de récupération active'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    periodization_type = forms.ChoiceField(
        label=_('Type de périodisation'),
        choices=[
            ('linear', _('Linéaire - Progression régulière')),
            ('undulating', _('Ondulée - Variation semaine par semaine')),
            ('block', _('Par blocs - Phases spécialisées')),
            ('auto', _('Automatique - Laissez l\'IA décider'))
        ],
        initial='auto',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    emphasis = forms.ChoiceField(
        label=_('Accent principal du plan'),
        choices=[
            ('balanced', _('Équilibré')),
            ('endurance', _('Endurance')),
            ('speed', _('Vitesse')),
            ('strength', _('Force')),
            ('recovery', _('Récupération'))
        ],
        initial='balanced',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class QuickGoalForm(forms.ModelForm):
    """Formulaire rapide pour créer un objectif"""
    
    class Meta:
        model = Goal
        fields = [
            'name', 'goal_type', 'target_value', 'target_unit',
            'target_date', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Courir un 10K'
            }),
            'goal_type': forms.Select(attrs={'class': 'form-select'}),
            'target_value': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Valeur cible'
            }),
            'target_unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Unité (minutes, km, etc.)'
            }),
            'target_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description de l\'objectif...'
            })
        }
        labels = {
            'name': _('Nom de l\'objectif'),
            'goal_type': _('Type d\'objectif'),
            'target_value': _('Valeur cible'),
            'target_unit': _('Unité'),
            'target_date': _('Date cible'),
            'description': _('Description'),
        }
    
    def clean_target_date(self):
        target_date = self.cleaned_data.get('target_date')
        if target_date and target_date <= timezone.now().date():
            raise ValidationError('La date cible doit être dans le futur.')
        return target_date


class TrainingPlanFilterForm(forms.Form):
    """Formulaire de filtrage des plans d'entraînement"""
    
    goal = forms.ChoiceField(
        label=_('Objectif'),
        choices=[('', _('Tous'))] + TrainingPlan._meta.get_field('goal').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    level = forms.ChoiceField(
        label=_('Niveau'),
        choices=[('', _('Tous'))] + TrainingPlan._meta.get_field('level').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    is_active = forms.BooleanField(
        label=_('Plans actifs seulement'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    is_completed = forms.BooleanField(
        label=_('Plans terminés seulement'),
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class SessionUpdateForm(forms.ModelForm):
    """Formulaire pour mettre à jour une séance d'entraînement"""
    
    class Meta:
        model = WorkoutSession
        fields = [
            'status', 'actual_date', 'actual_duration', 'actual_distance',
            'perceived_exertion', 'notes'
        ]
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'actual_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'actual_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Minutes'
            }),
            'actual_distance': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kilomètres',
                'step': 0.1
            }),
            'perceived_exertion': forms.Select(
                choices=[(i, f"{i}/10") for i in range(1, 11)],
                attrs={'class': 'form-select'}
            ),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes sur la séance...'
            })
        }
        labels = {
            'status': _('Statut'),
            'actual_date': _('Date réelle'),
            'actual_duration': _('Durée réelle (min)'),
            'actual_distance': _('Distance réelle (km)'),
            'perceived_exertion': _('Effort perçu'),
            'notes': _('Notes'),
        }