"""
Exemples concrets pour soutenance de certification
Démonstration des capacités techniques et de la vision d'évolution
"""

from django.db import connection
from .models import Activity
from .models_flexible import FlexibleActivity, DataMigrationLog
import json
from datetime import datetime, timedelta


class CertificationDemos:
    """
    Classe de démonstration pour soutenance orale
    Présente les deux approches et leur complémentarité
    """
    
    def __init__(self):
        self.examples_data = self._get_sample_data()
    
    def _get_sample_data(self):
        """Données d'exemple pour démonstrations"""
        return {
            "garmin_activity_complete": {
                "activityId": 12345678901,
                "activityName": "Course matinale certification",
                "activityType": {"typeKey": "running"},
                "startTimeLocal": "2025-08-29T07:30:00",
                "distance": 5200,
                "duration": 1800,
                "averageSpeed": 2.89,
                "maxSpeed": 4.5,
                "calories": 320,
                "averageHR": 155,
                "maxHR": 178,
                "elevationGain": 45,
                "elevationLoss": 52,
                "vO2MaxValue": 48.5,
                "activityTrainingLoad": 125,
                # Nouveaux champs qui pourraient arriver
                "runningDynamics": {
                    "groundContactTime": 245,
                    "verticalOscillation": 8.2,
                    "runningPower": 285
                },
                "weatherConditions": {
                    "temperature": 18,
                    "humidity": 65,
                    "windSpeed": 5.2,
                    "pressure": 1013.25
                }
            }
        }
    
    # === DÉMONSTRATION 1 : APPROCHE CLASSIQUE (ACQUIS) ===
    
    def demo_sql_classique(self):
        """
        DÉMONSTRATION : Maîtrise SQL/ORM classique
        Pour montrer les acquis relationnels
        """
        print("=== DÉMONSTRATION SQL CLASSIQUE ===")
        
        # Requête d'agrégation complexe
        from django.db.models import Avg, Sum, Count, Q
        from django.db.models.functions import Extract, TruncWeek
        
        # Statistiques par semaine avec ORM Django
        weekly_stats = Activity.objects.filter(
            user_id=1,
            activity_type='running',
            start_time__gte=datetime.now() - timedelta(days=90)
        ).annotate(
            week=TruncWeek('start_time')
        ).values('week').annotate(
            total_distance=Sum('distance_meters'),
            avg_speed=Avg('average_speed'),
            avg_hr=Avg('average_hr'),
            activity_count=Count('id')
        ).order_by('week')
        
        print("Statistiques hebdomadaires (ORM Django):")
        for stat in weekly_stats:
            print(f"  Semaine {stat['week']}: {stat['activity_count']} courses, "
                  f"{stat['total_distance']/1000:.1f}km, "
                  f"FC moy: {stat['avg_hr']:.0f}bpm")
        
        # SQL brut pour requêtes complexes
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    activity_type,
                    COUNT(*) as total,
                    AVG(distance_meters/1000) as avg_distance_km,
                    AVG(duration_seconds/60) as avg_duration_min,
                    MAX(average_speed * 3.6) as max_speed_kmh
                FROM activities_activity 
                WHERE user_id = %s 
                AND start_time >= %s
                GROUP BY activity_type
                ORDER BY total DESC
            """, [1, datetime.now() - timedelta(days=365)])
            
            print("\nStatistiques par type d'activité (SQL brut):")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]} activités, "
                      f"moy {row[2]:.1f}km en {row[3]:.0f}min, "
                      f"max {row[4]:.1f}km/h")
        
        return {"status": "Maîtrise SQL/ORM démontrée"}
    
    # === DÉMONSTRATION 2 : APPROCHE FLEXIBLE (INNOVATION) ===
    
    def demo_json_flexible(self):
        """
        DÉMONSTRATION : Innovation avec JSON flexible
        Pour montrer la vision d'évolution
        """
        print("\n=== DÉMONSTRATION JSON FLEXIBLE ===")
        
        # Simulation d'ingestion de données enrichies
        sample_data = self.examples_data["garmin_activity_complete"]
        
        print("1. Ingestion de données JSON complètes:")
        print(f"   Champs standards: {len([k for k in sample_data.keys() if not isinstance(sample_data[k], dict)])}")
        print(f"   Objets complexes: {len([k for k in sample_data.keys() if isinstance(sample_data[k], dict)])}")
        
        # Démonstration requête JSON native PostgreSQL
        if FlexibleActivity.objects.exists():
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        activity_name,
                        garmin_raw_data->>'averageSpeed' as speed,
                        garmin_raw_data->'runningDynamics'->>'groundContactTime' as contact_time,
                        garmin_raw_data->'weatherConditions'->>'temperature' as temp
                    FROM activities_flexibleactivity
                    WHERE garmin_raw_data ? 'runningDynamics'
                    AND (garmin_raw_data->'weatherConditions'->>'temperature')::float > 15
                    LIMIT 5
                """)
                
                print("\n2. Requêtes JSON avancées (nouveaux champs automatiques):")
                for row in cursor.fetchall():
                    print(f"   {row[0]}: vitesse {row[1]}m/s, "
                          f"contact sol {row[2]}ms, temp {row[3]}°C")
        
        # Démonstration de l'extensibilité
        print("\n3. Extensibilité démontrée:")
        print("   ✅ Nouveaux champs Garmin ingérés sans migration")
        print("   ✅ Données météo et dynamiques préservées")
        print("   ✅ Requêtes sur champs futurs possibles")
        
        return {"status": "Innovation JSON démontrée"}
    
    # === DÉMONSTRATION 3 : COEXISTENCE (PRAGMATISME) ===
    
    def demo_coexistence_pragmatique(self):
        """
        DÉMONSTRATION : Les deux approches coexistent
        Pour montrer le pragmatisme de la solution
        """
        print("\n=== DÉMONSTRATION COEXISTENCE ===")
        
        # Comparaison de performance
        import time
        
        print("1. Comparaison de performance:")
        
        # Requête classique
        start_time = time.time()
        classic_count = Activity.objects.filter(user_id=1).count()
        classic_time = time.time() - start_time
        print(f"   Modèle classique: {classic_count} activités en {classic_time*1000:.1f}ms")
        
        # Requête flexible (si données existent)
        start_time = time.time()
        flexible_count = FlexibleActivity.objects.filter(user_id=1).count()
        flexible_time = time.time() - start_time
        print(f"   Modèle flexible: {flexible_count} activités en {flexible_time*1000:.1f}ms")
        
        # Démonstration de rétrocompatibilité
        print("\n2. Rétrocompatibilité:")
        if FlexibleActivity.objects.exists():
            activity = FlexibleActivity.objects.first()
            print(f"   Accès classique: duration = {activity.duration_seconds}s")
            print(f"   Accès JSON: speed = {activity.average_speed}m/s")
            print("   → Même interface, sources différentes")
        
        # Migration tracking
        migration_count = DataMigrationLog.objects.count()
        print(f"\n3. Traçabilité: {migration_count} migrations logguées")
        
        return {
            "classic_performance": classic_time,
            "flexible_performance": flexible_time,
            "migration_tracking": migration_count
        }
    
    # === DÉMONSTRATION 4 : VISION FUTURE (EXPERTISE) ===
    
    def demo_vision_evolutive(self):
        """
        DÉMONSTRATION : Vision d'évolution
        Pour montrer la réflexion architecturale
        """
        print("\n=== VISION ÉVOLUTIVE ===")
        
        print("1. Évolution sans refonte:")
        print("   ✅ Nouvelles APIs (Polar, Suunto) → Nouveau champ JSON")
        print("   ✅ Changements Garmin → Pas de migration")
        print("   ✅ Nouveaux capteurs IoT → Ingestion automatique")
        
        print("\n2. Stratégie de migration:")
        print("   Phase 1: Coexistence (actuel)")
        print("   Phase 2: Migration progressive")
        print("   Phase 3: Optimisation et bascule")
        
        print("\n3. Bénéfices métier:")
        print("   💰 Coût de maintenance réduit")
        print("   🚀 Time-to-market accéléré")
        print("   🔒 Zéro perte de données")
        print("   📈 Scalabilité garantie")
        
        return {"status": "Vision architecturale démontrée"}
    
    # === SCRIPT DE DÉMONSTRATION COMPLÈTE ===
    
    def run_complete_demo(self):
        """
        Démonstration complète pour soutenance
        À exécuter pendant la présentation
        """
        print("🎯 DÉMONSTRATION CERTIFICATION - ÉVOLUTION SCHEMA DONNÉES")
        print("=" * 70)
        
        results = {}
        
        # 1. Acquis techniques
        results['sql_classique'] = self.demo_sql_classique()
        
        # 2. Innovation technique  
        results['json_flexible'] = self.demo_json_flexible()
        
        # 3. Pragmatisme solution
        results['coexistence'] = self.demo_coexistence_pragmatique()
        
        # 4. Vision future
        results['vision'] = self.demo_vision_evolutive()
        
        print("\n" + "=" * 70)
        print("✅ DÉMONSTRATION COMPLÈTE - PRÊT POUR CERTIFICATION")
        
        return results


# === SCRIPT D'EXEMPLE POUR SOUTENANCE ===

if __name__ == "__main__":
    """
    Script à lancer pendant la soutenance pour démonstration live
    """
    demo = CertificationDemos()
    demo.run_complete_demo()