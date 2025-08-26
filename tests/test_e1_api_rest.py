"""
Tests pour E1 - API REST
Tests couvrant les endpoints REST, CRUD operations et sécurité
"""

import pytest
import sys
import os
import requests

# Ajouter les chemins du projet
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(project_root)

class TestAPIRESTEndpoints:
    """Tests des endpoints API REST"""
    
    def test_api_rest_get_activities(self):
        """Test endpoint GET /activities"""
        # TODO: Implémenter test GET activities
        assert True, "Test GET activities à implémenter"
    
    def test_api_rest_post_activity(self):
        """Test endpoint POST /activities"""
        # TODO: Implémenter test POST activity
        assert True, "Test POST activity à implémenter"
        
    def test_api_rest_put_activity(self):
        """Test endpoint PUT /activities/{id}"""
        # TODO: Implémenter test PUT activity
        assert True, "Test PUT activity à implémenter"
        
    def test_api_rest_delete_activity(self):
        """Test endpoint DELETE /activities/{id}"""
        # TODO: Implémenter test DELETE activity
        assert True, "Test DELETE activity à implémenter"

class TestAPIRESTSecurity:
    """Tests de sécurité API REST"""
    
    def test_api_rest_authentification_requise(self):
        """Test que l'authentification est requise"""
        # TODO: Implémenter test auth requise
        assert True, "Test auth requise à implémenter"
        
    def test_api_rest_validation_donnees_entree(self):
        """Test validation des données d'entrée"""
        # TODO: Implémenter test validation input
        assert True, "Test validation input à implémenter"
        
    def test_api_rest_gestion_erreurs(self):
        """Test gestion des erreurs et codes HTTP"""
        # TODO: Implémenter test gestion erreurs
        assert True, "Test gestion erreurs à implémenter"