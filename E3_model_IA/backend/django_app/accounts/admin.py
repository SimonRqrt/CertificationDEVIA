from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = _('User Profile')
    verbose_name_plural = _('User Profiles')
    fields = (
        ('vma', 'vo2_max'),
        ('resting_heart_rate', 'max_heart_rate'),
        ('hr_zone_1_min', 'hr_zone_1_max'),
        ('hr_zone_2_min', 'hr_zone_2_max'),
        ('hr_zone_3_min', 'hr_zone_3_max'),
        ('hr_zone_4_min', 'hr_zone_4_max'),
        ('hr_zone_5_min', 'hr_zone_5_max'),
        ('prediction_5k', 'prediction_10k'),
        ('prediction_half_marathon', 'prediction_marathon'),
        ('current_fitness', 'current_fatigue', 'current_form'),
        'last_sync',
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'email', 'birth_date', 'weight', 'height')
        }),
        (_('Sports preferences'), {
            'fields': ('preferred_activity', 'main_goal', 'garmin_email', 'strava_connected')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_premium', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'birth_date', 'weight', 'height')
        }),
        (_('Sports preferences'), {
            'fields': ('preferred_activity', 'main_goal', 'garmin_email')
        }),
    )
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'preferred_activity', 'is_premium', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_premium', 'preferred_activity', 'main_goal')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    
    def get_inline_instances(self, request, obj=None):
        if obj:
            return super().get_inline_instances(request, obj)
        return []


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'vma', 'vo2_max', 'current_fitness', 'last_sync')
    list_filter = ('last_sync', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('User'), {'fields': ('user',)}),
        (_('Performance Metrics'), {
            'fields': ('vma', 'vo2_max', 'resting_heart_rate', 'max_heart_rate')
        }),
        (_('Heart Rate Zones'), {
            'fields': (
                ('hr_zone_1_min', 'hr_zone_1_max'),
                ('hr_zone_2_min', 'hr_zone_2_max'),
                ('hr_zone_3_min', 'hr_zone_3_max'),
                ('hr_zone_4_min', 'hr_zone_4_max'),
                ('hr_zone_5_min', 'hr_zone_5_max'),
            )
        }),
        (_('Performance Predictions'), {
            'fields': (
                ('prediction_5k', 'prediction_10k'),
                ('prediction_half_marathon', 'prediction_marathon'),
            )
        }),
        (_('Training Load'), {
            'fields': ('current_fitness', 'current_fatigue', 'current_form')
        }),
        (_('Sync Information'), {
            'fields': ('last_sync', 'created_at', 'updated_at')
        }),
    )