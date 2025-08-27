"""
Script de test pour valider l'approche "objectif-centrée" 
de la génération de plans d'entraînement

Contexte : 
L'agent IA détermine maintenant automatiquement la durée optimale 
en fonction de l'objectif de l'utilisateur, plutôt que de laisser 
l'utilisateur choisir une durée arbitraire.

Tests :
1. Scénario A : Avec target_time="45:00" (objectif de temps pour 10k)
2. Scénario B : Sans target_time="" (objectif général pour 10k)
"""

import sys
import os
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path

# Ajouter le chemin du projet
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(project_root)

try:
    from E3_model_IA.scripts.advanced_agent import get_coaching_graph
    from langchain_core.messages import HumanMessage
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Assurez-vous que les dépendances sont installées et que les chemins sont corrects")
    sys.exit(1)

class TestApprocheeObjectifCentree:
    """Tests pour valider l'approche objectif-centrée"""
    
    def setup_method(self):
        """Initialisation commune à tous les tests"""
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "scenarios": {},
            "analysis": {},
            "recommendations": []
        }
    
    async def setup_agent(self):
        """Initialisation de l'agent IA"""
        print("🔧 Initialisation de l'agent IA...")
        try:
            self.graph = await get_coaching_graph()
            self.user_id = 1  # Utilisateur de test
            print("✅ Agent IA initialisé avec succès")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation : {e}")
            return False
    
    def create_test_prompt_scenario_a(self):
        """Scénario A : Avec target_time pour objectif de temps"""
        return f"""
Je suis l'utilisateur {self.user_id}. Je souhaite générer un plan d'entraînement avec ces paramètres :

OBJECTIF : Courir un 10k en 45:00 (quarante-cinq minutes)
NIVEAU : intermédiaire 
SESSIONS : 3 par semaine
DURÉE : 0 semaines (laisse l'agent déterminer la durée optimale)
TARGET_TIME : 45:00

Instructions pour l'agent :
1. Analyse d'abord mes données utilisateur avec get_user_metrics_from_db
2. Recherche les connaissances pertinentes avec get_training_knowledge  
3. Détermine automatiquement la durée optimale du plan (PAS seulement 2 semaines)
4. Justifie ton choix de durée en fonction de l'écart entre ma performance actuelle et l'objectif
5. Génère un plan complet couvrant TOUTE la durée choisie

L'objectif est d'améliorer ma vitesse pour atteindre 45:00 sur 10k. 
Génère un plan d'entraînement personnalisé sur plusieurs semaines.
"""
    
    def create_test_prompt_scenario_b(self):
        """Scénario B : Sans target_time pour objectif général"""
        return f"""
Je suis l'utilisateur {self.user_id}. Je souhaite générer un plan d'entraînement avec ces paramètres :

OBJECTIF : Améliorer ma performance sur 10k (objectif général)
NIVEAU : intermédiaire
SESSIONS : 3 par semaine  
DURÉE : 0 semaines (laisse l'agent déterminer la durée optimale)
TARGET_TIME : (aucun temps spécifique)

Instructions pour l'agent :
1. Analyse d'abord mes données utilisateur avec get_user_metrics_from_db
2. Recherche les connaissances pertinentes avec get_training_knowledge
3. Détermine automatiquement la durée optimale du plan basée sur mon niveau
4. Propose un objectif de temps réaliste basé sur mes performances actuelles
5. Génère un plan complet couvrant TOUTE la durée choisie

L'objectif est d'améliorer ma performance générale sur 10k sans temps cible spécifique.
Génère un plan d'entraînement personnalisé sur plusieurs semaines.
"""
    
    async def run_scenario(self, scenario_name, prompt, max_retries=2):
        """Exécution d'un scénario de test avec gestion des erreurs"""
        print(f"\n{'='*60}")
        print(f"🧪 EXÉCUTION - {scenario_name}")
        print(f"{'='*60}")
        
        scenario_result = {
            "prompt": prompt,
            "response": "",
            "analysis": {},
            "execution_time": 0,
            "errors": [],
            "retries": 0
        }
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                
                print(f"📤 Envoi du prompt à l'agent (tentative {attempt + 1})...")
                print(f"📝 Prompt : {prompt[:200]}...")
                
                # Configuration de la conversation
                config = {
                    "configurable": {
                        "thread_id": f"test-objective-{scenario_name.lower()}-{int(time.time())}"
                    }
                }
                
                response_parts = []
                async for event in self.graph.astream(
                    {"messages": [HumanMessage(content=prompt)], "mode": "plan_generator"},
                    config=config
                ):
                    for step in event.values():
                        if "messages" in step and step["messages"]:
                            message = step["messages"][-1]
                            if hasattr(message, 'content') and message.content:
                                response_parts.append(str(message.content))
                                print(f"📥 Réponse partielle: {str(message.content)[:100]}...")
                
                execution_time = time.time() - start_time
                full_response = '\n'.join(response_parts)
                
                if not full_response.strip():
                    raise Exception("Réponse vide de l'agent")
                
                scenario_result.update({
                    "response": full_response,
                    "execution_time": execution_time,
                    "retries": attempt
                })
                
                print(f"✅ Scénario {scenario_name} exécuté avec succès en {execution_time:.2f}s")
                break
                
            except Exception as e:
                error_msg = f"Tentative {attempt + 1} échouée: {str(e)}"
                scenario_result["errors"].append(error_msg)
                print(f"❌ {error_msg}")
                
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Backoff exponentiel
                    print(f"⏳ Attente {wait_time}s avant nouvelle tentative...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"❌ Scénario {scenario_name} échoué après {max_retries + 1} tentatives")
                    scenario_result["response"] = f"ÉCHEC: {'; '.join(scenario_result['errors'])}"
        
        return scenario_result
    
    def analyze_response(self, scenario_name, response):
        """Analyse de la réponse pour validation"""
        analysis = {
            "duration_determined": False,
            "duration_weeks": 0,
            "duration_justified": False,
            "performance_gap_analyzed": False,
            "complete_plan_generated": False,
            "week_count": 0,
            "target_time_considered": False,
            "recommendations_quality": "unknown"
        }
        
        response_lower = response.lower()
        
        # 1. Vérification que la durée est déterminée
        duration_indicators = ["semaine", "weeks", "durée", "plan de", "programme de"]
        for indicator in duration_indicators:
            if indicator in response_lower:
                analysis["duration_determined"] = True
                break
        
        # 2. Extraction du nombre de semaines
        import re
        week_patterns = [
            r'(\d+)\s*semaine',
            r'semaine\s*(\d+)',
            r'plan de\s*(\d+)',
            r'programme de\s*(\d+)',
            r'##\s*semaine\s*(\d+)'
        ]
        
        week_numbers = []
        for pattern in week_patterns:
            matches = re.findall(pattern, response_lower)
            week_numbers.extend([int(m) for m in matches])
        
        if week_numbers:
            analysis["duration_weeks"] = max(week_numbers)
            analysis["week_count"] = len(set(week_numbers))
        
        # 3. Vérification que la durée est justifiée
        justification_indicators = [
            "parce que", "car", "en raison", "afin de", "pour atteindre",
            "objectif", "performance", "progression", "amélioration"
        ]
        analysis["duration_justified"] = any(ind in response_lower for ind in justification_indicators)
        
        # 4. Analyse de l'écart de performance
        gap_indicators = [
            "écart", "différence", "améliorer", "progression", "actuel", 
            "objectif", "performance", "temps", "vitesse"
        ]
        analysis["performance_gap_analyzed"] = any(ind in response_lower for ind in gap_indicators)
        
        # 5. Vérification du plan complet
        plan_indicators = ["tableau", "jour", "lundi", "mardi", "séance", "entraînement"]
        analysis["complete_plan_generated"] = any(ind in response_lower for ind in plan_indicators)
        
        # 6. Vérification de la prise en compte du target_time
        time_indicators = ["45:00", "quarante-cinq", "45 minutes", "temps objectif"]
        analysis["target_time_considered"] = any(ind in response_lower for ind in time_indicators)
        
        # 7. Qualité des recommandations
        if analysis["duration_weeks"] >= 6 and analysis["complete_plan_generated"]:
            analysis["recommendations_quality"] = "excellent"
        elif analysis["duration_weeks"] >= 4 and analysis["duration_justified"]:
            analysis["recommendations_quality"] = "good"
        elif analysis["duration_determined"]:
            analysis["recommendations_quality"] = "basic"
        else:
            analysis["recommendations_quality"] = "poor"
        
        return analysis
    
    def generate_recommendations(self):
        """Génération des recommandations d'amélioration"""
        recommendations = []
        
        # Analyse comparative des scénarios
        scenario_a = self.results["scenarios"].get("Scénario A", {})
        scenario_b = self.results["scenarios"].get("Scénario B", {})
        
        analysis_a = scenario_a.get("analysis", {})
        analysis_b = scenario_b.get("analysis", {})
        
        # Recommandations basées sur la durée
        if analysis_a.get("duration_weeks", 0) <= 2:
            recommendations.append(
                "🔴 CRITIQUE: L'agent génère des plans trop courts (≤2 semaines). "
                "Modifier le prompt pour insister sur des plans de 6-12 semaines minimum."
            )
        elif analysis_a.get("duration_weeks", 0) < 6:
            recommendations.append(
                "🟡 AMÉLIORATION: L'agent pourrait générer des plans plus longs "
                "pour permettre une progression graduelle et durable."
            )
        else:
            recommendations.append(
                "🟢 EXCELLENT: L'agent génère des plans de durée appropriée "
                f"({analysis_a.get('duration_weeks', 0)} semaines)."
            )
        
        # Recommandations sur la justification
        if not analysis_a.get("duration_justified"):
            recommendations.append(
                "🔴 MANQUANT: L'agent ne justifie pas suffisamment son choix de durée. "
                "Ajouter une consigne explicite pour expliquer la logique temporelle."
            )
        
        # Recommandations sur l'analyse des performances
        if not analysis_a.get("performance_gap_analyzed"):
            recommendations.append(
                "🟡 AMÉLIORATION: L'agent devrait mieux analyser l'écart entre "
                "performance actuelle et objectif pour adapter la durée."
            )
        
        # Comparaison entre scénarios
        if analysis_a.get("target_time_considered") and not analysis_b.get("target_time_considered"):
            recommendations.append(
                "🟢 POSITIF: L'agent adapte bien sa réponse selon la présence d'un temps cible."
            )
        
        return recommendations
    
    async def run_all_tests(self):
        """Exécution de tous les tests"""
        print("🚀 DÉBUT DES TESTS - Approche objectif-centrée")
        print("="*70)
        
        # Initialisation
        if not await self.setup_agent():
            return self.results
        
        # Scénario A : Avec target_time
        prompt_a = self.create_test_prompt_scenario_a()
        result_a = await self.run_scenario("Scénario A", prompt_a)
        result_a["analysis"] = self.analyze_response("Scénario A", result_a["response"])
        self.results["scenarios"]["Scénario A"] = result_a
        
        # Scénario B : Sans target_time  
        prompt_b = self.create_test_prompt_scenario_b()
        result_b = await self.run_scenario("Scénario B", prompt_b)
        result_b["analysis"] = self.analyze_response("Scénario B", result_b["response"])
        self.results["scenarios"]["Scénario B"] = result_b
        
        # Génération des recommandations
        self.results["recommendations"] = self.generate_recommendations()
        
        return self.results
    
    def save_results(self, filename="rapport_approche_objectif_centree.json"):
        """Sauvegarde des résultats"""
        filepath = Path(__file__).parent / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"📄 Rapport sauvegardé : {filepath}")
        return filepath

def print_detailed_report(results):
    """Affichage détaillé du rapport"""
    print("\n" + "="*80)
    print("📋 RAPPORT DÉTAILLÉ - Tests approche objectif-centrée")
    print("="*80)
    
    print(f"\n🕐 Timestamp : {results['test_timestamp']}")
    
    for scenario_name, scenario_data in results["scenarios"].items():
        print(f"\n{'🔵' if scenario_name == 'Scénario A' else '🟡'} {scenario_name.upper()}")
        print("-" * 50)
        
        analysis = scenario_data["analysis"]
        
        print(f"⏱️  Temps d'exécution : {scenario_data['execution_time']:.2f}s")
        print(f"🔄 Tentatives : {scenario_data['retries'] + 1}")
        print(f"📏 Durée déterminée : {'✅' if analysis['duration_determined'] else '❌'}")
        print(f"📅 Semaines planifiées : {analysis['duration_weeks']}")
        print(f"📝 Durée justifiée : {'✅' if analysis['duration_justified'] else '❌'}")
        print(f"📊 Écart performance analysé : {'✅' if analysis['performance_gap_analyzed'] else '❌'}")
        print(f"📋 Plan complet généré : {'✅' if analysis['complete_plan_generated'] else '❌'}")
        print(f"🎯 Temps cible considéré : {'✅' if analysis['target_time_considered'] else '❌'}")
        print(f"⭐ Qualité : {analysis['recommendations_quality']}")
        
        if scenario_data.get("errors"):
            print(f"❌ Erreurs : {len(scenario_data['errors'])}")
            for error in scenario_data["errors"]:
                print(f"   • {error}")
        
        # Aperçu de la réponse
        response_preview = scenario_data["response"][:300].replace('\n', ' ')
        print(f"📄 Aperçu réponse : {response_preview}...")
    
    print(f"\n💡 RECOMMANDATIONS ({len(results['recommendations'])})")
    print("-" * 50)
    for i, rec in enumerate(results["recommendations"], 1):
        print(f"{i}. {rec}")
    
    print("\n" + "="*80)

async def main():
    """Fonction principale d'exécution des tests"""
    tester = TestApprocheeObjectifCentree()
    
    try:
        # Exécution des tests
        results = await tester.run_all_tests()
        
        # Affichage du rapport détaillé
        print_detailed_report(results)
        
        # Sauvegarde
        report_file = tester.save_results()
        
        # Résumé final
        total_scenarios = len(results["scenarios"])
        successful_scenarios = sum(
            1 for s in results["scenarios"].values() 
            if not s["response"].startswith("ÉCHEC")
        )
        
        print(f"\n🎯 RÉSUMÉ FINAL")
        print(f"Scénarios testés : {total_scenarios}")
        print(f"Scénarios réussis : {successful_scenarios}")
        print(f"Recommandations : {len(results['recommendations'])}")
        print(f"Rapport complet : {report_file}")
        
        if successful_scenarios == total_scenarios:
            print("🎉 Tous les tests ont réussi !")
        else:
            print("⚠️  Certains tests ont échoué, voir le rapport pour détails.")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution des tests : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Vérification de l'environnement
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Variable d'environnement OPENAI_API_KEY manquante")
        print("Ajoutez votre clé API OpenAI dans le fichier .env")
        sys.exit(1)
    
    # Lancement des tests
    asyncio.run(main())