## Carte des flux IA → métriques

- **Entrées FastAPI**:
  - POST `/v1/coaching/chat` → `AIService.chat_stream` → `coaching_agent.astream` → LLM (LangGraph/LangChain)
  - POST `/v1/coaching/chat-legacy` → `AIService.chat_legacy_stream` → `coaching_agent.astream`
  - POST `/v1/coaching/generate-training-plan` → `AIService.generate_training_plan` → `coaching_agent.invoke`
  - POST `/v1/coaching/generate-training-plan-advanced` → `coaching_agent.astream` (dans route avancée)

- **Callbacks LangChain/LangGraph**:
  - `FastAPIPrometheusCallback` (`prometheus_callback.py`) avec `on_llm_start|end|error` — enregistré dans `AIService.chat_stream`.

- **Provider OpenAI**:
  - `advanced_agent.py: make_llm()` → `ChatOpenAI(model="gpt-3.5-turbo")`. Token usage via `response.llm_output.token_usage`.

- **/metrics**:
  - `fastapi_app/main.py:/metrics` expose `generate_latest()` (registre par défaut, pas `app_registry`).

## Points d’accroche métriques (fichier:ligne)

- Streaming (chunks/end):
  - `services/ai_service.py:48-57` et `88-89` (boucles `async for … yield`).
  - `api_service.py:191-200`, `229-237` (stream depuis endpoints non-modulaires).

- Génération non-stream:
  - `services/ai_service.py:134-161` (invoke plan). Endpoint simple et avancé dans `api_service.py`/`routers/coaching.py`.

- Callbacks LLM:
  - `prometheus_callback.py:56-127` (tokens, latence, coût). Enregistré dans `services/ai_service.py:26-31`.

- Rate limiting:
  - `middleware/rate_limit.py:18-22` (SlowAPI handler — pas d’incrément 429).

- Auth/JWT:
  - `fastapi_auth_middleware.py:27-41` (401), `65-67` (403).

- Dépendances (DB):
  - `django_db_connector.py:test_connection 212-235` (ajouter gauge up + histogram latency).

- Export /metrics:
  - `fastapi_app/main.py:141-152` → `generate_latest()` (ne cible pas `app_registry`).

## Risques de cardinalité

- Éviter `user_id`, `thread_id` en labels. Préférer: `endpoint`, `model`, `mode`, `status`, `dependency_name`, `error_type`.

## Manques / Gaps

- Pas de compteurs 429 sur rate limit; pas de métriques auth 401/403.
- Pas de métriques DB up/latence.
- /metrics n’utilise pas `app_registry` dédié.
- Callbacks non branchés sur tous les chemins (legacy/advanced route directe).
- Pas de gestion d’abandon de stream (abort/cancel) ni compteur associé.
- Doublons de définitions de métriques (risque conflits).

## 5 priorités d’instrumentation (faible cardinalité)

1) `services/ai_service.py:48-57` et `88-89` — incrémenter `app_ai_stream_chunks_total` dans la boucle et `app_ai_stream_aborts_total` au catch; observer `app_ai_request_duration_seconds` en finally; labels: endpoint, model, mode, status.

2) `prometheus_callback.py:62-101` — compter `agent_llm_requests_total` (status ok/error), observer `agent_llm_latency_seconds`, incrémenter `agent_llm_tokens_total` (prompt|completion) et `agent_llm_cost_usd_total`; label `model` (+ `mode` pour requests).

3) `fastapi_app/main.py:141-152` — utiliser `generate_latest(app_registry)` si app_registry est la source des métriques; sinon unifier les définitions.

4) `middleware/rate_limit.py:18-22` — sur 429, incrémenter `rate_limit_hits_total` avec label `endpoint`.

5) `django_db_connector.py:212-235` — `dependency_up{name="postgres_django"}`, `dependency_latency_seconds{name="postgres_django"}` autour du test.

Labels autorisés: endpoint, model, mode, status, method, tool_name, error_type, dependency_name.


