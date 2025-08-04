# 🏗️ Architecture Hybride Intelligente Django + SQLAlchemy

## 🎯 Principe : Complémentarité au lieu de Redondance

### **Django** = Interface Utilisateur + CRUD Simple
- ✅ Authentification utilisateurs
- ✅ Interface web moderne  
- ✅ CRUD activités basique
- ✅ Gestion des plans d'entraînement
- ✅ Sessions de coaching IA

### **SQLAlchemy E1** = Analytics Engine + Performance
- 🔥 **Requêtes complexes** (agrégations multi-tables)
- 🔥 **Calculs de métriques** (VMA, VO2max, prédictions)
- 🔥 **Analytics avancées** (tendances, corrélations)
- 🔥 **Data Science** (pandas integration)
- 🔥 **Performance queries** (optimisations SQL)

## 💡 Cas d'usage concrets

### 1. **Dashboard Analytics Avancé**
```python
# Django affiche l'interface
# SQLAlchemy calcule les métriques complexes

def get_user_analytics_dashboard(user_id):
    # Requêtes impossibles avec Django ORM
    sql_query = """
    SELECT 
        DATE_TRUNC('week', start_time) as week,
        AVG(average_speed * 3.6) as avg_speed_kmh,
        SUM(training_load) as weekly_load,
        MAX(average_hr) as max_hr_week,
        COUNT(*) as activities_count,
        -- Calcul VMA par périodes
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY max_speed * 3.6) as vma_estimate
    FROM activities 
    WHERE user_id = :user_id 
      AND start_time >= NOW() - INTERVAL '12 weeks'
    GROUP BY DATE_TRUNC('week', start_time)
    ORDER BY week DESC
    """
    return engine.execute(sql_query, user_id=user_id).fetchall()
```

### 2. **Prédictions de Performance**
```python
# Machine Learning avec SQLAlchemy + pandas
def predict_race_performance(user_id: int, race_distance_km: float):
    # Récupérer données via SQLAlchemy
    activities_df = pd.read_sql(
        "SELECT * FROM activities WHERE user_id = %s AND activity_type = 'running'",
        engine, params=[user_id]
    )
    
    # Appliquer algorithmes ML
    vma = compute_vma_from_df(activities_df)
    predicted_time = race_prediction_riegel(vma, race_distance_km)
    
    return {
        'predicted_time_minutes': predicted_time,
        'confidence_score': calculate_confidence(activities_df),
        'training_recommendations': generate_training_plan(vma, race_distance_km)
    }
```

### 3. **API Analytics Dédiée**
```python
# FastAPI endpoints utilisant SQLAlchemy
@app.get("/v1/analytics/trends/{user_id}")
async def get_performance_trends(user_id: int, period_weeks: int = 12):
    \"\"\"Analytics impossibles avec Django ORM\"\"\"
    
    # Requête complexe avec window functions
    query = text(\"\"\"
    SELECT 
        start_time,
        distance_meters/1000 as distance_km,
        duration_seconds/60 as duration_min,
        average_speed * 3.6 as pace_kmh,
        -- Moyennes mobiles
        AVG(average_speed * 3.6) OVER (
            ORDER BY start_time 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) as pace_trend_7d,
        -- Écart type glissant pour détecter la régularité
        STDDEV(training_load) OVER (
            ORDER BY start_time 
            ROWS BETWEEN 13 PRECEDING AND CURRENT ROW
        ) as load_stability
    FROM activities 
    WHERE user_id = :user_id 
      AND start_time >= NOW() - INTERVAL ':weeks weeks'
    ORDER BY start_time DESC
    \"\"\")
    
    results = engine.execute(query, user_id=user_id, weeks=period_weeks)
    return {'trends': [dict(row) for row in results]}

@app.get("/v1/analytics/zones/{user_id}")  
async def get_training_zones_analysis(user_id: int):
    \"\"\"Analyse des zones d'entraînement\"\"\"
    
    # Calcul sophistiqué impossible avec Django ORM
    query = text(\"\"\"
    SELECT 
        CASE 
            WHEN average_hr <= (SELECT MAX(average_hr) * 0.6 FROM activities WHERE user_id = :user_id) THEN 'Zone 1 - Recovery'
            WHEN average_hr <= (SELECT MAX(average_hr) * 0.7 FROM activities WHERE user_id = :user_id) THEN 'Zone 2 - Aerobic'
            WHEN average_hr <= (SELECT MAX(average_hr) * 0.8 FROM activities WHERE user_id = :user_id) THEN 'Zone 3 - Tempo'
            WHEN average_hr <= (SELECT MAX(average_hr) * 0.9 FROM activities WHERE user_id = :user_id) THEN 'Zone 4 - Threshold'
            ELSE 'Zone 5 - VO2max'
        END as hr_zone,
        COUNT(*) as activities_count,
        AVG(duration_seconds)/60 as avg_duration_min,
        SUM(duration_seconds)/3600 as total_hours,
        AVG(training_load) as avg_training_load
    FROM activities 
    WHERE user_id = :user_id 
      AND average_hr IS NOT NULL
    GROUP BY 1
    ORDER BY hr_zone
    \"\"\")
    
    results = engine.execute(query, user_id=user_id)
    return {'zones_analysis': [dict(row) for row in results]}
```

### 4. **Synchronisation Intelligente**
```python
# Sync périodique Django → SQLAlchemy pour analytics
def sync_django_to_analytics():
    \"\"\"Copie les nouvelles activités Django vers tables analytics E1\"\"\"
    
    # Récupérer nouvelles activités Django
    django_activities = Activity.objects.filter(
        synced_to_analytics=False
    ).values()
    
    # Convertir et enrichir pour analytics
    analytics_data = []
    for activity in django_activities:
        enriched = enrich_activity_for_analytics(activity)
        analytics_data.append(enriched)
    
    # Insérer en batch dans SQLAlchemy
    if analytics_data:
        engine.execute(analytics_table.insert(), analytics_data)
        
        # Marquer comme synchronisées
        Activity.objects.filter(
            id__in=[a['id'] for a in django_activities]
        ).update(synced_to_analytics=True)
```

## 🔄 Architecture Finale Optimisée

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   DJANGO        │    │   SQLAlchemy E1  │    │   FastAPI       │
│   Interface     │◄──►│   Analytics      │◄──►│   API           │
│   - Auth users  │    │   - Métriques    │    │   - Coaching IA │
│   - CRUD simple │    │   - Requêtes     │    │   - Analytics   │
│   - Templates   │    │   - ML/pandas    │    │   - Endpoints   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Supabase      │    │   SQLite E1      │    │   Knowledge     │
│   PostgreSQL    │    │   Analytics      │    │   Base          │
│   - Users       │    │   - Metrics      │    │   - RAG docs    │
│   - Activities  │    │   - Aggregated   │    │   - Training    │
│   - Plans       │    │   - ML features  │    │   - FAISS       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## ⚡ Avantages de cette approche

1. **✅ Conformité E1** : SQLAlchemy respecte tous les critères de la grille
2. **✅ Valeur ajoutée** : Analytics impossibles avec Django ORM seul  
3. **✅ Performance** : Requêtes optimisées pour le big data
4. **✅ Évolutivité** : Séparation claire des responsabilités
5. **✅ ML Ready** : Integration pandas/scikit-learn native
6. **✅ Maintenance** : Chaque système dans son domaine d'expertise

## 🎯 Implémentation progressive

1. **Phase 1** : Sync Django → SQLAlchemy (données identiques)
2. **Phase 2** : Endpoints analytics via FastAPI + SQLAlchemy  
3. **Phase 3** : Dashboard avancé dans Django utilisant APIs analytics
4. **Phase 4** : ML/AI features exploitant la richesse SQLAlchemy

**Résultat : Architecture professionnelle où chaque technologie apporte sa valeur unique !**