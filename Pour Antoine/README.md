# Scripts Django Production Exportés pour Antoine

Ce dossier contient tous les scripts exportés depuis le conteneur Django de production (port 8002).

## Structure du Dossier

### 📁 Templates HTML
```
templates/
├── core/
│   ├── base.html                 # Template de base avec layout principal
│   └── home.html                 # Page d'accueil Coach AI
├── coaching/
│   ├── simple_plan_result.html   # Résultats des plans de coaching
│   └── running_goal_wizard.html  # Assistant objectifs running
└── activities/
    └── pipeline_dashboard.html   # Dashboard pipeline données Garmin
```

### 📁 Fichiers Statiques (CSS/JS)
```
static/
├── css/
│   ├── style.css                # Styles principaux Coach AI
│   └── flaticon.css             # Icônes Flaticon
└── js/
    └── main.js                  # JavaScript principal
```

### 📁 Configuration Django
```
config/
├── urls.py                      # Routage principal URLs Django
└── settings.py                  # Configuration Django avec statiques
```

### 📁 Vues Django
```
views/
├── core_views.py                # Vues principales (home, stats)
└── coaching_views.py            # Vues coaching et IA
```

## Utilisation

Ces fichiers peuvent être utilisés pour :
- Comprendre l'architecture frontend Django
- Copier les templates vers d'autres environnements
- Analyser les styles CSS personnalisés
- Étudier les vues et le routage Django

## Source

Tous ces fichiers ont été exportés depuis le conteneur Django production :
- **Container**: `coach_ia_django`
- **Port**: 8002
- **Date d'export**: $(date)
- **Version Django**: 4.2.7

## Notes

- Le fichier `templates/core/quick_stats.html` n'existait pas dans le conteneur source
- Tous les autres fichiers ont été exportés avec succès
- Les chemins sont préservés par rapport à la structure Django originale