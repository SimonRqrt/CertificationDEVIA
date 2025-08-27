#!/usr/bin/env python3
"""
Script de test pour vérifier si l'agent IA respecte le paramètre duration_weeks.
Test avec un plan 10k, niveau intermédiaire, 3 séances/semaine, 12 semaines.
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Ajouter le chemin du projet pour les imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Charger les variables d'environnement depuis le répertoire racine
load_dotenv(project_root / ".env")

from rich import print as rprint
from langchain_core.messages import HumanMessage

# Import de l'agent
from E3_model_IA.scripts.advanced_agent import get_coaching_graph, AgentState

async def test_duration_weeks():
    """Test pour vérifier que l'agent génère bien un plan de 12 semaines."""
    
    rprint("[bold cyan]🧪 Test de l'agent IA - Paramètre duration_weeks[/bold cyan]")
    rprint("=" * 60)
    
    try:
        # Initialiser l'agent
        rprint("[yellow]📋 Initialisation de l'agent...[/yellow]")
        graph = await get_coaching_graph()
        
        # Paramètres du test
        user_id = 1
        test_query = """Je suis l'utilisateur 1. 
Je souhaite un plan d'entraînement complet pour préparer un 10k.

Paramètres de ma demande :
- Objectif : Course 10km 
- Niveau : intermédiaire
- Fréquence : 3 séances par semaine
- Durée du plan : 12 semaines exactement

Peux-tu me générer un plan d'entraînement structuré sur ces 12 semaines ?"""

        rprint(f"[yellow]🎯 Test avec les paramètres :[/yellow]")
        rprint(f"   - Utilisateur ID: {user_id}")
        rprint(f"   - Objectif: 10k")
        rprint(f"   - Niveau: intermédiaire") 
        rprint(f"   - Fréquence: 3 séances/semaine")
        rprint(f"   - Durée: 12 semaines")
        rprint()
        
        # Configurer le mode plan_generator pour forcer la génération multi-semaines
        initial_state = {
            "messages": [HumanMessage(content=test_query)],
            "mode": "plan_generator"  # ✅ Mode spécifique pour plans multi-semaines
        }
        
        rprint("[yellow]⚡ Exécution de l'agent...[/yellow]")
        rprint("(Cela peut prendre quelques secondes)")
        rprint()
        
        full_response = ""
        
        # Stream de l'exécution
        async for event in graph.astream(
            initial_state,
            config={"configurable": {"thread_id": f"test-duration-{user_id}"}}
        ):
            for step in event.values():
                if "messages" in step and step["messages"]:
                    message = step["messages"][-1]
                    if hasattr(message, 'content') and message.content:
                        # Accumuler la réponse complète
                        if hasattr(message, 'type') and message.type == "ai":
                            full_response += message.content
        
        rprint("[bold green]✅ Réponse complète de l'agent :[/bold green]")
        rprint("=" * 60)
        rprint(full_response)
        rprint("=" * 60)
        
        # Analyse de la réponse
        rprint("\n[bold yellow]📊 Analyse de la réponse :[/bold yellow]")
        
        # Compter les occurrences de "Semaine"
        semaine_count = full_response.lower().count("semaine")
        rprint(f"   - Nombre d'occurrences du mot 'semaine': {semaine_count}")
        
        # Rechercher les mentions explicites de semaines numérotées
        weeks_found = []
        for i in range(1, 21):  # Chercher jusqu'à 20 semaines
            if f"semaine {i}" in full_response.lower() or f"## semaine {i}" in full_response.lower():
                weeks_found.append(i)
        
        rprint(f"   - Semaines numérotées détectées: {weeks_found}")
        rprint(f"   - Nombre de semaines générées: {len(weeks_found)}")
        
        # Vérification du critère de réussite
        success = len(weeks_found) >= 12
        
        if success:
            rprint(f"[bold green]✅ SUCCÈS: L'agent a généré {len(weeks_found)} semaines (≥12 demandées)[/bold green]")
        else:
            rprint(f"[bold red]❌ ÉCHEC: L'agent a généré seulement {len(weeks_found)} semaines (< 12 demandées)[/bold red]")
        
        # Vérifications supplémentaires
        has_plan_structure = "| Jour" in full_response and "| Type Séance" in full_response
        has_objective_10k = "10k" in full_response.lower() or "10 km" in full_response.lower()
        has_intermediate_level = "intermédiaire" in full_response.lower()
        
        rprint(f"   - Structure de plan détectée: {'✅' if has_plan_structure else '❌'}")
        rprint(f"   - Objectif 10k mentionné: {'✅' if has_objective_10k else '❌'}")
        rprint(f"   - Niveau intermédiaire mentionné: {'✅' if has_intermediate_level else '❌'}")
        
        # Résumé final
        rprint(f"\n[bold {'green' if success else 'red'}]🎯 RÉSULTAT DU TEST:[/bold {'green' if success else 'red'}]")
        if success:
            rprint(f"[green]L'agent respecte bien le paramètre duration_weeks et génère un plan complet de {len(weeks_found)} semaines.[/green]")
        else:
            rprint(f"[red]L'agent ne respecte PAS le paramètre duration_weeks. Il a généré {len(weeks_found)} semaines au lieu de 12.[/red]")
        
        return success, len(weeks_found), full_response
        
    except Exception as e:
        rprint(f"[bold red]❌ Erreur lors du test: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        return False, 0, ""

async def main():
    """Fonction principale du test."""
    try:
        success, weeks_generated, response = await test_duration_weeks()
        
        # Optionnel : sauvegarder la réponse complète
        with open("test_agent_response.txt", "w", encoding="utf-8") as f:
            f.write(f"=== TEST AGENT DURATION_WEEKS ===\n")
            f.write(f"Paramètres: 10k, intermédiaire, 3 séances/semaine, 12 semaines\n")
            f.write(f"Semaines générées: {weeks_generated}\n")
            f.write(f"Succès: {success}\n\n")
            f.write("=== RÉPONSE COMPLÈTE ===\n")
            f.write(response)
        
        rprint(f"\n[cyan]📄 Réponse complète sauvegardée dans: test_agent_response.txt[/cyan]")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        rprint("\n[yellow]⚠️ Test interrompu par l'utilisateur[/yellow]")
        return 1
    except Exception as e:
        rprint(f"[bold red]💥 Erreur fatale: {e}[/bold red]")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))