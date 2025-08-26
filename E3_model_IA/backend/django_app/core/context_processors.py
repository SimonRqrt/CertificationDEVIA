from django.conf import settings
import os

def service_urls(request):
    """
    Context processor pour fournir les URLs des services à tous les templates
    Utilise localhost pour le navigateur même en environnement Docker
    """
    # En Docker, nous voulons que le navigateur utilise localhost, pas les noms de services internes
    if os.getenv('DOCKER_ENV') == 'true':
        # URLs pour le navigateur (depuis l'extérieur des containers)
        return {
            'FASTAPI_URL': 'http://localhost:8000',
            'STREAMLIT_URL': 'http://localhost:8501',
        }
    else:
        # URLs pour développement local
        return {
            'FASTAPI_URL': getattr(settings, 'FASTAPI_URL', 'http://localhost:8000'),
            'STREAMLIT_URL': getattr(settings, 'STREAMLIT_URL', 'http://localhost:8501'),
        }