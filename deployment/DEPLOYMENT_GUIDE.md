# 🚀 Guide de Déploiement Multi-Environnement

## 📋 Vue d'ensemble

Ce guide explique comment déployer CertificationDEVIA sur différents environnements avec Supabase PostgreSQL.

## 🏗️ Architectures par environnement

### 🖥️ **Développement Local (macOS)**
```
┌─────────────────┐    ┌─────────────────┐
│   Host macOS    │    │ Docker Desktop  │
│                 │    │                 │
│ Django Local    │    │ Django Container│
│       ↓         │    │       ↓         │
│ Supabase        │    │ SQLite Fallback │
│ PostgreSQL ✅   │    │ (IPv6 limit) ⚡ │
└─────────────────┘    └─────────────────┘
```

### ☁️ **Production Cloud (Railway/Fly.io/Render)**
```
┌─────────────────────────────────────────┐
│           Hébergeur Cloud               │
│  ┌─────────────┐    ┌─────────────────┐ │
│  │   Docker    │    │    Supabase     │ │
│  │ Containers  │◄──►│   PostgreSQL    │ │
│  │ (IPv6 ✅)   │    │   (Cloud DB)    │ │
│  └─────────────┘    └─────────────────┘ │
└─────────────────────────────────────────┘
```

## 🔧 Configurations disponibles

### 1. **Développement Local**
```bash
# Configuration actuelle (hybride)
docker compose -f docker-compose-supabase.yml up -d
```
- Host → Supabase PostgreSQL
- Docker → SQLite fallback
- Synchronisation automatique

### 2. **Production Locale (test)**
```bash
# Configuration production stricte
python3 deploy_production.py
```
- Force PostgreSQL uniquement
- Aucun fallback SQLite
- Test avant déploiement

### 3. **Production Cloud**
Variables d'environnement requises :
```bash
PRODUCTION_MODE=true
DISABLE_SQLITE_FALLBACK=true
DB_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@host:port/db
```

## 🌐 Hébergeurs recommandés

### ✅ **Railway** (Recommandé)
- **Support IPv6** : Natif
- **PostgreSQL** : Intégré ou Supabase externe
- **Docker** : Support complet
- **Prix** : $5/mois
- **Déploiement** : 1-click depuis GitHub

**Configuration Railway :**
```yaml
services:
  web:
    build:
      dockerfile: deployment/django.Dockerfile
    environment:
      PRODUCTION_MODE: true
      PORT: 8002
    variables:
      DATABASE_URL: ${{ Supabase.DATABASE_URL }}
```

### ✅ **Fly.io**
- **Support IPv6** : Excellent
- **Global network** : Edge locations
- **Docker** : Natif
- **Prix** : $0-10/mois
- **Avantage** : Performance mondiale

### ✅ **Render**
- **Support IPv6** : Natif
- **PostgreSQL** : Managé
- **Docker** : Support complet
- **Prix** : $7/mois
- **Avantage** : Simple d'utilisation

### ⚠️ **Heroku**
- **Support IPv6** : Limité
- **PostgreSQL** : Excellent
- **Prix** : $7-25/mois
- **Note** : Vérifier compatibilité Supabase

## 📦 Scripts de déploiement

### Local → Production Test
```bash
cd deployment
python3 deploy_production.py
```

### GitHub Actions (CI/CD)
```yaml
name: Deploy Production
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        run: |
          railway login --token ${{ secrets.RAILWAY_TOKEN }}
          railway up
```

## 🔍 Troubleshooting déploiement

### ❌ **"Network unreachable" en production**
**Cause** : IPv6 non supporté par l'hébergeur
**Solution** :
1. Vérifier support IPv6 hébergeur
2. Utiliser hébergeur avec IPv6 natif
3. Configuration réseau Docker personnalisée

### ❌ **"PostgreSQL connection failed"**
**Cause** : Variables d'environnement incorrectes
**Solution** :
```bash
# Vérifier variables
echo $DATABASE_URL
echo $DB_TYPE

# Test manuel
python3 -c "import psycopg2; psycopg2.connect('$DATABASE_URL')"
```

### ❌ **"Migration failed"**
**Cause** : Base de données non initialisée
**Solution** :
```bash
# En production
python3 manage.py migrate
python3 manage.py collectstatic --noinput
python3 manage.py createsuperuser --noinput
```

## 📊 Validation déploiement

### ✅ **Checklist pré-déploiement**
- [ ] Variables .env configurées
- [ ] Connexion Supabase testée
- [ ] Images Docker buildées
- [ ] Certificats SSL (si HTTPS)
- [ ] Monitoring configuré

### ✅ **Tests post-déploiement**
```bash
# Health checks
curl -f https://yourapp.com/health
curl -f https://yourapp.com/api/v1/health

# Test base de données
curl -f https://yourapp.com/api/v1/activities/

# Test IA
curl -X POST https://yourapp.com/api/v1/coaching/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Coach!"}'
```

## 🎯 **Recommandation finale**

### **Pour certification/démo :**
✅ **Railway** + **Supabase PostgreSQL**
- Déploiement simple en 5 minutes
- IPv6 natif (résout le problème Docker)
- Gratuit pour commencer
- GitHub integration automatique

### **Commandes de déploiement :**
```bash
# 1. Installer Railway CLI
npm install -g @railway/cli

# 2. Login
railway login

# 3. Créer projet
railway init

# 4. Déployer
railway up
```

### **Variables à configurer sur Railway :**
```
DATABASE_URL=postgresql://postgres:pass@host:6543/postgres
OPENAI_API_KEY=sk-...
SECRET_KEY=your-secret-key
PRODUCTION_MODE=true
DISABLE_SQLITE_FALLBACK=true
```

## 🔗 URLs après déploiement
- **Interface principale** : `https://yourapp.railway.app/`
- **Générateur Plans IA** : `https://yourapp.railway.app/api/v1/coaching/simple-plan/`
- **Chat Streamlit** : `https://yourapp.railway.app/chat/`
- **Admin Django** : `https://yourapp.railway.app/admin/`

---

> **Note** : Ce guide garantit que Docker + Supabase fonctionnent parfaitement en production cloud, résolvant le problème IPv6 de Docker Desktop local.