"""
Metriques Prometheus pour monitoring OpenAI et Coach AI
"""
from prometheus_client import Counter, Histogram, start_http_server

# Metriques OpenAI
openai_requests_total = Counter(
    'openai_requests_total',
    'Nombre total de requetes OpenAI'
)

openai_errors_total = Counter(
    'openai_errors_total', 
    'Nombre total d\'erreurs OpenAI'
)

openai_response_time = Histogram(
    'openai_response_time_seconds',
    'Temps de reponse OpenAI en secondes'
)

# Metriques Coach AI
training_plans_generated = Counter(
    'training_plans_generated_total',
    'Nombre total de plans d\'entrainement generes'
)

user_activities_processed = Counter(
    'user_activities_processed_total',
    'Nombre total d\'activites utilisateur traitees'
)

database_queries_total = Counter(
    'database_queries_total',
    'Nombre total de requetes base de donnees',
    ['query_type']
)

def start_metrics_server(port=8080):
    """Demarre le serveur de metriques Prometheus"""
    start_http_server(port)
    print(f"Serveur metriques Prometheus demarre sur le port {port}")