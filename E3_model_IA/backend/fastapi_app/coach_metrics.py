"""
Métriques spécialisées pour Coach AI - OpenAI et Agent IA
"""
from prometheus_client import Counter, Histogram, Gauge, start_http_server, generate_latest
import time
from functools import wraps

# ========== MÉTRIQUES OPENAI ==========
openai_requests_total = Counter(
    'openai_requests_total',
    'Nombre total de requetes vers OpenAI',
    ['model', 'endpoint']
)

openai_errors_total = Counter(
    'openai_errors_total', 
    'Nombre total d erreurs OpenAI',
    ['error_type']
)

openai_response_time = Histogram(
    'openai_response_time_seconds',
    'Temps de reponse OpenAI en secondes',
    ['model']
)

openai_tokens_used = Counter(
    'openai_tokens_used_total',
    'Nombre total de tokens utilises',
    ['type', 'model']  # type: prompt_tokens, completion_tokens
)

openai_cost_usd = Counter(
    'openai_cost_usd_total',
    'Cout total estime en USD',
    ['model']
)

# ========== MÉTRIQUES AGENT IA ==========
training_plans_generated = Counter(
    'training_plans_generated_total',
    'Nombre total de plans d entrainement generes',
    ['objective', 'level']  # ex: 10K, semi, débutant, avancé
)

coaching_sessions_total = Counter(
    'coaching_sessions_total',
    'Nombre total de sessions de coaching',
    ['session_type']  # conversation, plan_generation
)

coaching_session_duration = Histogram(
    'coaching_session_duration_seconds',
    'Duree des sessions de coaching en secondes'
)

user_activities_analyzed = Counter(
    'user_activities_analyzed_total',
    'Nombre d activites utilisateur analysees'
)

database_queries_total = Counter(
    'database_queries_total',
    'Nombre total de requetes base de donnees',
    ['query_type', 'status']  # select, insert, success, error
)

# ========== MÉTRIQUES EN TEMPS RÉEL ==========
active_users = Gauge(
    'active_users_current',
    'Nombre d utilisateurs actifs actuellement'
)

knowledge_base_size = Gauge(
    'knowledge_base_documents_total',
    'Nombre de documents dans la base de connaissances'
)

# ========== COÛTS ET QUOTAS ==========
# Prix approximatifs OpenAI (à ajuster)
MODEL_PRICING = {
    'gpt-3.5-turbo': {
        'input': 0.0015 / 1000,   # $0.0015 per 1K input tokens
        'output': 0.002 / 1000,   # $0.002 per 1K output tokens
    },
    'gpt-4': {
        'input': 0.03 / 1000,     # $0.03 per 1K input tokens  
        'output': 0.06 / 1000,    # $0.06 per 1K output tokens
    }
}

# ========== DÉCORATEURS POUR INSTRUMENTER ==========
def monitor_openai_call(model='gpt-3.5-turbo'):
    """Décorateur pour monitorer les appels OpenAI"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            openai_requests_total.labels(model=model, endpoint='chat').inc()
            
            try:
                result = func(*args, **kwargs)
                
                # Mesure du temps de réponse
                duration = time.time() - start_time
                openai_response_time.labels(model=model).observe(duration)
                
                # Extraction des tokens si disponible
                if hasattr(result, 'usage'):
                    prompt_tokens = result.usage.prompt_tokens
                    completion_tokens = result.usage.completion_tokens
                    
                    openai_tokens_used.labels(type='prompt', model=model).inc(prompt_tokens)
                    openai_tokens_used.labels(type='completion', model=model).inc(completion_tokens)
                    
                    # Calcul du coût estimé
                    if model in MODEL_PRICING:
                        cost = (prompt_tokens * MODEL_PRICING[model]['input'] + 
                               completion_tokens * MODEL_PRICING[model]['output'])
                        openai_cost_usd.labels(model=model).inc(cost)
                
                return result
                
            except Exception as e:
                error_type = type(e).__name__
                openai_errors_total.labels(error_type=error_type).inc()
                raise
                
        return wrapper
    return decorator

def monitor_training_plan_generation(objective, level):
    """Décorateur pour monitorer la génération de plans"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                training_plans_generated.labels(objective=objective, level=level).inc()
                return result
            finally:
                duration = time.time() - start_time
                coaching_session_duration.observe(duration)
                
        return wrapper
    return decorator

def monitor_coaching_session(session_type='conversation'):
    """Décorateur pour monitorer les sessions de coaching"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            coaching_sessions_total.labels(session_type=session_type).inc()
            start_time = time.time()
            
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.time() - start_time
                coaching_session_duration.observe(duration)
                
        return wrapper
    return decorator

# ========== FONCTIONS UTILITAIRES ==========
def update_active_users(count):
    """Met à jour le nombre d'utilisateurs actifs"""
    active_users.set(count)

def update_knowledge_base_size(count):
    """Met à jour la taille de la base de connaissances"""
    knowledge_base_size.set(count)

def record_database_query(query_type, status='success'):
    """Enregistre une requête base de données"""
    database_queries_total.labels(query_type=query_type, status=status).inc()

def get_metrics_summary():
    """Retourne un résumé des métriques pour debug"""
    try:
        # Utilise les méthodes collect() pour accéder aux valeurs des métriques
        openai_count = sum([sample.value for sample in openai_requests_total.collect()[0].samples])
        plans_count = sum([sample.value for sample in training_plans_generated.collect()[0].samples])
        sessions_count = sum([sample.value for sample in coaching_sessions_total.collect()[0].samples])
        errors_count = sum([sample.value for sample in openai_errors_total.collect()[0].samples])
        
        return {
            'openai_requests': openai_count,
            'training_plans': plans_count,
            'coaching_sessions': sessions_count,
            'openai_errors': errors_count,
            'active_users': active_users._value._value if hasattr(active_users._value, '_value') else 0,
            'knowledge_base_docs': knowledge_base_size._value._value if hasattr(knowledge_base_size._value, '_value') else 0
        }
    except Exception as e:
        return {'error': f'Erreur collecte métriques: {str(e)}'}