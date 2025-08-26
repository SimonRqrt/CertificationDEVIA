"""
Script de test RÉEL pour valider l'approche "objectif-centrée" 
avec la vraie API OpenAI

Version simplifiée qui charge les variables d'environnement et teste
l'agent réel avec les nouveaux paramètres.
"""

import sys
import os
import json
import time
import asyncio
from datetime import datetime
from pathlib import Path

# Chargement explicit des variables d'environnement
from dotenv import load_dotenv
load_dotenv()

# Vérification de la clé API
if not os.getenv('OPENAI_API_KEY'):
    print("❌ Variable d'environnement OPENAI_API_KEY manquante")
    print("Vérifiez votre fichier .env")
    sys.exit(1)

# Ajouter le chemin du projet
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(project_root)

try:
    from E3_model_IA.scripts.advanced_agent import get_coaching_graph
    from langchain_core.messages import HumanMessage
    print("✅ Imports réussis")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    print("Tentative avec les dépendances disponibles...")
    sys.exit(1)

class TestApprocheeObjectifCentreeReel:
    """Tests réels pour valider l'approche objectif-centrée"""
    
    def __init__(self):
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "mode": "PRODUCTION_API",
            "scenarios": {},
            "analysis": {},
            "recommendations": []
        }
        self.graph = None
        self.user_id = 1
    
    async def setup_agent(self):
        """Initialisation de l'agent IA réel"""
        print("🔧 Initialisation de l'agent IA avec API OpenAI...")
        try:
            self.graph = await get_coaching_graph()
            print("✅ Agent IA initialisé avec succès")
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation : {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_test_prompt_scenario_a(self):
        """Scénario A : Test avec target_time="45:00" """
        return f"""
Je suis l'utilisateur {self.user_id}. Je veux tester la nouvelle approche "objectif-centrée".

PARAMÈTRES DE TEST :
- Objectif : Courir un 10k en 45:00 (quarante-cinq minutes)
- Niveau : intermédiaire
- Sessions par semaine : 3
- target_time : "45:00"
- duration_weeks : 0 (IMPORTANT: laisse l'agent déterminer automatiquement)

INSTRUCTIONS SPÉCIFIQUES POUR L'AGENT :
1. Utilise OBLIGATOIREMENT l'outil get_user_metrics_from_db en premier
2. Recherche des connaissances avec get_training_knowledge 
3. DÉTERMINE AUTOMATIQUEMENT la durée optimale du plan (PAS seulement 2 semaines !)
4. JUSTIFIE ton choix de durée en fonction de l'écart performance actuelle vs objectif 45:00
5. Génère un plan COMPLET sur TOUTE la durée déterminée (minimum 6 semaines)

Mode : plan_generator
L'objectif est de valider que l'agent choisit intelligemment la durée basée sur l'objectif.
"""
    
    def create_test_prompt_scenario_b(self):
        """Scénario B : Test sans target_time (objectif général)"""
        return f"""
Je suis l'utilisateur {self.user_id}. Je veux tester l'approche "objectif-centrée" sans temps cible.

PARAMÈTRES DE TEST :
- Objectif : Améliorer ma performance sur 10k (pas de temps spécifique)  
- Niveau : intermédiaire
- Sessions par semaine : 3
- target_time : (aucun)
- duration_weeks : 0 (IMPORTANT: laisse l'agent déterminer automatiquement)

INSTRUCTIONS SPÉCIFIQUES POUR L'AGENT :
1. Utilise OBLIGATOIREMENT l'outil get_user_metrics_from_db en premier
2. Recherche des connaissances avec get_training_knowledge
3. PROPOSE un objectif de temps réaliste basé sur mes données actuelles
4. DÉTERMINE AUTOMATIQUEMENT une durée optimale pour le développement complet
5. JUSTIFIE le choix de durée pour exploration du potentiel
6. Génère un plan COMPLET sur TOUTE la durée déterminée

Mode : plan_generator
Test de la capacité de l'agent à proposer durée ET objectif de façon autonome.
"""
    
    async def run_scenario(self, scenario_name, prompt, timeout=120):
        """Exécution d'un scénario réel avec timeout"""
        print(f"\n{'='*60}")
        print(f"🧪 EXÉCUTION RÉELLE - {scenario_name}")
        print(f"{'='*60}")
        
        scenario_result = {
            "prompt": prompt,
            "response": "",
            "execution_time": 0,
            "tool_calls_detected": [],
            "errors": [],
            "timeout_reached": False
        }
        
        try:
            start_time = time.time()
            
            print(f"📤 Envoi du prompt à l'agent OpenAI...")
            print(f"📝 Prompt (aperçu): {prompt[:150]}...")
            
            # Configuration avec thread unique
            config = {
                "configurable": {
                    "thread_id": f"test-real-{scenario_name.lower().replace(' ', '-')}-{int(time.time())}"
                }
            }
            
            response_parts = []
            tool_calls_detected = []
            
            # Stream avec timeout
            try:
                async with asyncio.timeout(timeout):
                    async for event in self.graph.astream(
                        {"messages": [HumanMessage(content=prompt)], "mode": "plan_generator"},
                        config=config
                    ):
                        for node_name, step in event.items():
                            if "messages" in step and step["messages"]:
                                message = step["messages"][-1]
                                
                                # Détection des appels d'outils
                                if hasattr(message, 'tool_calls') and message.tool_calls:
                                    for tool_call in message.tool_calls:
                                        tool_name = tool_call.get('name', 'unknown')
                                        tool_calls_detected.append(tool_name)
                                        print(f"🔧 Outil détecté : {tool_name}")
                                
                                # Collecte des réponses
                                if hasattr(message, 'content') and message.content:
                                    content = str(message.content)
                                    response_parts.append(content)
                                    print(f"📥 Réponse partielle ({len(content)} caractères)")
                                    
            except asyncio.TimeoutError:
                scenario_result["timeout_reached"] = True
                print(f"⏰ Timeout atteint après {timeout}s")
            
            execution_time = time.time() - start_time
            full_response = '\n'.join(response_parts).strip()
            
            if not full_response:
                raise Exception("Réponse vide de l'agent après timeout/erreur")
            
            scenario_result.update({
                "response": full_response,
                "execution_time": execution_time,
                "tool_calls_detected": list(set(tool_calls_detected))  # Déduplication
            })
            
            print(f"✅ Scénario {scenario_name} exécuté en {execution_time:.2f}s")
            print(f"📊 Outils utilisés : {scenario_result['tool_calls_detected']}")
            print(f"📏 Réponse : {len(full_response)} caractères")
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Erreur: {str(e)}"
            scenario_result["errors"].append(error_msg)
            scenario_result["execution_time"] = execution_time
            print(f"❌ Scénario {scenario_name} échoué après {execution_time:.2f}s: {error_msg}")
        
        return scenario_result
    
    def analyze_response(self, scenario_name, response, tool_calls):
        """Analyse approfondie de la réponse réelle"""
        analysis = {
            "duration_determined": False,
            "duration_weeks": 0,
            "duration_justified": False,
            "performance_gap_analyzed": False,
            "complete_plan_generated": False,
            "tools_used_correctly": False,
            "target_time_addressed": False,
            "objective_proposed": False,
            "quality_score": 0
        }
        
        response_lower = response.lower()
        
        # 1. Analyse des outils utilisés
        expected_tools = ["get_user_metrics_from_db", "get_training_knowledge"]
        tools_used = len([t for t in expected_tools if t in tool_calls])
        analysis["tools_used_correctly"] = tools_used >= 1
        
        # 2. Détection durée déterminée
        duration_keywords = [
            "durée déterminée", "semaines", "plan de", "programme de", 
            "durée optimale", "durée recommandée"
        ]
        analysis["duration_determined"] = any(kw in response_lower for kw in duration_keywords)
        
        # 3. Extraction nombre de semaines
        import re
        week_patterns = [
            r'(\d+)\s*semaines?',
            r'plan de\s*(\d+)',
            r'programme de\s*(\d+)',  
            r'durée.*?(\d+).*?semaines?',
            r'##\s*semaine\s*(\d+)'
        ]
        
        week_numbers = []
        for pattern in week_patterns:
            matches = re.findall(pattern, response_lower)
            week_numbers.extend([int(m) for m in matches if int(m) <= 20])  # Semaines réalistes
        
        if week_numbers:
            analysis["duration_weeks"] = max(week_numbers)
        
        # 4. Justification présente
        justification_keywords = [
            "justification", "parce que", "car", "en raison", "afin de",
            "nécessite", "permet", "écart", "objectif", "progression"
        ]
        analysis["duration_justified"] = any(kw in response_lower for kw in justification_keywords)
        
        # 5. Analyse écart performance
        gap_keywords = [
            "écart", "différence", "amélioration", "progression", "actuel",
            "performance", "vitesse", "temps", "objectif"
        ]
        analysis["performance_gap_analyzed"] = any(kw in response_lower for kw in gap_keywords)
        
        # 6. Plan complet généré
        plan_keywords = [
            "semaine 1", "semaine 2", "tableau", "jour", "séance",
            "lundi", "mardi", "entraînement", "plan hebdomadaire"
        ]
        plan_count = sum(1 for kw in plan_keywords if kw in response_lower)
        analysis["complete_plan_generated"] = plan_count >= 3
        
        # 7. Scénario A : target_time pris en compte
        if scenario_name == "Scénario A":
            time_keywords = ["45:00", "quarante-cinq", "45 minutes", "temps objectif", "temps cible"]
            analysis["target_time_addressed"] = any(kw in response_lower for kw in time_keywords)
        
        # 8. Scénario B : objectif proposé
        if scenario_name == "Scénario B":
            proposal_keywords = [
                "objectif proposé", "objectif recommandé", "temps suggéré",
                "potentiel", "amélioration de", "passer de"
            ]
            analysis["objective_proposed"] = any(kw in response_lower for kw in proposal_keywords)
        
        # 9. Score qualité
        score = 0
        if analysis["tools_used_correctly"]: score += 2
        if analysis["duration_determined"]: score += 2  
        if analysis["duration_weeks"] >= 6: score += 2
        if analysis["duration_justified"]: score += 1
        if analysis["performance_gap_analyzed"]: score += 1
        if analysis["complete_plan_generated"]: score += 2
        
        analysis["quality_score"] = score
        return analysis
    
    def generate_recommendations(self):
        """Recommandations basées sur les tests réels"""
        recommendations = []
        
        scenario_a = self.results["scenarios"].get("Scénario A", {})
        scenario_b = self.results["scenarios"].get("Scénario B", {}) 
        
        analysis_a = scenario_a.get("analysis", {})
        analysis_b = scenario_b.get("analysis", {})
        
        # Évaluation globale
        if analysis_a.get("quality_score", 0) >= 8 and analysis_b.get("quality_score", 0) >= 8:
            recommendations.append(
                "🟢 SUCCÈS TOTAL: L'approche objectif-centrée fonctionne parfaitement "
                "avec l'API OpenAI réelle. Déploiement recommandé."
            )
        elif analysis_a.get("quality_score", 0) >= 6 or analysis_b.get("quality_score", 0) >= 6:
            recommendations.append(
                "🟡 SUCCÈS PARTIEL: L'approche fonctionne mais nécessite des ajustements "
                "dans les prompts système avant déploiement."
            )
        else:
            recommendations.append(
                "🔴 ÉCHEC: L'approche nécessite des modifications importantes "
                "avant d'être utilisable en production."
            )
        
        # Recommandations spécifiques
        duration_a = analysis_a.get("duration_weeks", 0)
        duration_b = analysis_b.get("duration_weeks", 0)
        
        if duration_a >= 6 and duration_b >= 6:
            recommendations.append(f"✅ Durées appropriées générées: {duration_a} et {duration_b} semaines")
        else:
            recommendations.append(f"❌ Durées insuffisantes: {duration_a} et {duration_b} semaines")
        
        if analysis_a.get("tools_used_correctly") and analysis_b.get("tools_used_correctly"):
            recommendations.append("✅ Outils utilisés correctement dans les deux scénarios")
        else:
            recommendations.append("❌ Problème d'utilisation des outils détecté")
        
        return recommendations
    
    async def run_all_tests(self):
        """Exécution complète des tests réels"""
        print("🚀 DÉBUT DES TESTS RÉELS - Approche objectif-centrée")
        print("="*70)
        print("🌐 Tests avec API OpenAI authentique")
        
        # Initialisation
        if not await self.setup_agent():
            return self.results
        
        # Scénario A - Avec target_time
        prompt_a = self.create_test_prompt_scenario_a()
        result_a = await self.run_scenario("Scénario A", prompt_a)
        result_a["analysis"] = self.analyze_response("Scénario A", result_a["response"], result_a["tool_calls_detected"])
        self.results["scenarios"]["Scénario A"] = result_a
        
        # Scénario B - Sans target_time
        prompt_b = self.create_test_prompt_scenario_b()
        result_b = await self.run_scenario("Scénario B", prompt_b)
        result_b["analysis"] = self.analyze_response("Scénario B", result_b["response"], result_b["tool_calls_detected"]) 
        self.results["scenarios"]["Scénario B"] = result_b
        
        # Recommandations
        self.results["recommendations"] = self.generate_recommendations()
        
        return self.results
    
    def save_results(self, filename="rapport_reel_approche_objectif_centree.json"):
        """Sauvegarde des résultats réels"""
        filepath = Path(__file__).parent / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        print(f"📄 Rapport réel sauvegardé : {filepath}")
        return filepath

def print_real_report(results):
    """Affichage du rapport des tests réels"""
    print("\n" + "="*80)
    print("📋 RAPPORT TESTS RÉELS - Approche objectif-centrée")  
    print("="*80)
    
    print(f"🕐 Timestamp : {results['test_timestamp']}")
    print(f"🌐 Mode : {results['mode']}")
    
    for scenario_name, scenario_data in results["scenarios"].items():
        print(f"\n{'🔵' if scenario_name == 'Scénario A' else '🟡'} {scenario_name.upper()}")
        print("-" * 50)
        
        analysis = scenario_data.get("analysis", {})
        
        print(f"⏱️  Temps d'exécution : {scenario_data.get('execution_time', 0):.2f}s")
        print(f"🔧 Outils détectés : {scenario_data.get('tool_calls_detected', [])}")
        print(f"📏 Durée déterminée : {'✅' if analysis.get('duration_determined') else '❌'}")
        print(f"📅 Semaines planifiées : {analysis.get('duration_weeks', 0)}")
        print(f"📝 Durée justifiée : {'✅' if analysis.get('duration_justified') else '❌'}")
        print(f"📊 Écart analysé : {'✅' if analysis.get('performance_gap_analyzed') else '❌'}")
        print(f"📋 Plan complet : {'✅' if analysis.get('complete_plan_generated') else '❌'}")
        print(f"🎯 Score qualité : {analysis.get('quality_score', 0)}/10")
        
        if scenario_data.get("errors"):
            print(f"❌ Erreurs : {len(scenario_data['errors'])}")
            for error in scenario_data["errors"][:2]:  # Limite affichage erreurs
                print(f"   • {error}")
    
    print(f"\n💡 RECOMMANDATIONS FINALES ({len(results.get('recommendations', []))})")
    print("-" * 50)
    for i, rec in enumerate(results.get("recommendations", []), 1):
        print(f"{i}. {rec}")
    
    print("\n" + "="*80)

async def main():
    """Fonction principale des tests réels"""
    print("🔑 Vérification de l'environnement...")
    print(f"✅ OPENAI_API_KEY présente : {bool(os.getenv('OPENAI_API_KEY'))}")
    
    tester = TestApprocheeObjectifCentreeReel()
    
    try:
        # Exécution
        results = await tester.run_all_tests()
        
        # Rapport
        print_real_report(results)
        
        # Sauvegarde
        report_file = tester.save_results()
        
        # Résumé
        successful_scenarios = len([s for s in results["scenarios"].values() 
                                   if not s.get("errors") and s.get("response")])
        total_scenarios = len(results["scenarios"])
        
        print(f"\n🎯 RÉSUMÉ FINAL")
        print(f"Scénarios testés : {total_scenarios}")
        print(f"Scénarios réussis : {successful_scenarios}")
        print(f"Recommandations : {len(results['recommendations'])}")
        print(f"Rapport : {report_file}")
        
        if successful_scenarios == total_scenarios:
            print("🎉 Tous les tests réels ont réussi !")
        else:
            print("⚠️  Certains tests ont échoué - voir rapport")
        
    except Exception as e:
        print(f"❌ Erreur critique : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())