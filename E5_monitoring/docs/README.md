# E5 - Monitoring et Observabilité - Documentation

## Documents disponibles

### Configuration et Architecture
- **[README_MONITORING.md](README_MONITORING.md)** - Guide complet du monitoring Coach AI
  - Architecture Prometheus/Grafana/Alertmanager
  - Métriques surveillées C11/C20
  - Configuration des alertes
  - Scripts de vérification

### Debugging et Incidents  
- **[documentation_debugging_c21.md](documentation_debugging_c21.md)** - Procédures de debugging (C21)
- **[incident_2024_08_20_metrics_openai.md](incident_2024_08_20_metrics_openai.md)** - Rapport d'incident OpenAI

## Critères de certification couverts
- **C11** : Monitoring du modèle IA
- **C20** : Surveillance des seuils et alertes  
- **C21** : Procédures de debugging et gestion d'incidents

## Scripts et outils
- `../scripts/webhook_receiver.py` - Récepteur d'alertes
- `../scripts/health_check_monitoring.sh` - Vérification santé monitoring

## Dashboards et configurations
- `../grafana/` - Dashboards Grafana
- `../prometheus/` - Configuration et règles d'alerte
- `../alertmanager/` - Configuration notifications