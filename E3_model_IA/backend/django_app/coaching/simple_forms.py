from django import forms
from django.utils.translation import gettext_lazy as _


class SimplePlanGenerationForm(forms.Form):
    """Formulaire simplifié pour générer un plan d'entraînement avec l'IA"""
    
    goal = forms.ChoiceField(
        label=_('Objectif principal'),
        choices=[
            ('5k', _('5 kilomètres - Course courte')),
            ('10k', _('10 kilomètres - Distance intermédiaire')),
            ('half_marathon', _('Semi-marathon (21,1 km)')),
            ('marathon', _('Marathon (42,2 km)')),
            ('fitness', _('Forme générale - Rester en forme')),
            ('endurance', _('Améliorer mon endurance')),
            ('speed', _('Courir plus vite'))
        ],
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'style': 'font-size: 1.1rem;'
        })
    )
    
    level = forms.ChoiceField(
        label=_('Votre niveau actuel'),
        choices=[
            ('beginner', _('🏃‍♀️ Débutant - Je commence la course')),
            ('intermediate', _('🏃‍♂️ Intermédiaire - Je cours régulièrement')),
            ('advanced', _('🏃‍♀️ Avancé - J\'ai de l\'expérience'))
        ],
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'style': 'font-size: 1.1rem;'
        })
    )
    
    sessions_per_week = forms.ChoiceField(
        label=_('Combien de fois par semaine pouvez-vous vous entraîner ?'),
        choices=[
            ('2', _('2 fois par semaine')),
            ('3', _('3 fois par semaine')),
            ('4', _('4 fois par semaine')),
            ('5', _('5 fois par semaine')),
            ('6', _('6 fois par semaine'))
        ],
        initial='3',
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'style': 'font-size: 1.1rem;'
        })
    )
    
    target_date = forms.DateField(
        label=_('Date cible (optionnel)'),
        required=False,
        help_text=_('Si vous avez une course ou un objectif précis en tête'),
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-lg',
            'style': 'font-size: 1.1rem;'
        })
    )
    
    additional_notes = forms.CharField(
        label=_('Notes supplémentaires (optionnel)'),
        required=False,
        help_text=_("Blessures, contraintes particulières, préférences..."),
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Ex: Je préfère courir le matin, j\'ai eu une blessure au genou...',
            'style': 'font-size: 1rem;'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Ajouter des classes Bootstrap pour un meilleur rendu
        for field_name, field in self.fields.items():
            if hasattr(field.widget, 'attrs'):
                field.widget.attrs.update({
                    'class': field.widget.attrs.get('class', '') + ' mb-3'
                })