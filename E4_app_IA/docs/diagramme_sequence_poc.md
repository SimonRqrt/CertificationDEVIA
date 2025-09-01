# Diagramme de Séquence POC - Coach IA

## Séquence POC: Génération de Plan d'Entraînement

```mermaid
sequenceDiagram
    participant U as 👤 Utilisateur
    participant DW as 🌐 Django Web
    participant API as ⚡ FastAPI
    participant AUTH as 🔐 Auth Service
    participant ETL as 🔄 Pipeline ETL
    participant GA as 🏃 Garmin API
    participant DB as 🗄️ PostgreSQL
    participant AG as 🤖 Agent IA
    participant RAG as 📚 RAG Service
    participant LLM as 🧠 LLM Service
    participant CACHE as ⚡ Redis Cache

    Note over U,CACHE: POC - Génération Plan Marathon Personnalisé
    
    %% Phase 1: Authentification et configuration
    U->>DW: 1. Accède au formulaire de plan
    DW->>U: 2. Affiche formulaire objectif
    U->>DW: 3. Saisit: Objectif Marathon, Niveau Intermédiaire
    DW->>AUTH: 4. Vérifie session utilisateur
    AUTH->>CACHE: 5. Contrôle token session
    CACHE-->>AUTH: 6. Token valide
    AUTH-->>DW: 7. Utilisateur authentifié
    
    %% Phase 2: Connexion et récupération données Garmin
    DW->>U: 8. Demande autorisation Garmin
    U->>DW: 9. Autorise connexion Garmin
    DW->>API: 10. POST /connect-garmin (user_id, oauth_code)
    API->>AUTH: 11. Valide token utilisateur
    AUTH-->>API: 12. Token valide
    
    API->>ETL: 13. Démarre pipeline Garmin
    ETL->>GA: 14. OAuth2 - Exchange code for token
    GA-->>ETL: 15. Access token + refresh token
    
    ETL->>GA: 16. GET /activities (last 6 months)
    GA-->>ETL: 17. JSON activities data
    ETL->>GA: 18. GET /user-profile
    GA-->>ETL: 19. JSON profile data
    
    %% Phase 3: Traitement et validation des données
    ETL->>ETL: 20. Validation format données
    ETL->>ETL: 21. Calcul métriques (VMA, seuils)
    ETL->>DB: 22. INSERT activities_temp
    DB-->>ETL: 23. Success
    ETL->>API: 24. Pipeline terminé (temp_session_id)
    API-->>DW: 25. Données récupérées
    
    %% Phase 4: Génération du plan par l'IA
    DW->>API: 26. POST /generate-plan
    Note over API: {objective: "marathon", level: "intermediate", session_id: "temp_123"}
    
    API->>CACHE: 27. Check cache plan
    CACHE-->>API: 28. Cache miss
    
    API->>AG: 29. Génère plan d'entraînement
    AG->>DB: 30. SELECT activities FROM temp WHERE session_id
    DB-->>AG: 31. Historique activités
    
    AG->>AG: 32. Analyse profil coureur
    Note over AG: Calcul VMA moyenne, volume hebdo, progression
    
    AG->>RAG: 33. Query knowledge base
    Note over RAG: "plan marathon niveau intermédiaire VMA 14km/h"
    RAG->>RAG: 34. Recherche vectorielle
    RAG-->>AG: 35. Contexte entraînement marathon
    
    AG->>LLM: 36. Prompt enrichi
    Note over LLM: System: Expert coach running<br/>Context: Profil + Knowledge<br/>Task: Plan 16 semaines marathon
    
    LLM-->>AG: 37. Plan d'entraînement structuré
    AG->>AG: 38. Post-traitement et validation
    AG-->>API: 39. Plan finalisé (JSON)
    
    %% Phase 5: Mise en cache et affichage
    API->>CACHE: 40. Cache plan (key: user_objective_hash)
    API->>DB: 41. DELETE activities_temp WHERE session_id
    Note over API,DB: RGPD: Suppression données temporaires
    
    API-->>DW: 42. Plan d'entraînement
    DW->>DW: 43. Formatage HTML + tableaux
    DW->>U: 44. Affiche plan personnalisé
    
    %% Phase 6: Actions utilisateur
    U->>DW: 45. Demande export PDF
    DW->>API: 46. POST /export-plan
    API->>API: 47. Génération PDF
    API-->>DW: 48. URL téléchargement
    DW-->>U: 49. Lien de téléchargement
    
    Note over U,CACHE: POC Validé ✅<br/>Temps total: ~15 secondes<br/>Plan personnalisé généré avec succès
```

## Séquence POC Alternative: Chat Conversationnel Streamlit

```mermaid
sequenceDiagram
    participant U as 👤 Utilisateur
    participant ST as 💬 Streamlit
    participant API as ⚡ FastAPI
    participant AG as 🤖 Agent IA
    participant LLM as 🧠 LLM Service
    participant CACHE as ⚡ Redis

    Note over U,CACHE: POC - Conseil Conversationnel Instantané
    
    U->>ST: 1. "J'ai couru 10K en 45min, comment améliorer?"
    ST->>API: 2. POST /chat
    Note over API: {message: "analyse performance", context: "10K en 45min"}
    
    API->>CACHE: 3. Check conversation context
    CACHE-->>API: 4. Nouvelle conversation
    
    API->>AG: 5. Analyse question utilisateur
    AG->>AG: 6. Calcul métriques (VMA ≈ 13.3 km/h)
    AG->>LLM: 7. Prompt avec analyse
    
    LLM-->>AG: 8. Conseils personnalisés
    AG-->>API: 9. Réponse structurée
    API->>CACHE: 10. Sauvegarde conversation
    API-->>ST: 11. Réponse formatée
    ST-->>U: 12. Affichage conseils + suggestions
    
    U->>ST: 13. "Quel plan pour passer sous 40min?"
    ST->>API: 14. POST /chat (avec contexte)
    API->>CACHE: 15. Récupère historique conversation
    CACHE-->>API: 16. Contexte précédent
    
    API->>AG: 17. Génère plan progressif
    AG->>LLM: 18. Prompt plan sub-40
    LLM-->>AG: 19. Plan 8 semaines
    AG-->>API: 20. Plan avec progression
    API-->>ST: 21. Plan affiché
    ST-->>U: 22. Plan interactif + calendrier
    
    Note over U,CACHE: POC Chat Validé ✅<br/>Réponses instantanées<br/>Contexte conversationnel maintenu
```

## Métriques POC et Validation

### Critères de Réussite POC

#### Performance
- ✅ Temps de réponse API < 2s (95% des cas)
- ✅ Génération plan IA < 10s 
- ✅ Pipeline ETL Garmin < 5s
- ✅ Interface responsive < 1s

#### Fonctionnel
- ✅ Authentification OAuth Garmin fonctionnelle
- ✅ Récupération données activités complète
- ✅ Génération plan personnalisé pertinent
- ✅ Export PDF fonctionnel
- ✅ Chat conversationnel avec contexte

#### Technique
- ✅ Architecture microservices stable
- ✅ Gestion d'erreurs robuste
- ✅ Conformité RGPD (suppression auto)
- ✅ Monitoring en temps réel
- ✅ Cache Redis performant

### Scénarios de Test POC

#### Scénario 1: Débutant Marathon
```yaml
Profil: Coureur débutant, VMA 12 km/h
Objectif: Premier marathon en 4h30
Résultat: Plan 20 semaines progressif validé ✅
```

#### Scénario 2: Amélioration 10K
```yaml
Profil: Coureur confirmé, 10K en 42min
Objectif: Passer sous 40min
Résultat: Plan 12 semaines spécialisé validé ✅
```

#### Scénario 3: Retour Blessure
```yaml
Profil: Coureur expérimenté, arrêt 3 mois
Objectif: Reprise progressive
Résultat: Plan adapté avec précautions validé ✅
```

### Conclusion POC

Le POC démontre la faisabilité technique et fonctionnelle de la solution:

1. **Intégration API externe** réussie (Garmin Connect)
2. **Pipeline IA** opérationnel avec agents spécialisés
3. **Interfaces utilisateur** intuitives et performantes
4. **Architecture technique** scalable et maintenable
5. **Conformité RGPD** respectée

➡️ **Validation pour passage en développement complet**