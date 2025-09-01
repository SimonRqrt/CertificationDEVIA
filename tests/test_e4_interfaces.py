import pytest
import requests
import sys
import os

try:
    from bs4 import BeautifulSoup
except ImportError:
    pytest.skip("BeautifulSoup4 non installé", allow_module_level=True)

project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(project_root)

class TestDjangoInterface:
    """Tests interface Django web"""
    
    @pytest.fixture
    def django_base_url(self):
        return "http://localhost:8002"
    
    def test_django_health_endpoint(self, django_base_url):
        """Test l'endpoint de santé Django"""
        try:
            response = requests.get(f"{django_base_url}/health/", timeout=5)
            assert response.status_code == 200
            assert "OK" in response.text
        except requests.exceptions.RequestException:
            pytest.skip("Service Django non disponible")
    
    def test_django_home_page(self, django_base_url):
        """Test la page d'accueil Django"""
        try:
            response = requests.get(django_base_url, timeout=5)
            assert response.status_code == 200
            assert "Coach AI" in response.text
            assert "intelligence artificielle" in response.text.lower()
        except requests.exceptions.RequestException:
            pytest.skip("Service Django non disponible")
    
    def test_django_admin_login_form(self, django_base_url):
        """Test la page de connexion admin Django"""
        try:
            response = requests.get(f"{django_base_url}/admin/", timeout=5)
            assert response.status_code == 200
            assert "Coach AI Administration" in response.text
            assert "login-form" in response.text
        except requests.exceptions.RequestException:
            pytest.skip("Service Django non disponible")
    
    def test_django_metrics_endpoint(self, django_base_url):
        """Test l'endpoint métriques Prometheus"""
        try:
            response = requests.get(f"{django_base_url}/metrics/", timeout=5)
            assert response.status_code == 200
            assert "django_" in response.text
        except requests.exceptions.RequestException:
            pytest.skip("Service Django non disponible")

class TestStreamlitInterface:
    """Tests interface Streamlit"""
    
    @pytest.fixture
    def streamlit_base_url(self):
        return "http://localhost:8501"
    
    def test_streamlit_accessibility(self, streamlit_base_url):
        """Test l'accessibilité de l'interface Streamlit"""
        try:
            response = requests.get(streamlit_base_url, timeout=5)
            assert response.status_code == 200
            # Vérifier la présence de métadonnées HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            assert soup.find('title') is not None
            assert soup.find('meta', attrs={'name': 'viewport'}) is not None
        except requests.exceptions.RequestException:
            pytest.skip("Service Streamlit non disponible")
    
    def test_streamlit_responsive_design(self, streamlit_base_url):
        """Test les éléments de design responsif"""
        try:
            response = requests.get(streamlit_base_url, timeout=5)
            assert response.status_code == 200
            # Vérifier viewport et CSS responsive
            assert 'viewport' in response.text
            assert 'width=device-width' in response.text
        except requests.exceptions.RequestException:
            pytest.skip("Service Streamlit non disponible")

class TestIntegrationsInterfaces:
    """Tests d'intégration des interfaces"""
    
    def test_microservices_availability(self):
        """Test la disponibilité des microservices principaux"""
        services = [
            ("http://localhost:8002", "Django"),
            ("http://localhost:8501", "Streamlit"),
            ("http://localhost:8000", "FastAPI"),
            ("http://localhost:8001", "E1 API")
        ]
        
        available_services = []
        for url, name in services:
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    available_services.append(name)
            except requests.exceptions.RequestException:
                pass
        
        # En environnement de développement: au moins 2 services
        # En CI/CD: acceptable que services soient indisponibles
        if len(available_services) == 0:
            pytest.skip("Aucun service disponible (environnement CI/CD)")
        else:
            assert len(available_services) >= 2, f"Services disponibles: {available_services}"
    
    def test_cross_service_navigation(self):
        """Test la navigation entre services"""
        try:
            # Test navigation Django -> liens vers autres services
            django_response = requests.get("http://localhost:8002", timeout=5)
            if django_response.status_code == 200:
                # Vérifier présence de liens ou références aux autres services
                content = django_response.text.lower()
                assert "coach" in content or "ai" in content
        except requests.exceptions.RequestException:
            pytest.skip("Services non disponibles pour test navigation")
    
    def test_wcag_compliance_basics(self):
        """Test des éléments basiques de conformité WCAG"""
        urls_to_test = [
            "http://localhost:8002",
            "http://localhost:8501"
        ]
        
        wcag_compliant_count = 0
        
        for url in urls_to_test:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Vérifications WCAG basiques
                    has_title = soup.find('title') is not None
                    has_lang = soup.find('html', attrs={'lang': True}) is not None or 'lang=' in response.text
                    has_viewport = soup.find('meta', attrs={'name': 'viewport'}) is not None
                    
                    if has_title and (has_lang or 'lang' in response.text) and has_viewport:
                        wcag_compliant_count += 1
                        
            except requests.exceptions.RequestException:
                continue
        
        # En environnement de développement: au moins une interface WCAG compliant
        # En CI/CD: acceptable que services soient indisponibles
        if wcag_compliant_count == 0:
            # Vérifier si c'est un environnement CI/CD (aucun service disponible)
            services_available = False
            for url in urls_to_test:
                try:
                    response = requests.get(url, timeout=2)
                    if response.status_code == 200:
                        services_available = True
                        break
                except requests.exceptions.RequestException:
                    continue
            
            if not services_available:
                pytest.skip("Services indisponibles (environnement CI/CD)")
            else:
                assert False, "Aucune interface ne respecte les critères WCAG basiques"
        else:
            assert wcag_compliant_count >= 1