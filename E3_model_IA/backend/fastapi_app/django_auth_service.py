import os
import sys
import django
from pathlib import Path
import requests
from typing import Optional, Dict, Any
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
import logging

# Configuration Django - mise à jour après réorganisation
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent.parent
DJANGO_APP_DIR = PROJECT_ROOT / 'E1_gestion_donnees' / 'api_rest'

# Ajouter les chemins Django au PYTHONPATH
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(DJANGO_APP_DIR))

# Configuration Django pour utilisation standalone
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coach_ai_web.settings')

# Changer le répertoire de travail vers Django app
original_cwd = os.getcwd()
os.chdir(DJANGO_APP_DIR)
django.setup()
os.chdir(original_cwd)

# Imports Django après setup
from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.backends import BaseBackend

User = get_user_model()
logger = logging.getLogger(__name__)


class UserInfo(BaseModel):
    """Modèle Pydantic pour les informations utilisateur"""
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    is_premium: bool
    preferred_activity: str
    main_goal: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class DjangoAuthService:
    """Service d'authentification Django pour FastAPI"""
    
    def __init__(self):
        self.jwt_auth = JWTAuthentication()
        self.django_url = os.getenv('DJANGO_URL', 'http://localhost:8002')
        
    def authenticate_token(self, token: str) -> Optional[UserInfo]:
        """Authentifier un token JWT Django depuis FastAPI"""
        try:
            # Valider le token JWT
            validated_token = self.jwt_auth.get_validated_token(token)
            user = self.jwt_auth.get_user(validated_token)
            
            if not user or not user.is_active:
                return None
            
            # Convertir en modèle Pydantic
            user_info = UserInfo(
                id=user.id,
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                is_active=user.is_active,
                is_premium=user.is_premium,
                preferred_activity=user.preferred_activity,
                main_goal=user.main_goal,
                created_at=user.created_at
            )
            
            return user_info
            
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Token invalide : {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur d'authentification : {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[UserInfo]:
        """Récupérer un utilisateur par son ID"""
        try:
            user = User.objects.get(id=user_id, is_active=True)
            return UserInfo.from_orm(user)
        except User.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'utilisateur {user_id}: {e}")
            return None
    
    def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Récupérer le profil complet d'un utilisateur"""
        try:
            user = User.objects.get(id=user_id, is_active=True)
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            return {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'birth_date': user.birth_date,
                    'weight': user.weight,
                    'height': user.height,
                    'preferred_activity': user.preferred_activity,
                    'main_goal': user.main_goal,
                    'is_premium': user.is_premium,
                    'bmi': user.bmi,
                },
                'profile': {
                    'vma': profile.vma,
                    'vo2_max': profile.vo2_max,
                    'resting_heart_rate': profile.resting_heart_rate,
                    'max_heart_rate': profile.max_heart_rate,
                    'current_fitness': profile.current_fitness,
                    'current_fatigue': profile.current_fatigue,
                    'current_form': profile.current_form,
                    'prediction_5k': profile.prediction_5k,
                    'prediction_10k': profile.prediction_10k,
                    'prediction_half_marathon': profile.prediction_half_marathon,
                    'prediction_marathon': profile.prediction_marathon,
                    'last_sync': profile.last_sync,
                }
            }
        except User.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du profil {user_id}: {e}")
            return None
    
    def authenticate_with_django_api(self, token: str) -> Optional[Dict[str, Any]]:
        """Authentifier via l'API Django (fallback)"""
        try:
            headers = {'Authorization': f'Bearer {token}'}
            response = requests.get(
                f'{self.django_url}/api/v1/auth/profile/',
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Échec de l'authentification API Django: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de communication avec Django API: {e}")
            return None
    
    def create_coaching_session(self, user_id: int, session_data: Dict[str, Any]) -> Optional[int]:
        """Créer une session de coaching dans Django"""
        try:
            from coaching.models import CoachingSession
            
            session = CoachingSession.objects.create(
                user_id=user_id,
                session_id=session_data.get('session_id'),
                title=session_data.get('title', ''),
                user_message=session_data.get('user_message', ''),
                ai_response=session_data.get('ai_response', ''),
                context_data=session_data.get('context_data', {}),
                response_time=session_data.get('response_time')
            )
            
            return session.id
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la session: {e}")
            return None
    
    def get_user_activities_count(self, user_id: int) -> int:
        """Récupérer le nombre d'activités d'un utilisateur"""
        try:
            from activities.models import Activity
            return Activity.objects.filter(user_id=user_id).count()
        except Exception as e:
            logger.error(f"Erreur lors du comptage des activités: {e}")
            return 0
    
    def get_user_goals_count(self, user_id: int) -> int:
        """Récupérer le nombre d'objectifs actifs d'un utilisateur"""
        try:
            from coaching.models import Goal
            return Goal.objects.filter(user_id=user_id, is_active=True).count()
        except Exception as e:
            logger.error(f"Erreur lors du comptage des objectifs: {e}")
            return 0
    
    def get_user_context_for_coaching(self, user_id: int) -> Dict[str, Any]:
        """Récupérer le contexte utilisateur pour le coaching IA"""
        try:
            profile_data = self.get_user_profile(user_id)
            if not profile_data:
                return {}
            
            activities_count = self.get_user_activities_count(user_id)
            goals_count = self.get_user_goals_count(user_id)
            
            return {
                'user_profile': profile_data,
                'stats': {
                    'activities_count': activities_count,
                    'active_goals': goals_count,
                },
                'preferences': {
                    'preferred_activity': profile_data['user']['preferred_activity'],
                    'main_goal': profile_data['user']['main_goal'],
                    'is_premium': profile_data['user']['is_premium'],
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du contexte: {e}")
            return {}


# Instance globale du service
django_auth_service = DjangoAuthService()


def get_current_user_from_token(token: str) -> Optional[UserInfo]:
    """Fonction utilitaire pour récupérer l'utilisateur actuel depuis un token"""
    return django_auth_service.authenticate_token(token)


def get_user_coaching_context(user_id: int) -> Dict[str, Any]:
    """Fonction utilitaire pour récupérer le contexte coaching d'un utilisateur"""
    return django_auth_service.get_user_context_for_coaching(user_id)