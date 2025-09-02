# Journal de veille — API IA & métriques sportives (C6)

**Auteur** : Simon Riquart  
**Thème** : API d’IA appliquées aux métriques d’entraînement (OpenAPI-first, agent IA)  
**Périmètre** : OpenAI (prioritaire), LangChain/LangGraph, Garmin/Strava, métriques (VO₂, HRV, charge d’entraînement, puissance), RAG/embeddings, observabilité (latence, erreurs, coût), conformité (RGPD).  
**Organisation** : planification **flexible** avec une **moyenne d’1 h/semaine**. Veille centralisée via **Inoreader** (RSS, Web feeds, newsletters), notes en **Markdown** (repo), exportables en HTML/PDF si besoin.

---

## Checklist accessibilité minimale (à appliquer à chaque note)
- Titres hiérarchisés (H1→H2→H3), liens explicites et descriptifs
- Alternatives textuelles pour schémas/captures
- Phrases courtes, vocabulaire simple, contraste suffisant dans les exports
- Tableaux légendés et sobres quand nécessaires

---

## Modèle d’entrée (copier/coller)
**Semaine** : Sx (≈ 60 min, session(s) flexible(s))  
**Focus** : …  
**Sources (Inoreader)** : …  
**Faits saillants** : …  
**Impacts** : … (agent, OpenAPI, RAG/embeddings, monitoring, RGPD)  
**Décisions** : …  
**Prochaines étapes** : …  
**Traçabilité** : commit `docs/veille/…` (durée, semaine)

---

## Entrées simulées (exemple réaliste, ~1 h/semaine)

### Semaine 1 — Cadrage & outillage (≈ 60 min)
**Focus** : cadrage de la thématique et mise en place d’Inoreader (RSS + Web feeds + newsletters).  
**Sources (Inoreader)** : docs API IA (OpenAI), LangChain/LangGraph, Garmin/Strava (portails développeurs).  
**Faits saillants** : constitution d’un périmètre resserré sur les API IA, l’intégration OpenAPI et les métriques sportives clés ; création de tags/règles pour prioriser VO₂, HRV, charge, puissance.  
**Impacts** : cadre de veille clair, bruit réduit ; base stable pour le benchmark (C7).  
**Décisions** : valider le format de note hebdo en Markdown, créer le journal versionné.  
**Prochaines étapes** : préparer un premier schéma JSON de sortie pour l’agent.  
**Traçabilité** : commit `docs/veille/S1_cadrage.md` (60 min).

### Semaine 2 — Contrats OpenAPI & sorties JSON (≈ 60 min)
**Focus** : contraintes de sortie JSON validables pour l’agent.  
**Sources (Inoreader)** : exemples OpenAPI/Swagger, guides de validation de schémas.  
**Faits saillants** : définition d’un schéma de plan d’entraînement (séances, intensités, durées, justifications).  
**Impacts** : réduction des post-traitements, meilleures garanties de conformité des réponses.  
**Décisions** : imposer la validation JSON côté API ; rejeter les réponses non conformes.  
**Prochaines étapes** : intégrer la validation dans FastAPI.  
**Traçabilité** : commit `docs/veille/S2_openapi_json.md` (60 min).

### Semaine 3 — RAG : ancrage des réponses (≈ 60 min)
**Focus** : RAG minimal pour adosser l’agent à un corpus interne (fiches métriques & principes d’entraînement).  
**Sources (Inoreader)** : docs LangChain/LangGraph, bonnes pratiques RAG.  
**Faits saillants** : sélection d’un format court de fiches, citations simples dans les réponses.  
**Impacts** : baisse attendue des hallucinations, traçabilité des justifications.  
**Décisions** : préparer un connecteur d’indexation minimal.  
**Prochaines étapes** : constituer un lot pilote de fiches métriques.  
**Traçabilité** : commit `docs/veille/S3_rag_minimal.md` (60 min).

### Semaine 4 — Embeddings & recherche (≈ 60 min)
**Focus** : choix d’embeddings compatibles avec l’existant ; test de requêtes simples.  
**Sources (Inoreader)** : docs embeddings, retours d’expérience intégration avec LangChain.  
**Faits saillants** : compromis pertinence/coût acceptable pour un premier jalon.  
**Impacts** : meilleure récupération contextuelle pour le RAG.  
**Décisions** : retenir une option par défaut à valider dans C7.  
**Prochaines étapes** : mesurer rapidement la qualité de récupération sur le lot pilote.  
**Traçabilité** : commit `docs/veille/S4_embeddings.md` (60 min).

### Semaine 5 — Observabilité (≈ 60 min)
**Focus** : instrumentation latence/erreurs/coûts côté API IA.  
**Sources (Inoreader)** : guides FastAPI/Prometheus, pratiques de traçage.  
**Faits saillants** : définition d’un tableau de bord minimal (latence P95, erreurs, coût/requête).  
**Impacts** : vision objective des compromis modèle/coût/latence.  
**Décisions** : exposer des métriques et activer un tableau de bord.  
**Prochaines étapes** : brancher la collecte sur l’API IA.  
**Traçabilité** : commit `docs/veille/S5_observabilite.md` (60 min).

### Semaine 6 — Sécurité & filtrage utilisateur (≈ 60 min)
**Focus** : authentification par jeton, filtrage par utilisateur, journalisation.  
**Sources (Inoreader)** : docs sécurité FastAPI/DRF, exemples de politiques de tokens.  
**Faits saillants** : clarification des rôles et des champs obligatoires côté tokens.  
**Impacts** : moindre risque d’accès croisé aux données ; conformité renforcée.  
**Décisions** : documenter la politique d’accès et la traçabilité des appels.  
**Prochaines étapes** : ajouter un log d’audit minimal.  
**Traçabilité** : commit `docs/veille/S6_securite.md` (60 min).

### Semaine 7 — Outillage de l’agent (≈ 60 min)
**Focus** : prompts/outils pour tenir compte des splits, zones, charges.  
**Sources (Inoreader)** : notes LangChain/LangGraph, exemples d’outils.  
**Faits saillants** : identification des paramètres clés à exposer à l’agent.  
**Impacts** : recommandations plus précises et explicables.  
**Décisions** : stabiliser un prompt d’agent de base.  
**Prochaines étapes** : organiser des tests comparatifs.  
**Traçabilité** : commit `docs/veille/S7_agent_outils.md` (60 min).

### Semaine 8 — Consolidation vers C7/C8 (≈ 60 min)
**Focus** : tri final vers benchmark (C7) et paramétrage (C8).  
**Sources (Inoreader)** : revue des synthèses précédentes.  
**Faits saillants** : classement par impact/effort et risques.  
**Impacts** : passage fluide de la veille à l’action (tests, intégration).  
**Décisions** : figer la shortlist de services et de paramètres.  
**Prochaines étapes** : lancer le benchmark C7 et le paramétrage C8.  
**Traçabilité** : commit `docs/veille/S8_consolidation.md` (60 min).
