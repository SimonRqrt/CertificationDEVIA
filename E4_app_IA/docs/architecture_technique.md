# Architecture Technique - Coach IA

## Schéma d'Architecture Technique

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Browser]
        MOB[Mobile App]
    end

    subgraph "Load Balancer"
        LB[Nginx Load Balancer]
    end

    subgraph "Application Layer"
        subgraph "Frontend Services"
            DJANGO[Django Web App<br/>Port 8000]
            STREAMLIT[Streamlit App<br/>Port 8501]
        end
        
        subgraph "Backend Services"
            FASTAPI[FastAPI Service<br/>Port 8080]
            AUTH[Auth Service<br/>Port 8081]
        end
        
        subgraph "AI Services"
            LLM[LLM Service<br/>OpenAI/Anthropic]
            AGENT[Agent Service<br/>LangChain]
            RAG[RAG Service<br/>Vector DB]
        end
    end

    subgraph "Data Layer"
        subgraph "Databases"
            POSTGRES[(PostgreSQL<br/>Primary DB)]
            REDIS[(Redis<br/>Cache/Sessions)]
            VECTOR[(Vector DB<br/>Embeddings)]
        end
        
        subgraph "External APIs"
            GARMIN[Garmin Connect API]
            STRAVA[Strava API]
        end
    end

    subgraph "Infrastructure Layer"
        subgraph "Monitoring"
            PROM[Prometheus<br/>Metrics]
            GRAF[Grafana<br/>Dashboards]
            LOKI[Loki<br/>Logs]
        end
        
        subgraph "Security"
            OAUTH[OAuth 2.0]
            JWT[JWT Tokens]
            VAULT[Secrets Vault]
        end
    end

    subgraph "DevOps Layer"
        subgraph "CI/CD"
            GIT[GitLab]
            CICD[GitLab CI/CD]
            REG[Container Registry]
        end
        
        subgraph "Deployment"
            DOCKER[Docker Containers]
            COMPOSE[Docker Compose]
            K8S[Kubernetes]
        end
    end

    %% Client connections
    WEB --> LB
    MOB --> LB
    
    %% Load balancer routing
    LB --> DJANGO
    LB --> STREAMLIT
    LB --> FASTAPI
    
    %% Internal service communication
    DJANGO --> FASTAPI
    STREAMLIT --> FASTAPI
    FASTAPI --> AUTH
    FASTAPI --> LLM
    FASTAPI --> AGENT
    AGENT --> RAG
    
    %% Database connections
    DJANGO --> POSTGRES
    FASTAPI --> POSTGRES
    AUTH --> REDIS
    RAG --> VECTOR
    
    %% External API connections
    FASTAPI --> GARMIN
    FASTAPI --> STRAVA
    
    %% Monitoring connections
    DJANGO -.-> PROM
    FASTAPI -.-> PROM
    LLM -.-> PROM
    PROM --> GRAF
    DJANGO -.-> LOKI
    FASTAPI -.-> LOKI
    
    %% Security
    AUTH --> OAUTH
    AUTH --> JWT
    FASTAPI --> VAULT
    
    %% DevOps flow
    GIT --> CICD
    CICD --> REG
    REG --> DOCKER
    DOCKER --> COMPOSE

    style DJANGO fill:#2E8B57
    style STREAMLIT fill:#FF6347
    style FASTAPI fill:#4169E1
    style POSTGRES fill:#336791
    style LLM fill:#FFD700
    style PROM fill:#E6522C
    style GRAF fill:#F46800
```

## Technologies et Versions

### Frontend
- **Django 4.2+**: Interface web principale, génération guidée de plans
- **Streamlit 1.28+**: Interface conversationnelle avec l'IA
- **HTML5/CSS3/JavaScript**: Technologies web standards

### Backend
- **FastAPI 0.104+**: API REST principale, haute performance
- **Python 3.11+**: Langage principal du backend
- **Pydantic**: Validation et sérialisation des données
- **SQLAlchemy**: ORM pour la base de données

### Intelligence Artificielle
- **OpenAI GPT-4**: Modèle de langage principal
- **LangChain**: Framework pour les agents IA et RAG
- **ChromaDB**: Base de données vectorielle pour les embeddings
- **Sentence Transformers**: Génération d'embeddings

### Base de Données
- **PostgreSQL 15+**: Base de données principale
- **Redis 7+**: Cache et gestion des sessions
- **pgvector**: Extension PostgreSQL pour les vecteurs

### Infrastructure
- **Docker & Docker Compose**: Conteneurisation
- **Nginx**: Reverse proxy et load balancer
- **Prometheus**: Collecte de métriques
- **Grafana**: Visualisation et dashboards
- **Loki**: Agrégation de logs

### Sécurité
- **OAuth 2.0**: Authentification avec Garmin/Strava
- **JWT**: Tokens d'authentification
- **HTTPS/TLS**: Chiffrement des communications
- **HashiCorp Vault**: Gestion des secrets

### DevOps
- **GitLab CI/CD**: Pipeline d'intégration continue
- **Docker Registry**: Stockage des images
- **Kubernetes**: Orchestration (production)

## Contraintes Techniques

### Performance
- Temps de réponse API < 500ms (95e percentile)
- Temps de génération IA < 10s
- Support de 100 utilisateurs simultanés

### Sécurité
- Conformité RGPD
- Chiffrement des données sensibles
- Audit trail complet
- Rate limiting sur les APIs

### Disponibilité
- SLA 99.5% de disponibilité
- Sauvegarde quotidienne automatique
- Plan de reprise d'activité < 4h

### Scalabilité
- Architecture microservices
- Scaling horizontal des services
- Cache distribué avec Redis
- CDN pour les assets statiques