from fastapi import FastAPI, Request, Response
from prometheus_client import Counter, Histogram, Gauge, CONTENT_TYPE_LATEST, generate_latest
import time

# --- Requêtes & latence ---
APP_REQ = Counter(
    "app_ai_requests_total", "Total des requêtes", ["endpoint", "model", "status"]
)
APP_LAT = Histogram(
    "app_ai_request_duration_seconds", "Latence requêtes", ["endpoint", "model"],
    buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10)
)

# --- Tokens LLM ---
AGENT_TOKENS = Counter(
    "agent_llm_tokens_total", "Tokens LLM", ["type", "model"]
)

# --- Coût LLM (pour panneau coût) ---
AGENT_COST_USD = Counter(
    "agent_llm_cost_usd_total", "Coût LLM en USD", ["model"]
)

# --- Streams ---
STREAM_CHUNKS = Counter(
    "app_ai_stream_chunks_total", "Chunks stream envoyés par réponse", []
)
STREAM_ABORTS = Counter(
    "app_ai_stream_aborts_total", "Streams abandonnés", ["model", "mode"]
)

# --- Rate limiting ---
RATE_LIMIT_HITS = Counter(
    "rate_limit_hits_total", "Hits de rate limiting (HTTP 429)", ["endpoint"]
)

# --- Dépendances ---
DEP_UP = Gauge("dependency_up", "Dépendance up/down", ["name"])
DEP_LAT = Histogram(
    "dependency_latency_seconds", "Latence dépendance", ["name"],
    buckets=(0.01, 0.05, 0.1, 0.2, 0.5, 1, 2)
)


def instrument_app(app: FastAPI) -> None:
    @app.middleware("http")
    async def prom_mw(request: Request, call_next):
        endpoint = request.url.path
        model = request.headers.get("X-Model", "unknown")
        start = time.perf_counter()
        status_code = "500"
        try:
            response = await call_next(request)
            status_code = str(response.status_code)
            return response
        finally:
            dur = time.perf_counter() - start
            APP_LAT.labels(endpoint, model).observe(dur)
            ok = status_code.startswith(("2", "3"))
            APP_REQ.labels(endpoint, model, "ok" if ok else "error").inc()

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/health")
    def health():
        return {"status": "ok"}


def record_llm_usage(response) -> None:
    model_name = getattr(response, "model", "unknown")
    usage = getattr(response, "usage", None)
    if not usage:
        return
    try:
        prompt_tokens = getattr(usage, "prompt_tokens", 0) or 0
        completion_tokens = getattr(usage, "completion_tokens", 0) or 0
        total_tokens = getattr(usage, "total_tokens", prompt_tokens + completion_tokens)
        AGENT_TOKENS.labels("prompt", model_name).inc(prompt_tokens)
        AGENT_TOKENS.labels("completion", model_name).inc(completion_tokens)
        AGENT_TOKENS.labels("total", model_name).inc(total_tokens)
    except Exception:
        pass


