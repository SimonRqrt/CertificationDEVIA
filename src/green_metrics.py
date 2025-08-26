"""
Métriques éco-conception pour monitoring Green IT
Conformité critère 168 - Bonnes pratiques d'éco-conception
"""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import psutil
import time
from functools import lru_cache

# Registry pour métriques Green IT
green_registry = CollectorRegistry()

# Métriques environnementales
energy_consumption_watts = Gauge(
    'app_energy_consumption_watts', 
    'Consommation énergétique estimée en watts',
    registry=green_registry
)

cache_hit_ratio = Gauge(
    'cache_efficiency_ratio', 
    'Ratio d\'efficacité du cache (0-1)',
    registry=green_registry
)

network_transfer_bytes = Counter(
    'network_transfer_total_bytes', 
    'Octets transférés total',
    ['direction'],  # 'in' ou 'out'
    registry=green_registry
)

page_size_bytes = Histogram(
    'page_size_bytes',
    'Taille des pages servies en octets',
    buckets=[1024, 5120, 10240, 51200, 102400, 512000, 1048576],  # 1KB à 1MB
    registry=green_registry
)

cpu_efficiency = Gauge(
    'cpu_efficiency_ratio',
    'Ratio d\'efficacité CPU (requêtes/seconde par % CPU)',
    registry=green_registry
)

class GreenMetricsCollector:
    """Collecteur de métriques éco-conception"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.cache_hits = 0
        self.cache_requests = 0
        
    def record_request(self, response_size_bytes: int):
        """Enregistre une requête pour les métriques Green IT"""
        self.request_count += 1
        page_size_bytes.observe(response_size_bytes)
        network_transfer_bytes.labels(direction='out').inc(response_size_bytes)
        
        # Mise à jour efficacité CPU toutes les 100 requêtes
        if self.request_count % 100 == 0:
            self.update_cpu_efficiency()
    
    def record_cache_hit(self, hit: bool):
        """Enregistre un hit/miss de cache"""
        self.cache_requests += 1
        if hit:
            self.cache_hits += 1
        
        # Mise à jour ratio cache
        if self.cache_requests > 0:
            ratio = self.cache_hits / self.cache_requests
            cache_hit_ratio.set(ratio)
    
    def update_energy_consumption(self):
        """Calcule et met à jour la consommation énergétique estimée"""
        try:
            # Consommation CPU (estimation basée sur l'utilisation)
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_watts = (cpu_percent / 100) * 65  # CPU typique 65W max
            
            # Consommation RAM (estimation)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_watts = (memory_percent / 100) * 20  # RAM typique 20W max
            
            # Consommation réseau (estimation basée sur I/O)
            network_io = psutil.net_io_counters()
            network_watts = min((network_io.bytes_sent + network_io.bytes_recv) / 1e9, 10)
            
            total_watts = cpu_watts + memory_watts + network_watts
            energy_consumption_watts.set(total_watts)
            
        except Exception as e:
            print(f"Erreur calcul consommation énergétique: {e}")
            energy_consumption_watts.set(0)
    
    def update_cpu_efficiency(self):
        """Calcule l'efficacité CPU (requêtes/seconde par % CPU)"""
        try:
            elapsed_time = time.time() - self.start_time
            requests_per_second = self.request_count / elapsed_time if elapsed_time > 0 else 0
            
            cpu_percent = psutil.cpu_percent()
            if cpu_percent > 0:
                efficiency = requests_per_second / cpu_percent
                cpu_efficiency.set(efficiency)
            
        except Exception as e:
            print(f"Erreur calcul efficacité CPU: {e}")
            cpu_efficiency.set(0)

# Instance globale du collecteur
green_collector = GreenMetricsCollector()

@lru_cache(maxsize=128)
def calculate_carbon_footprint(requests_per_day: int) -> dict:
    """
    Calcule l'empreinte carbone quotidienne estimée
    
    Args:
        requests_per_day: Nombre de requêtes par jour
        
    Returns:
        dict: Métriques d'empreinte carbone
    """
    server_kwh = requests_per_day * 0.0001
    
    network_kwh = requests_per_day * 0.00005
    
    client_kwh = requests_per_day * 0.00002
    
    total_kwh = server_kwh + network_kwh + client_kwh
    
    co2_factor = 57
    
    total_co2_grams = total_kwh * co2_factor
    
    return {
        'daily_co2_grams': round(total_co2_grams, 2),
        'monthly_co2_kg': round(total_co2_grams * 30 / 1000, 2),
        'yearly_co2_kg': round(total_co2_grams * 365 / 1000, 2),
        'equivalent_km_car': round(total_co2_grams / 120, 2),  # 120g CO2/km voiture
        'equivalent_trees': round(total_co2_grams / 20000, 3),  # 20kg CO2/an par arbre
        'server_kwh': round(server_kwh, 4),
        'network_kwh': round(network_kwh, 4),
        'client_kwh': round(client_kwh, 4),
        'total_kwh': round(total_kwh, 4)
    }

def get_ecoindex_score(dom_size: int, transfer_size_kb: int, http_requests: int) -> dict:
    """
    Calcule le score EcoIndex selon la méthodologie officielle
    
    Args:
        dom_size: Nombre d'éléments DOM
        transfer_size_kb: Taille transfert en KB
        http_requests: Nombre de requêtes HTTP
        
    Returns:
        dict: Score EcoIndex et grade
    """
    # Formule EcoIndex officielle (quantiles 2024)
    score_dom = max(0, 100 - (5 * (dom_size - 100) / 900))
    score_transfer = max(0, 100 - (5 * (transfer_size_kb - 100) / 1900))
    score_requests = max(0, 100 - (5 * (http_requests - 5) / 95))
    
    # Score final (moyenne pondérée)
    ecoindex_score = (score_dom + score_transfer + score_requests) / 3
    
    # Détermination du grade
    if ecoindex_score >= 75:
        grade = 'A'
        color = '#349A47'
    elif ecoindex_score >= 65:
        grade = 'B'
        color = '#51B651'
    elif ecoindex_score >= 50:
        grade = 'C'
        color = '#CADB2A'
    elif ecoindex_score >= 35:
        grade = 'D'
        color = '#F6EB14'
    elif ecoindex_score >= 20:
        grade = 'E'
        color = '#FECD06'
    elif ecoindex_score >= 5:
        grade = 'F'
        color = '#F99839'
    else:
        grade = 'G'
        color = '#ED2124'
    
    return {
        'score': round(ecoindex_score, 1),
        'grade': grade,
        'color': color,
        'dom_score': round(score_dom, 1),
        'transfer_score': round(score_transfer, 1),
        'requests_score': round(score_requests, 1),
        'recommendations': get_ecoindex_recommendations(ecoindex_score, dom_size, transfer_size_kb, http_requests)
    }

def get_ecoindex_recommendations(score: float, dom_size: int, transfer_size_kb: int, http_requests: int) -> list:
    """Génère des recommandations d'amélioration EcoIndex"""
    recommendations = []
    
    if dom_size > 500:
        recommendations.append(f"Réduire le DOM ({dom_size} éléments) : lazy loading, pagination")
    
    if transfer_size_kb > 1000:
        recommendations.append(f"Optimiser le poids ({transfer_size_kb}KB) : compression, WebP, minification")
    
    if http_requests > 50:
        recommendations.append(f"Réduire les requêtes ({http_requests}) : bundling, sprites, cache")
    
    if score < 50:
        recommendations.extend([
            "Implémenter un CDN vert",
            "Activer le cache navigateur",
            "Optimiser les images (format moderne)",
            "Minifier CSS/JS",
            "Utiliser la compression gzip/brotli"
        ])
    
    return recommendations

# Exemple d'utilisation pour monitoring
def monitor_green_metrics():
    """Fonction de monitoring continue des métriques vertes"""
    green_collector.update_energy_consumption()
    
    # Exemple de page type Coach IA
    ecoindex = get_ecoindex_score(
        dom_size=250,
        transfer_size_kb=180,
        http_requests=12
    )
    
    carbon_footprint = calculate_carbon_footprint(1000)
    
    return {
        'ecoindex': ecoindex,
        'carbon_footprint': carbon_footprint,
        'energy_watts': energy_consumption_watts._value._value,
        'cache_efficiency': cache_hit_ratio._value._value,
        'cpu_efficiency': cpu_efficiency._value._value
    }

if __name__ == "__main__":
    # Test des métriques
    results = monitor_green_metrics()
    print("Métriques Green IT:")
    print(f"Score EcoIndex: {results['ecoindex']['score']} ({results['ecoindex']['grade']})")
    print(f"Empreinte carbone: {results['carbon_footprint']['daily_co2_grams']}g CO2/jour")
    print(f"Consommation: {results['energy_watts']}W")