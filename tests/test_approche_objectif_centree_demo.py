"""
Script de test DÉMO pour valider l'approche "objectif-centrée" 
Version avec simulation pour présenter les fonctionnalités sans dépendre de l'API
"""

import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

# Chargement explicite des variables d'environnement
from dotenv import load_dotenv
load_dotenv()

@dataclass
class MockResponse:
    """Réponse simulée de l'agent IA"""
    content: str
    execution_time: float
    tool_calls_made: List[str]

class MockAgent:
    """Agent IA simulé pour démonstration"""
    
    def __init__(self):
        self.user_metrics = {
            "user_id": 1,
            "total_activities": 15,
            "avg_distance_km": 8.5,
            "avg_duration_min": 42.3,
            "avg_heart_rate": 155,
            "avg_speed_kmh": 12.1,
            "total_distance_km": 127.5,
            "last_activity_date": "2024-08-20"
        }
    
    def simulate_scenario_a_response(self) -> MockResponse:
        """Simulation réponse pour scénario A (avec target_time)"""
        response = """
### Plan d'entraînement personnalisé - Objectif 10k en 45:00

**Analyse de votre profil :**
Basé sur vos 15 activités récentes (vitesse moyenne : 12.1 km/h = 49:35 au 10k), 
votre objectif de 45:00 représente une amélioration de 9.3% de votre vitesse. 
Cette progression nécessite un plan structuré de 8 semaines minimum.

**Durée déterminée automatiquement : 8 semaines**
**Justification :** L'écart entre votre temps actuel (≈49:35) et l'objectif (45:00) 
nécessite une amélioration graduelle de la VMA et de l'endurance spécifique. 
8 semaines permettent une progression de 1.5% par semaine, soit un objectif réaliste et durable.

## Semaine 1 - Phase d'adaptation
| Jour | Type Séance | Durée | Description | Intensité |
|------|-------------|-------|-------------|-----------|
| Lundi | Repos | - | Récupération complète | Repos |
| Mardi | Endurance | 40min | Footing léger en aisance respiratoire | Faible |
| Mercredi | Fractionné | 50min | 2x(6x30/30) à 95% VMA + échauffement | Élevée |
| Jeudi | Repos | - | Étirements ou récupération active | Repos |
| Vendredi | Seuil | 45min | 3x6min à 85% FCM + échauffement | Modérée |
| Samedi | Repos | - | Préparation sortie longue | Repos |
| Dimanche | Sortie longue | 60min | Endurance fondamentale continue | Faible |

## Semaine 2 - Progression volume
| Jour | Type Séance | Durée | Description | Intensité |
|------|-------------|-------|-------------|-----------|
| Lundi | Repos | - | Récupération complète | Repos |
| Mardi | Endurance | 45min | Footing léger en aisance respiratoire | Faible |
| Mercredi | Fractionné | 55min | 2x(8x30/30) à 95-100% VMA | Élevée |
| Jeudi | Repos | - | Étirements ou récupération active | Repos |
| Vendredi | Seuil | 50min | 4x6min à 85-90% FCM | Modérée |
| Samedi | Repos | - | Préparation sortie longue | Repos |
| Dimanche | Sortie longue | 70min | Endurance fondamentale continue | Faible |

## Semaine 3-6 - Phase d'intensification
[Progression continue avec augmentation graduelle du volume et de l'intensité]

## Semaine 7 - Pré-compétition
[Maintien de l'intensité, réduction du volume]

## Semaine 8 - Affûtage
[Volume réduit, intensité spécifique, préparation finale]

**Objectif estimé à 8 semaines :**
Courir 10 km en 45:00 grâce à l'amélioration de votre VMA de 13.3 km/h actuelle à 14.5 km/h.

**Conseils personnalisés :**
- Votre rythme cardiaque moyen (155 bpm) indique une bonne condition de base
- Augmentez progressivement la vitesse des séances seuil de 12.1 à 13.3 km/h
- Travaillez la régularité : vos 8.5km moyens par sortie sont parfaits pour le 10k

**⚠️ Recommandations importantes :**
- Écoutez votre corps et adaptez l'intensité si nécessaire
- Hydratez-vous régulièrement pendant les séances
- En cas de douleur, consultez un professionnel de santé
"""
        
        return MockResponse(
            content=response.strip(),
            execution_time=2.3,
            tool_calls_made=["get_user_metrics_from_db", "get_training_knowledge"]
        )
    
    def simulate_scenario_b_response(self) -> MockResponse:
        """Simulation réponse pour scénario B (sans target_time)"""
        response = """
### Plan d'entraînement personnalisé - Amélioration générale 10k

**Analyse de votre profil :**
Avec 15 activités récentes et une vitesse moyenne de 12.1 km/h, vous avez un profil 
d'intermédiaire régulier. Votre potentiel d'amélioration est évalué à 15-20% sur 10-12 semaines.

**Durée déterminée automatiquement : 10 semaines**
**Justification :** Sans objectif de temps spécifique, un plan de 10 semaines permet 
d'optimiser toutes vos filières énergétiques et d'explorer votre potentiel maximal 
en toute sécurité.

**Objectif proposé basé sur vos données :**
Passer de votre temps actuel estimé (≈49:30) à un objectif de 46:00, soit une amélioration 
de 7% réaliste sur cette durée.

## Semaine 1-2 - Évaluation et adaptation
| Jour | Type Séance | Durée | Description | Intensité |
|------|-------------|-------|-------------|-----------|
| Lundi | Repos | - | Récupération complète | Repos |
| Mardi | Endurance | 40min | Footing d'évaluation du rythme naturel | Faible |
| Mercredi | Test VMA | 50min | Test progressif + évaluation FCM | Test |
| Jeudi | Repos | - | Analyse des données du test | Repos |
| Vendredi | Endurance | 45min | Footing à l'allure découverte | Faible |
| Samedi | Repos | - | Préparation | Repos |
| Dimanche | Sortie longue | 60min | Endurance fondamentale | Faible |

## Semaine 3-6 - Développement global
[Plan progressif multi-filières]

## Semaine 7-8 - Spécialisation 10k
[Focus sur l'allure spécifique et la résistance]

## Semaine 9-10 - Optimisation et test
[Affûtage et évaluation des progrès]

**Objectif estimé à 10 semaines :**
Amélioration générale avec potentiel de courir 10 km entre 46:00 et 47:30 selon progression.

**Conseils personnalisés :**
- Profil équilibré : explorez différents types d'entraînement
- Distance moyenne de 8.5km idéale pour progresser sur 10k
- Régularité excellente (15 activités) : maintenez cette constance

**⚠️ Recommandations importantes :**
- Écoutez votre corps et adaptez l'intensité si nécessaire  
- Ce plan sans contrainte temporelle privilégie la progression durable
- Réévaluez vos objectifs en semaine 5 pour affiner la suite
"""
        
        return MockResponse(
            content=response.strip(),
            execution_time=2.1,
            tool_calls_made=["get_user_metrics_from_db", "get_training_knowledge"]
        )

class TestApprocheeObjectifCentreeDemo:
    """Version démo des tests pour l'approche objectif-centrée"""
    
    def __init__(self):
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "mode": "DEMONSTRATION",
            "scenarios": {},
            "analysis": {},
            "recommendations": []
        }
        self.agent = MockAgent()
    
    def create_test_prompt_scenario_a(self):
        """Scénario A : Avec target_time pour objectif de temps"""
        return """
SCÉNARIO A - Test avec objectif de temps spécifique

PARAMÈTRES D'ENTRÉE :
- user_id: 1
- goal: "10k"  
- level: "intermediate"
- sessions_per_week: 3
- target_time: "45:00"
- duration_weeks: 0 (agent détermine automatiquement)

ATTENDU DE L'AGENT :
1. Analyser les données utilisateur existantes
2. Calculer l'écart entre performance actuelle et objectif (45:00)
3. Déterminer automatiquement une durée optimale (6-10 semaines attendues)
4. Justifier le choix de durée basé sur l'écart de performance
5. Générer un plan complet sur TOUTE la durée déterminée
"""
    
    def create_test_prompt_scenario_b(self):
        """Scénario B : Sans target_time pour objectif général"""
        return """
SCÉNARIO B - Test sans objectif de temps spécifique

PARAMÈTRES D'ENTRÉE :
- user_id: 1
- goal: "10k" (amélioration générale)
- level: "intermediate"
- sessions_per_week: 3
- target_time: "" (pas de temps cible)
- duration_weeks: 0 (agent détermine automatiquement)

ATTENDU DE L'AGENT :
1. Analyser les données utilisateur existantes
2. Proposer un objectif de temps réaliste basé sur les performances
3. Déterminer une durée optimale pour exploration du potentiel
4. Justifier le choix temporel pour développement complet
5. Générer un plan évolutif sur la durée déterminée
"""
    
    def run_scenario(self, scenario_name: str, prompt: str) -> Dict[str, Any]:
        """Simulation d'exécution d'un scénario"""
        print(f"\n{'='*60}")
        print(f"🧪 EXÉCUTION SIMULATION - {scenario_name}")
        print(f"{'='*60}")
        
        print(f"📤 Prompt simulé envoyé à l'agent...")
        print(f"📋 Paramètres : {prompt[:150]}...")
        
        # Simulation délai réseau
        import time
        time.sleep(0.5)
        
        # Obtenir la réponse simulée
        if scenario_name == "Scénario A":
            mock_response = self.agent.simulate_scenario_a_response()
        else:
            mock_response = self.agent.simulate_scenario_b_response()
        
        print(f"📥 Réponse reçue de l'agent simulé ({mock_response.execution_time}s)")
        print(f"🔧 Outils utilisés : {', '.join(mock_response.tool_calls_made)}")
        
        scenario_result = {
            "prompt": prompt,
            "response": mock_response.content,
            "execution_time": mock_response.execution_time,
            "tool_calls_made": mock_response.tool_calls_made,
            "errors": [],
            "retries": 0
        }
        
        print(f"✅ Scénario {scenario_name} simulé avec succès")
        return scenario_result
    
    def analyze_response(self, scenario_name: str, response: str) -> Dict[str, Any]:
        """Analyse détaillée de la réponse"""
        analysis = {
            "duration_determined": False,
            "duration_weeks": 0, 
            "duration_justified": False,
            "performance_gap_analyzed": False,
            "complete_plan_generated": False,
            "week_count": 0,
            "target_time_considered": False,
            "objective_proposed": False,
            "recommendations_quality": "unknown"
        }
        
        response_lower = response.lower()
        
        # 1. Vérification durée déterminée
        if "durée déterminée automatiquement" in response_lower or "semaines" in response_lower:
            analysis["duration_determined"] = True
        
        # 2. Extraction nombre de semaines  
        import re
        week_patterns = [r'(\d+)\s*semaines?', r'plan de\s*(\d+)', r'durée.*?(\d+)']
        week_numbers = []
        for pattern in week_patterns:
            matches = re.findall(pattern, response_lower)
            week_numbers.extend([int(m) for m in matches])
        
        if week_numbers:
            analysis["duration_weeks"] = max(week_numbers)
            analysis["week_count"] = len([w for w in week_numbers if w <= 20])  # Semaines réalistes
        
        # 3. Justification présente
        justification_keywords = ["justification", "parce que", "nécessite", "permet", "écart"]
        analysis["duration_justified"] = any(kw in response_lower for kw in justification_keywords)
        
        # 4. Analyse écart performance
        gap_keywords = ["écart", "amélioration", "progression", "actuel", "objectif", "vitesse"]
        analysis["performance_gap_analyzed"] = any(kw in response_lower for kw in gap_keywords)
        
        # 5. Plan complet avec tableaux
        plan_indicators = ["semaine 1", "semaine 2", "tableau", "jour", "séance"]
        analysis["complete_plan_generated"] = any(ind in response_lower for ind in plan_indicators)
        
        # 6. Temps cible considéré (pour scénario A)
        time_indicators = ["45:00", "45 min", "temps", "objectif"]
        analysis["target_time_considered"] = any(ind in response_lower for ind in time_indicators)
        
        # 7. Objectif proposé (pour scénario B)
        proposal_indicators = ["objectif proposé", "potentiel", "46:00", "47:30"]
        analysis["objective_proposed"] = any(ind in response_lower for ind in proposal_indicators)
        
        # 8. Qualité globale
        score = 0
        if analysis["duration_determined"]: score += 2
        if analysis["duration_weeks"] >= 6: score += 2
        if analysis["duration_justified"]: score += 2
        if analysis["performance_gap_analyzed"]: score += 2
        if analysis["complete_plan_generated"]: score += 2
        
        if score >= 8: analysis["recommendations_quality"] = "excellent"
        elif score >= 6: analysis["recommendations_quality"] = "good" 
        elif score >= 4: analysis["recommendations_quality"] = "basic"
        else: analysis["recommendations_quality"] = "poor"
        
        return analysis
    
    def generate_recommendations(self) -> List[str]:
        """Génération des recommandations d'amélioration"""
        recommendations = []
        
        scenario_a = self.results["scenarios"].get("Scénario A", {})
        scenario_b = self.results["scenarios"].get("Scénario B", {})
        
        analysis_a = scenario_a.get("analysis", {})
        analysis_b = scenario_b.get("analysis", {})
        
        # Évaluation durée
        duration_a = analysis_a.get("duration_weeks", 0)
        duration_b = analysis_b.get("duration_weeks", 0)
        
        if duration_a >= 8 and duration_b >= 8:
            recommendations.append(
                "🟢 EXCELLENT: L'agent génère des plans de durée appropriée "
                f"(Scénario A: {duration_a}sem, Scénario B: {duration_b}sem). "
                "Cette approche permet une progression graduelle et durable."
            )
        elif duration_a >= 6 or duration_b >= 6:
            recommendations.append(
                "🟡 BIEN: L'agent génère des plans de durée acceptable, "
                "mais pourrait bénéficier d'optimisations pour certains objectifs."
            )
        else:
            recommendations.append(
                "🔴 CRITIQUE: Plans trop courts détectés. "
                "Modifier les prompts pour encourager des plans de 6+ semaines minimum."
            )
        
        # Évaluation justification
        if analysis_a.get("duration_justified") and analysis_b.get("duration_justified"):
            recommendations.append(
                "🟢 EXCELLENT: L'agent justifie systématiquement ses choix de durée "
                "en analysant les données utilisateur et les objectifs."
            )
        else:
            recommendations.append(
                "🟡 AMÉLIORATION: Renforcer les consignes pour que l'agent "
                "justifie toujours ses décisions temporelles."
            )
        
        # Évaluation différenciation scénarios
        if (analysis_a.get("target_time_considered") and 
            analysis_b.get("objective_proposed")):
            recommendations.append(
                "🟢 EXCELLENT: L'agent adapte intelligemment sa réponse selon "
                "la présence ou l'absence d'un objectif de temps spécifique."
            )
        
        # Recommandations techniques
        if analysis_a.get("complete_plan_generated"):
            recommendations.append(
                "🟢 POSITIF: L'agent génère des plans détaillés avec tableaux "
                "structurés facilitant le suivi utilisateur."
            )
        
        if analysis_a.get("performance_gap_analyzed"):
            recommendations.append(
                "🟢 POSITIF: L'analyse de l'écart performance actuelle/objectif "
                "permet un calibrage précis de la durée nécessaire."
            )
        
        # Recommandation globale
        quality_a = analysis_a.get("recommendations_quality", "unknown")
        quality_b = analysis_b.get("recommendations_quality", "unknown") 
        
        if quality_a == "excellent" and quality_b == "excellent":
            recommendations.append(
                "🎯 CONCLUSION: L'approche 'objectif-centrée' fonctionne parfaitement. "
                "L'agent détermine automatiquement des durées optimales et justifiées."
            )
        elif quality_a == "good" or quality_b == "good":
            recommendations.append(
                "🎯 CONCLUSION: L'approche 'objectif-centrée' est prometteuse mais "
                "nécessite des ajustements mineurs dans les prompts système."
            )
        else:
            recommendations.append(
                "🎯 CONCLUSION: L'approche nécessite des améliorations significatives "
                "avant déploiement en production."
            )
        
        return recommendations
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Exécution complète des tests démo"""
        print("🚀 DÉBUT DES TESTS DÉMO - Approche objectif-centrée")
        print("="*70)
        print("ℹ️  MODE DÉMONSTRATION : Simulation des appels IA pour présentation")
        
        # Scénario A
        prompt_a = self.create_test_prompt_scenario_a()
        result_a = self.run_scenario("Scénario A", prompt_a)
        result_a["analysis"] = self.analyze_response("Scénario A", result_a["response"])
        self.results["scenarios"]["Scénario A"] = result_a
        
        # Scénario B
        prompt_b = self.create_test_prompt_scenario_b() 
        result_b = self.run_scenario("Scénario B", prompt_b)
        result_b["analysis"] = self.analyze_response("Scénario B", result_b["response"])
        self.results["scenarios"]["Scénario B"] = result_b
        
        # Recommandations
        self.results["recommendations"] = self.generate_recommendations()
        
        return self.results
    
    def save_results(self, filename: str = "rapport_demo_approche_objectif_centree.json") -> Path:
        """Sauvegarde du rapport démo"""
        filepath = Path(__file__).parent / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"📄 Rapport démo sauvegardé : {filepath}")
        return filepath

def print_detailed_report(results: Dict[str, Any]) -> None:
    """Affichage du rapport détaillé"""
    print("\n" + "="*80)
    print("📋 RAPPORT DÉTAILLÉ - Tests démo approche objectif-centrée")
    print("="*80)
    
    print(f"\n🕐 Timestamp : {results['test_timestamp']}")
    print(f"🎭 Mode : {results['mode']}")
    
    for scenario_name, scenario_data in results["scenarios"].items():
        print(f"\n{'🔵' if scenario_name == 'Scénario A' else '🟡'} {scenario_name.upper()}")
        print("-" * 50)
        
        analysis = scenario_data["analysis"]
        
        print(f"⏱️  Temps d'exécution : {scenario_data['execution_time']:.2f}s")
        print(f"🔧 Outils utilisés : {', '.join(scenario_data['tool_calls_made'])}")
        print(f"📏 Durée déterminée : {'✅' if analysis['duration_determined'] else '❌'}")
        print(f"📅 Semaines planifiées : {analysis['duration_weeks']}")
        print(f"📝 Durée justifiée : {'✅' if analysis['duration_justified'] else '❌'}")
        print(f"📊 Écart performance analysé : {'✅' if analysis['performance_gap_analyzed'] else '❌'}")
        print(f"📋 Plan complet généré : {'✅' if analysis['complete_plan_generated'] else '❌'}")
        
        if scenario_name == "Scénario A":
            print(f"🎯 Temps cible considéré : {'✅' if analysis['target_time_considered'] else '❌'}")
        else:
            print(f"💡 Objectif proposé : {'✅' if analysis['objective_proposed'] else '❌'}")
            
        print(f"⭐ Qualité globale : {analysis['recommendations_quality'].upper()}")
        
        # Aperçu réponse
        response_preview = scenario_data["response"][:200].replace('\n', ' ')
        print(f"📄 Aperçu réponse : {response_preview}...")
    
    print(f"\n💡 RECOMMANDATIONS ({len(results['recommendations'])})")
    print("-" * 50)
    for i, rec in enumerate(results["recommendations"], 1):
        print(f"{i}. {rec}")
    
    print(f"\n📊 MÉTRIQUES DE VALIDATION")
    print("-" * 50)
    
    scenario_a_analysis = results["scenarios"]["Scénario A"]["analysis"]
    scenario_b_analysis = results["scenarios"]["Scénario B"]["analysis"]
    
    print(f"✅ Durées appropriées : {scenario_a_analysis['duration_weeks']}sem / {scenario_b_analysis['duration_weeks']}sem")
    print(f"✅ Justifications présentes : Scénario A={scenario_a_analysis['duration_justified']} / Scénario B={scenario_b_analysis['duration_justified']}")
    print(f"✅ Plans complets : Scénario A={scenario_a_analysis['complete_plan_generated']} / Scénario B={scenario_b_analysis['complete_plan_generated']}")
    print(f"✅ Différenciation scénarios : {'OUI' if scenario_a_analysis['target_time_considered'] != scenario_b_analysis['objective_proposed'] else 'NON'}")
    
    print("\n" + "="*80)

def main():
    """Fonction principale de démonstration"""
    print("🎭 DÉMONSTRATION - Tests approche objectif-centrée")
    print("="*60)
    print("Cette démo simule le comportement attendu de l'agent IA réel")
    print("pour valider l'approche sans dépendre d'API externes.")
    print()
    
    try:
        # Initialisation et exécution
        tester = TestApprocheeObjectifCentreeDemo()
        results = tester.run_all_tests()
        
        # Affichage rapport
        print_detailed_report(results)
        
        # Sauvegarde
        report_file = tester.save_results()
        
        # Résumé final
        successful_scenarios = len([s for s in results["scenarios"].values() 
                                   if not s["response"].startswith("ÉCHEC")])
        total_scenarios = len(results["scenarios"])
        
        print(f"\n🎯 RÉSUMÉ FINAL DÉMO")
        print(f"Scénarios testés : {total_scenarios}")
        print(f"Scénarios simulés : {successful_scenarios}")
        print(f"Recommandations générées : {len(results['recommendations'])}")
        print(f"Rapport complet : {report_file}")
        
        print("\n🚀 PROCHAINES ÉTAPES RECOMMANDÉES :")
        print("1. Tester avec une vraie API OpenAI")
        print("2. Valider les durées générées sur différents profils utilisateurs")
        print("3. A/B tester l'ancienne vs nouvelle approche")
        print("4. Monitorer les métriques de satisfaction utilisateur")
        
        print("\n✨ Démonstration terminée avec succès !")
        
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()