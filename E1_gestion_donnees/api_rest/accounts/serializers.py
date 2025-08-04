from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription d'un nouvel utilisateur"""
    
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'birth_date', 'weight', 'height',
            'preferred_activity', 'main_goal', 'garmin_email'
        )
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password": _("Password fields didn't match.")}
            )
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        
        # Créer le profil utilisateur automatiquement
        UserProfile.objects.create(user=user)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer pour la connexion utilisateur"""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    _('Unable to log in with provided credentials.'),
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    _('User account is disabled.'),
                    code='authorization'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                _('Must include "email" and "password".'),
                code='authorization'
            )


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil utilisateur"""
    
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les informations utilisateur"""
    
    profile = UserProfileSerializer(read_only=True)
    bmi = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'birth_date', 'weight', 'height', 'preferred_activity',
            'main_goal', 'garmin_email', 'strava_connected',
            'is_premium', 'created_at', 'updated_at', 'bmi', 'profile'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'bmi')
    
    def update(self, instance, validated_data):
        """Mise à jour avec gestion du profil"""
        profile_data = validated_data.pop('profile', {})
        
        # Mise à jour de l'utilisateur
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Mise à jour du profil si des données sont fournies
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer pour le changement de mot de passe"""
    
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(_('Current password is incorrect.'))
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password": _("New password fields didn't match.")}
            )
        return attrs
    
    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetSerializer(serializers.Serializer):
    """Serializer pour la réinitialisation de mot de passe"""
    
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(_('User with this email does not exist.'))
        return value