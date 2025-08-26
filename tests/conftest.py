"""
Configuration pytest pour les tests Coach AI
Fixtures communes et configuration globale
"""

import pytest
import sys
import os

# Configuration des chemins
@pytest.fixture(scope="session", autouse=True)
def setup_paths():
    """Ajouter les chemins du projet au PYTHONPATH"""
    project_root = os.path.join(os.path.dirname(__file__), '..')
    sys.path.insert(0, project_root)
    sys.path.insert(0, os.path.join(project_root, 'E3_model_IA/backend/fastapi_app'))
    sys.path.insert(0, os.path.join(project_root, 'E3_model_IA/backend/django_app'))

# Fixtures communes
@pytest.fixture
def mock_api_key():
    """Clé API mockée pour les tests"""
    return "test_api_key_for_testing"

@pytest.fixture 
def sample_activity_data():
    """Données d'activité sample pour les tests"""
    return {
        "id": 1,
        "name": "Test Run",
        "distance": 5.0,
        "duration": 1800,
        "activity_type": "running"
    }