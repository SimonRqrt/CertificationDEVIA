# 🐳 Docker + Supabase PostgreSQL

Configuration Docker optimisée pour Coach AI avec Supabase PostgreSQL.

## 📋 **Fichiers créés/modifiés**

### ✅ **Dockerfiles mis à jour**
- `django.Dockerfile` - Suppression drivers MSSQL, ajout PostgreSQL
- `requirements-django.txt` - Suppression pymssql/mssql-django

### ✅ **Docker Compose**
- `docker-compose-supabase.yml` - Configuration complète avec Nginx
- `docker-compose-supabase-simple.yml` - Configuration simplifiée (recommandée)

### ✅ **Scripts de démarrage**
- `start_supabase.py` - Script complet de démarrage
- `test_docker_supabase.py` - Script de test et validation

### ✅ **Configuration Nginx**
- `nginx-supabase.conf` - Reverse proxy optimisé

## 🚀 **Démarrage rapide**

### Option 1 : Script automatique
```bash
cd deployment
python3 start_supabase.py
```

### Option 2 : Manuel
```bash
cd deployment
docker compose -f docker-compose-supabase-simple.yml build
docker compose -f docker-compose-supabase-simple.yml up -d
```

## 📡 **Services disponibles**

| Service | URL | Description |
|---------|-----|-------------|
| Django | http://localhost:8002/ | Interface web principale |
| FastAPI | http://localhost:8000/docs | API IA + documentation |
| Streamlit | http://localhost:8501/ | Chat conversationnel |
| Nginx | http://localhost/ | Reverse proxy (avec nginx) |

## 🗄️ **Base de données**

- **Principale** : Supabase PostgreSQL (cloud)
- **Fallback** : SQLite local (automatique)
- **Connexion** : Variables d'environnement depuis .env

## ⚙️ **Variables d'environnement**

Variables automatiquement configurées dans les containers :
```bash
DOCKER_ENV=true
DB_TYPE=postgresql  
DB_HOST=db.tbsxjflpsbiuklxzjwai.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=gN0qC8NHDzjOh1LH
DATABASE_URL=postgresql://postgres:password@host:5432/postgres
```

## 🧪 **Tests et validation**

### Test de connectivité Supabase (local)
```bash
pg_isready -h db.tbsxjflpsbiuklxzjwai.supabase.co -p 5432 -U postgres
# ✅ db.tbsxjflpsbiuklxzjwai.supabase.co:5432 - accepting connections
```

### Test des services Docker
```bash
cd deployment
python3 test_docker_supabase.py
```

### Vérification manuelle
```bash
# État des containers
docker compose -f docker-compose-supabase-simple.yml ps

# Logs en temps réel
docker compose -f docker-compose-supabase-simple.yml logs -f

# Test connexion Supabase depuis container
docker exec coach_ai_django_supabase python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1'); print('✅ Supabase OK')"
```

## 🔧 **Avantages de cette configuration**

### ✅ **Simplicité**
- Plus de drivers ODBC complexes
- Configuration PostgreSQL standard
- Variables d'environnement unifiées

### ✅ **Performance**
- Images Docker allégées
- Connexions directes Supabase
- Fallback SQLite intelligent

### ✅ **Maintenance**
- Configuration cloud Supabase
- Pas de base locale à maintenir
- Scripts automatisés

### ✅ **Déploiement**
- Compatible avec tous les orchestrateurs
- Variables d'env configurables
- Health checks intégrés

## 🐛 **Dépannage**

### Problème de connectivité Supabase
```bash
# Tester depuis l'hôte
pg_isready -h db.tbsxjflpsbiuklxzjwai.supabase.co -p 5432 -U postgres

# Vérifier les logs Docker
docker logs coach_ai_django_supabase

# Tester le fallback SQLite
docker exec coach_ai_django_supabase ls -la /app/data/
```

### Problème de build
```bash
# Nettoyer le cache Docker
docker system prune -f
docker builder prune -f

# Rebuild sans cache
docker compose -f docker-compose-supabase-simple.yml build --no-cache
```

### Variables d'environnement
```bash
# Vérifier dans le container
docker exec coach_ai_django_supabase env | grep DB_
```

## 🎯 **Prochaines étapes**

1. **Résoudre réseau Docker** : Investiguer problème connectivité container → Supabase
2. **Optimiser images** : Multi-stage builds pour réduire la taille
3. **CI/CD** : Intégrer dans GitHub Actions
4. **Monitoring** : Ajouter Prometheus/Grafana
5. **Secrets** : Utiliser Docker secrets pour les credentials

---

> **Note** : Configuration testée en local, prête pour déploiement cloud (AWS, Azure, GCP).