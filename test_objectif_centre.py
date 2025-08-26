#!/usr/bin/env python3
"""
Script de test pour l'approche "objectif-centrée" de génération de plans d'entraînement.

Ce script teste si l'agent IA détermine automatiquement une durée optimale en fonction de l'objectif
plutôt que de laisser l'utilisateur choisir une durée arbitraire.

Deux scénarios sont testés :
- Scénario A : Avec target_time="45:00" (objectif de temps spécifique)
- Scénario B : Sans target_time (objectif général)

L'agent doit analyser l'écart entre la performance actuelle et l'objectif pour déterminer
une durée de préparation appropriée (pas seulement 2 semaines).
"""

import asyncio
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Ajouter le chemin du projet pour les imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Charger les variables d'environnement
load_dotenv(project_root / ".env")

from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from langchain_core.messages import HumanMessage

# Import de l'agent
from E3_model_IA.scripts.advanced_agent import get_coaching_graph

console = Console()

class ObjectiveCenteredTester:
    """Classe pour tester l'approche objectif-centrée"""
    
    def __init__(self):
        self.results = []
        self.test_start_time = datetime.now()
        
    async def initialize_agent(self):
        """Initialiser l'agent de coaching"""
        rprint("[yellow]📋 Initialisation de l'agent de coaching...[/yellow]")
        self.graph = await get_coaching_graph()
        rprint("[green]✅ Agent initialisé avec succès[/green]")
    
    def create_prompt(self, scenario_name, target_time=None, duration_weeks=0):
        """Créer le prompt selon l'approche objectif-centrée"""
        target_time_info = ""
        if target_time:
            target_time_info = f"- TEMPS OBJECTIF: {target_time} sur 10k"
        
        duration_instruction = ""
        if duration_weeks > 0:
            duration_instruction = f"- DURÉE IMPOSÉE: {duration_weeks} semaines exactement"
        else:
            duration_instruction = "- DURÉE À DÉTERMINER: Analyse l'écart entre niveau actuel et objectif pour déterminer la durée optimale (4-20 semaines)"
        
        prompt = f"""Je suis l'utilisateur 1.

ANALYSE ET GÉNÈRE un plan d'entraînement intelligent:
- Objectif: 10k  
- Niveau déclaré: intermédiaire
- 3 séances/semaine
{target_time_info}
{duration_instruction}

ÉTAPES OBLIGATOIRES:
1. UTILISE get_user_metrics_from_db(1) pour analyser le niveau réel
2. ÉVALUE l'écart entre performance actuelle et objectif cible
3. DÉTERMINE la durée optimale de préparation (justifie ton choix)
4. GÉNÈRE le plan COMPLET sur cette durée avec tableaux markdown pour CHAQUE semaine

IMPORTANT: Si objectif de temps donné, calcule une progression réaliste. Sinon, utilise durées standards selon l'objectif.

Sois précis, réaliste et justifie tes choix."""

        return prompt
    
    async def run_scenario(self, scenario_name, description, target_time=None, duration_weeks=0):
        """Exécuter un scénario de test"""
        rprint(f"\n[bold cyan]🧪 {scenario_name}: {description}[/bold cyan]")
        rprint("=" * 80)
        
        # Préparer le prompt
        prompt = self.create_prompt(scenario_name, target_time, duration_weeks)
        
        rprint(f"[yellow]📤 Prompt envoyé à l'agent :[/yellow]")
        rprint(Panel(prompt, title="Prompt", border_style="yellow"))
        
        # Paramètres du test
        user_id = 1
        thread_id = f"test-objectif-{scenario_name.lower().replace(' ', '-')}-{int(time.time())}"
        
        rprint(f"[yellow]⚡ Exécution du {scenario_name}...[/yellow]")
        rprint("(Cela peut prendre 30-60 secondes)")
        
        start_time = time.time()
        full_response = ""
        
        try:
            # Configurer le mode plan_generator pour forcer la génération multi-semaines
            initial_state = {
                "messages": [HumanMessage(content=prompt)],
                "mode": "plan_generator"
            }
            
            # Stream de l'exécution
            async for event in self.graph.astream(
                initial_state,
                config={"configurable": {"thread_id": thread_id}}
            ):
                for step in event.values():
                    if "messages" in step and step["messages"]:
                        message = step["messages"][-1]
                        if hasattr(message, 'content') and message.content:
                            if hasattr(message, 'type') and message.type == "ai":
                                full_response += message.content
            
            execution_time = time.time() - start_time
            
            rprint(f"[green]✅ {scenario_name} terminé en {execution_time:.1f}s[/green]")
            
            # Analyser la réponse
            analysis = self.analyze_response(full_response, target_time, duration_weeks)
            
            # Stocker les résultats
            result = {
                "scenario": scenario_name,
                "description": description,
                "target_time": target_time,
                "duration_weeks_input": duration_weeks,
                "prompt": prompt,
                "response": full_response,
                "execution_time": execution_time,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
            self.results.append(result)
            
            # Afficher le résumé
            self.display_scenario_summary(result)
            
            return result
            
        except Exception as e:
            rprint(f"[bold red]❌ Erreur lors du {scenario_name}: {e}[/bold red]")
            import traceback
            traceback.print_exc()
            return None
    
    def analyze_response(self, response, target_time, duration_weeks_input):
        """Analyser la réponse de l'agent"""
        analysis = {
            "response_length": len(response),
            "weeks_found": [],
            "duration_determined": None,
            "justification_found": False,
            "gap_analysis_found": False,
            "complete_plan_found": False,
            "metrics_used": False,
            "target_time_mentioned": False,
            "progression_calculated": False
        }
        
        # Rechercher les semaines numérotées
        for i in range(1, 25):  # Chercher jusqu'à 24 semaines
            week_patterns = [
                f"semaine {i}",
                f"## semaine {i}",
                f"# semaine {i}",
                f"### semaine {i}"
            ]
            for pattern in week_patterns:
                if pattern in response.lower():
                    analysis["weeks_found"].append(i)
                    break
        
        # Déterminer la durée effective
        max_week = max(analysis["weeks_found"]) if analysis["weeks_found"] else 0
        analysis["duration_determined"] = max_week
        
        # Rechercher des justifications de durée
        justification_keywords = [
            "semaines nécessaires",
            "durée optimale",
            "progression progressive",
            "temps de préparation",
            "écart entre",
            "justification",
            "raison de cette durée",
            "choix de la durée"
        ]
        
        for keyword in justification_keywords:
            if keyword.lower() in response.lower():
                analysis["justification_found"] = True
                break
        
        # Rechercher l'analyse de l'écart
        gap_keywords = [
            "écart entre",
            "niveau actuel",
            "objectif cible",
            "performance actuelle",
            "progresser de",
            "amélioration nécessaire"
        ]
        
        for keyword in gap_keywords:
            if keyword.lower() in response.lower():
                analysis["gap_analysis_found"] = True
                break
        
        # Vérifier la structure de plan complet
        plan_indicators = [
            "| Jour" in response and "| Type Séance" in response,
            response.count("##") >= analysis["duration_determined"],  # Un titre par semaine minimum
            "tableau" in response.lower() or "plan" in response.lower()
        ]
        analysis["complete_plan_found"] = any(plan_indicators)
        
        # Vérifier l'utilisation des métriques
        metrics_keywords = [
            "get_user_metrics_from_db",
            "métriques utilisateur",
            "données utilisateur",
            "profil utilisateur",
            "activités récentes"
        ]
        
        for keyword in metrics_keywords:
            if keyword.lower() in response.lower():
                analysis["metrics_used"] = True
                break
        
        # Vérifier la mention du target_time
        if target_time:
            analysis["target_time_mentioned"] = target_time in response or "45:00" in response or "45 min" in response
        
        # Vérifier le calcul de progression
        progression_keywords = [
            "progression",
            "réaliste",
            "objectif atteignable",
            "amélioration graduelle",
            "paliers"
        ]
        
        for keyword in progression_keywords:
            if keyword.lower() in response.lower():
                analysis["progression_calculated"] = True
                break
        
        return analysis
    
    def display_scenario_summary(self, result):
        """Afficher le résumé d'un scénario"""
        analysis = result["analysis"]
        
        # Créer un tableau de résumé
        table = Table(title=f"Résumé - {result['scenario']}")
        table.add_column("Critère", style="cyan")
        table.add_column("Résultat", style="green")
        table.add_column("Statut", justify="center")
        
        # Durée déterminée
        duration_status = "✅" if analysis["duration_determined"] > 2 else "❌"
        table.add_row(
            "Durée déterminée", 
            f"{analysis['duration_determined']} semaines",
            duration_status
        )
        
        # Justification
        justification_status = "✅" if analysis["justification_found"] else "❌"
        table.add_row(
            "Justification de durée", 
            "Trouvée" if analysis["justification_found"] else "Manquante",
            justification_status
        )
        
        # Analyse d'écart
        gap_status = "✅" if analysis["gap_analysis_found"] else "❌"
        table.add_row(
            "Analyse d'écart", 
            "Effectuée" if analysis["gap_analysis_found"] else "Manquante",
            gap_status
        )
        
        # Utilisation des métriques
        metrics_status = "✅" if analysis["metrics_used"] else "❌"
        table.add_row(
            "Utilisation métriques", 
            "Oui" if analysis["metrics_used"] else "Non",
            metrics_status
        )
        
        # Plan complet
        plan_status = "✅" if analysis["complete_plan_found"] else "❌"
        table.add_row(
            "Plan complet généré", 
            "Oui" if analysis["complete_plan_found"] else "Non",
            plan_status
        )
        
        # Target time (si applicable)
        if result["target_time"]:
            target_time_status = "✅" if analysis["target_time_mentioned"] else "❌"
            table.add_row(
                "Objectif de temps pris en compte", 
                "Oui" if analysis["target_time_mentioned"] else "Non",
                target_time_status
            )
        
        console.print(table)
        
        # Afficher un extrait de la réponse
        response_preview = result["response"][:500] + "..." if len(result["response"]) > 500 else result["response"]
        rprint(f"\n[yellow]📖 Extrait de la réponse :[/yellow]")
        rprint(Panel(response_preview, title="Réponse (extrait)", border_style="blue"))
    
    def generate_detailed_report(self):
        """Générer le rapport détaillé final"""
        report_content = self.create_report_content()
        
        # Sauvegarder dans un fichier
        timestamp = self.test_start_time.strftime("%Y%m%d_%H%M%S")
        report_filename = f"rapport_objectif_centre_{timestamp}.md"
        
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        rprint(f"\n[bold green]📊 Rapport détaillé généré: {report_filename}[/bold green]")
        
        # Sauvegarder les données brutes en JSON
        json_filename = f"donnees_test_objectif_centre_{timestamp}.json"
        with open(json_filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        rprint(f"[cyan]📄 Données brutes sauvegardées: {json_filename}[/cyan]")
        
        return report_filename
    
    def create_report_content(self):
        """Créer le contenu du rapport détaillé"""
        timestamp = self.test_start_time.strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# Rapport de Test : Approche "Objectif-Centrée"

**Date et heure du test :** {timestamp}
**Objectif :** Valider que l'agent IA détermine automatiquement une durée optimale en fonction de l'objectif plutôt que de laisser l'utilisateur choisir une durée arbitraire.

## Résumé Exécutif

Ce test compare l'efficacité de la nouvelle approche "objectif-centrée" par rapport à l'ancienne approche "durée-centrée". L'agent doit analyser l'écart entre la performance actuelle de l'utilisateur et son objectif pour déterminer une durée de préparation appropriée.

## Scénarios Testés

"""
        
        for i, result in enumerate(self.results, 1):
            analysis = result["analysis"]
            
            report += f"""### Scénario {i}: {result['scenario']}

**Description :** {result['description']}

**Paramètres d'entrée :**
- Objectif : 10k
- Niveau : intermédiaire  
- Fréquence : 3 séances/semaine
- Target time : {result['target_time'] if result['target_time'] else 'Non spécifié'}
- Duration weeks : {result['duration_weeks_input']} (0 = agent détermine)

**Prompt envoyé :**
```
{result['prompt']}
```

**Temps d'exécution :** {result['execution_time']:.1f} secondes

**Résultats de l'analyse :**

| Critère | Résultat | Statut |
|---------|----------|--------|
| Durée déterminée | {analysis['duration_determined']} semaines | {'✅ Succès' if analysis['duration_determined'] > 2 else '❌ Échec'} |
| Justification fournie | {'Oui' if analysis['justification_found'] else 'Non'} | {'✅' if analysis['justification_found'] else '❌'} |
| Analyse d'écart effectuée | {'Oui' if analysis['gap_analysis_found'] else 'Non'} | {'✅' if analysis['gap_analysis_found'] else '❌'} |
| Métriques utilisateur utilisées | {'Oui' if analysis['metrics_used'] else 'Non'} | {'✅' if analysis['metrics_used'] else '❌'} |
| Plan complet généré | {'Oui' if analysis['complete_plan_found'] else 'Non'} | {'✅' if analysis['complete_plan_found'] else '❌'} |
| Objectif temps pris en compte | {'Oui' if analysis.get('target_time_mentioned', False) else 'Non applicable' if not result['target_time'] else 'Non'} | {'✅' if analysis.get('target_time_mentioned', True) else '❌'} |

**Semaines détectées dans le plan :** {', '.join(map(str, analysis['weeks_found'][:10]))}{'...' if len(analysis['weeks_found']) > 10 else ''}

**Réponse complète de l'agent :**

```markdown
{result['response']}
```

---

"""
        
        # Analyse comparative
        report += """## Analyse Comparative

"""
        
        if len(self.results) >= 2:
            scenario_a = self.results[0]['analysis']
            scenario_b = self.results[1]['analysis']
            
            report += f"""### Comparaison des Durées Déterminées

- **Scénario A (avec target_time)** : {scenario_a['duration_determined']} semaines
- **Scénario B (sans target_time)** : {scenario_b['duration_determined']} semaines

### Qualité des Justifications

- **Scénario A** : {'Justification trouvée' if scenario_a['justification_found'] else 'Justification manquante'}
- **Scénario B** : {'Justification trouvée' if scenario_b['justification_found'] else 'Justification manquante'}

### Utilisation des Métriques Utilisateur

- **Scénario A** : {'Métriques utilisées' if scenario_a['metrics_used'] else 'Métriques non utilisées'}
- **Scénario B** : {'Métriques utilisées' if scenario_b['metrics_used'] else 'Métriques non utilisées'}

"""
        
        # Évaluation globale
        report += """## Évaluation Globale

### Points Positifs

"""
        
        positive_points = []
        negative_points = []
        
        for result in self.results:
            analysis = result['analysis']
            scenario = result['scenario']
            
            if analysis['duration_determined'] > 2:
                positive_points.append(f"✅ {scenario}: L'agent a déterminé une durée réaliste de {analysis['duration_determined']} semaines (>2)")
            else:
                negative_points.append(f"❌ {scenario}: Durée insuffisante de {analysis['duration_determined']} semaines")
                
            if analysis['justification_found']:
                positive_points.append(f"✅ {scenario}: Justification de la durée choisie fournie")
            else:
                negative_points.append(f"❌ {scenario}: Absence de justification pour la durée choisie")
                
            if analysis['gap_analysis_found']:
                positive_points.append(f"✅ {scenario}: Analyse de l'écart entre niveau actuel et objectif")
            else:
                negative_points.append(f"❌ {scenario}: Pas d'analyse d'écart détectée")
        
        for point in positive_points[:10]:  # Limiter à 10 points max
            report += f"- {point}\n"
        
        report += """
### Points d'Amélioration

"""
        
        for point in negative_points[:10]:  # Limiter à 10 points max
            report += f"- {point}\n"
        
        # Recommandations
        report += """
## Recommandations

### Améliorations du Prompt

"""
        
        if not all(r['analysis']['justification_found'] for r in self.results):
            report += """- **Renforcer l'exigence de justification** : Ajouter "OBLIGATOIRE: Justifie explicitement pourquoi tu choisis cette durée" dans le prompt.
"""
        
        if not all(r['analysis']['gap_analysis_found'] for r in self.results):
            report += """- **Clarifier l'analyse d'écart** : Reformuler l'étape 2 pour être plus explicite : "CALCULE l'écart en pourcentage entre la performance actuelle et l'objectif cible".
"""
        
        if not all(r['analysis']['metrics_used'] for r in self.results):
            report += """- **Forcer l'utilisation des métriques** : Ajouter une vérification que l'agent a bien appelé get_user_metrics_from_db avant de continuer.
"""
        
        report += """
### Améliorations Techniques

- **Validation des réponses** : Implémenter une vérification post-génération pour s'assurer que le nombre de semaines générées correspond à la durée déterminée.
- **Métriques de performance** : Ajouter des métriques pour mesurer la cohérence entre l'objectif, le niveau utilisateur et la durée proposée.
- **Feedback loop** : Implémenter un système de retour utilisateur pour affiner les durées proposées.

## Conclusion

"""
        
        success_rate = sum(1 for r in self.results if r['analysis']['duration_determined'] > 2) / len(self.results) * 100
        
        if success_rate >= 80:
            conclusion_status = "SUCCÈS"
            conclusion_color = "✅"
        elif success_rate >= 50:
            conclusion_status = "MITIGÉ"  
            conclusion_color = "⚠️"
        else:
            conclusion_status = "ÉCHEC"
            conclusion_color = "❌"
        
        report += f"""{conclusion_color} **Statut global : {conclusion_status}** ({success_rate:.0f}% de réussite)

L'approche "objectif-centrée" {"démontre son efficacité" if success_rate >= 80 else "nécessite des améliorations" if success_rate >= 50 else "présente des défaillances importantes"} dans la détermination automatique de durées de préparation appropriées.

{"Les agents analysent correctement les objectifs et génèrent des plans de durée réaliste." if success_rate >= 80 else "Des améliorations sont nécessaires pour garantir la cohérence des durées proposées." if success_rate >= 50 else "Une révision majeure du système de détermination de durée est recommandée."}

---

*Rapport généré automatiquement le {timestamp}*
"""
        
        return report

async def main():
    """Fonction principale du test"""
    console.rule("[bold blue]Test de l'Approche Objectif-Centrée[/bold blue]", style="blue")
    
    tester = ObjectiveCenteredTester()
    
    try:
        # Initialiser l'agent
        await tester.initialize_agent()
        
        # Scénario A : Avec target_time="45:00" (objectif de temps spécifique)
        await tester.run_scenario(
            scenario_name="Scénario A",
            description="Objectif de temps spécifique - 10k en 45:00",
            target_time="45:00",
            duration_weeks=0  # Agent détermine automatiquement
        )
        
        # Pause entre les scénarios
        rprint("\n[yellow]⏳ Pause de 5 secondes entre les scénarios...[/yellow]")
        await asyncio.sleep(5)
        
        # Scénario B : Sans target_time (objectif général)
        await tester.run_scenario(
            scenario_name="Scénario B", 
            description="Objectif général - 10k sans temps spécifique",
            target_time=None,
            duration_weeks=0  # Agent détermine automatiquement
        )
        
        # Générer le rapport détaillé
        rprint("\n[bold cyan]📊 Génération du rapport détaillé...[/bold cyan]")
        report_file = tester.generate_detailed_report()
        
        # Résumé final
        console.rule("[bold green]Test Terminé[/bold green]", style="green")
        
        success_count = sum(1 for r in tester.results if r['analysis']['duration_determined'] > 2)
        total_scenarios = len(tester.results)
        
        rprint(f"\n[bold]Résultats finaux :[/bold]")
        rprint(f"   - Scénarios réussis : {success_count}/{total_scenarios}")
        rprint(f"   - Rapport détaillé : {report_file}")
        
        if success_count == total_scenarios:
            rprint("[bold green]🎉 Tous les scénarios ont réussi ! L'approche objectif-centrée fonctionne correctement.[/bold green]")
        elif success_count > 0:
            rprint("[bold yellow]⚠️ Certains scénarios nécessitent des améliorations.[/bold yellow]")
        else:
            rprint("[bold red]❌ L'approche objectif-centrée nécessite une révision complète.[/bold red]")
        
        return 0 if success_count == total_scenarios else 1
        
    except KeyboardInterrupt:
        rprint("\n[yellow]⚠️ Test interrompu par l'utilisateur[/yellow]")
        return 1
    except Exception as e:
        rprint(f"[bold red]💥 Erreur fatale: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))