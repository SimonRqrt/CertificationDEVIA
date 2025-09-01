# Tests et Couverture - Documentation

## Documents disponibles  

### Rapports de Tests
- **[README.md](README.md)** - Guide d'exécution des tests
- **[coverage_report.md](coverage_report.md)** - Rapport de couverture de code

### Résultats et Métriques
- `../rapport_tests_api_ia.json` - Rapport détaillé tests API IA
- `../coverage_reports/coverage.xml` - Rapport de couverture XML
- `../coverage_reports/htmlcov/index.html` - Rapport interactif HTML

## Tests disponibles par module

### E1 - Gestion Données
- `test_e1_api_rest.py` - Tests API REST
- `test_e1_pipeline.py` - Tests pipeline ETL

### E3 - Modèle IA  
- `test_e3_agent_ia.py` - Tests agent IA
- `test_e3_api_ia.py` - Tests API IA (partiels)

### E4 - Interface Applications
- `test_e4_interfaces.py` - Tests Django/Streamlit

### E5 - Monitoring
- `test_e5_monitoring.py` - Tests monitoring

### Tests d'Intégration
- `test_integration.py` - Tests bout-en-bout

## Couverture actuelle
- **Tests fonctionnels** : 30/44 passent
- **Modules couverts** : E1, E3 (partiel), E4, E5  
- **Intégration** : Architecture Docker validée

## Exécution
```bash
# Tous les tests stables
pytest tests/test_e1_api_rest.py tests/test_e1_pipeline.py tests/test_e4_interfaces.py tests/test_e5_monitoring.py -v

# Avec couverture
pytest --cov=. --cov-report=html --cov-report=term-missing
```