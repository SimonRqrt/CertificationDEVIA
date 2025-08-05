import pytest
import sys
import os

# Ajouter les chemins au PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def test_project_structure():
    """Test que la structure du projet est correcte"""
    assert os.path.exists('E1_gestion_donnees')
    assert os.path.exists('E3_model_IA')
    assert os.path.exists('E4_app_IA')
    assert os.path.exists('deployment')

def test_requirements_exist():
    """Test que les fichiers requirements existent"""
    assert os.path.exists('requirements.txt')
    assert os.path.exists('E1_gestion_donnees/api_rest/requirements-django.txt')
    assert os.path.exists('E3_model_IA/backend/fastapi_app/requirements-fastapi.txt')
    assert os.path.exists('E4_app_IA/frontend/streamlit_app/requirements-streamlit.txt')

def test_docker_files_exist():
    """Test que les Dockerfiles existent"""
    assert os.path.exists('deployment/django.Dockerfile')
    assert os.path.exists('deployment/fastapi.Dockerfile')
    assert os.path.exists('deployment/streamlit.Dockerfile')
    assert os.path.exists('deployment/docker-compose-supabase.yml')

def test_python_version():
    """Test que Python 3.11+ est utilisé"""
    version = sys.version_info
    assert version.major == 3
    assert version.minor >= 11

if __name__ == "__main__":
    pytest.main([__file__]) 