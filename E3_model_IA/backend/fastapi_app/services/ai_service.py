"""
Service IA pour la gestion des interactions avec l'agent
"""

import json
import time
import uuid
from datetime import datetime
from langchain_core.messages import HumanMessage

from django_auth_service import django_auth_service

class AIService:
    def __init__(self, coaching_agent):
        self.coaching_agent = coaching_agent
    
    async def chat_stream(self, chat_request, user_id=None):
        """Stream de chat avec l'agent IA"""
        start_time = time.time()
        session_id = str(uuid.uuid4())
        
        user_id = user_id or chat_request.user_id or 1
        full_input = f"Je suis l'utilisateur {user_id}. {chat_request.message}"
        thread_id = chat_request.thread_id or f"user-thread-{user_id}"
        
        # SOLUTION FINALE: CallbackHandler intégré 
        from prometheus_callback import prometheus_callback
        config = {
            "configurable": {"thread_id": thread_id},
            "callbacks": [prometheus_callback]
        }

        # Stocker la session de coaching
        session_data = {
            'session_id': session_id,
            'title': chat_request.message[:100],
            'user_message': chat_request.message,
            'ai_response': '',
            'context_data': {'user_id': user_id},
            'response_time': None
        }

        ai_response_parts = []
        
        # Déterminer le mode basé sur le thread_id
        mode = "plan_generator" if "plan-generation" in thread_id else "streamlit"
        
        async for event in self.coaching_agent.astream({
            "messages": [HumanMessage(content=full_input)], 
            "mode": mode
        }, config=config):
            for step in event.values():
                message = step["messages"][-1]
                if hasattr(message, 'content') and message.content:
                    ai_response_parts.append(message.content)
                    yield json.dumps({"type": "content", "data": message.content}) + "\n"
        
        # Finaliser la session
        end_time = time.time()
        session_data['ai_response'] = ''.join(ai_response_parts)
        session_data['response_time'] = end_time - start_time
        
        # Enregistrer dans Django
        django_auth_service.create_coaching_session(1, session_data)
        
        yield json.dumps({"type": "end", "data": "Stream finished."}) + "\n"
    
    async def chat_legacy_stream(self, chat_request):
        """Stream de chat legacy avec clé API"""
        user_id = chat_request.user_id or 1
        full_input = f"Je suis l'utilisateur {user_id}. {chat_request.message}"
        thread_id = chat_request.thread_id or f"user-thread-{user_id}"
        
        # Configuration standard
        config = {"configurable": {"thread_id": thread_id}}

        # Déterminer le mode basé sur le thread_id
        mode = "plan_generator" if "plan-generation" in thread_id else "streamlit"
        print(f"DEBUG: thread_id={thread_id}, mode détecté={mode}")
        
        async for event in self.coaching_agent.astream({
            "messages": [HumanMessage(content=full_input)], 
            "mode": mode
        }, config=config):
            for step in event.values():
                message = step["messages"][-1]
                if hasattr(message, 'content') and message.content:
                    yield json.dumps({"type": "content", "data": message.content}) + "\n"
        yield json.dumps({"type": "end", "data": "Stream finished."}) + "\n"
    
    async def generate_training_plan(self, plan_request):
        """Génération de plan d'entraînement"""
        if not plan_request.use_advanced_agent:
            return {"error": "Agent avancé requis"}
        
        # Construction du prompt optimisé - approche objectif-centrée
        duration_instruction = ""
        if plan_request.duration_weeks > 0:
            duration_instruction = f"- DURÉE IMPOSÉE: {plan_request.duration_weeks} semaines exactement"
        else:
            duration_instruction = "- DURÉE À DÉTERMINER: Analyse l'écart entre niveau actuel et objectif pour déterminer la durée optimale (4-20 semaines)"
        
        target_time_info = ""
        if plan_request.target_time:
            target_time_info = f"- TEMPS OBJECTIF: {plan_request.target_time} sur {plan_request.goal}"
        
        full_input = f"""Je suis l'utilisateur {plan_request.user_id}.

ANALYSE ET GÉNÈRE un plan d'entraînement intelligent:
- Objectif: {plan_request.goal}  
- Niveau déclaré: {plan_request.level}
- {plan_request.sessions_per_week} séances/semaine
{target_time_info}
{duration_instruction}

ÉTAPES OBLIGATOIRES:
1. UTILISE get_user_metrics_from_db({plan_request.user_id}) pour analyser le niveau réel
2. ÉVALUE l'écart entre performance actuelle et objectif cible
3. DÉTERMINE la durée optimale de préparation (justifie ton choix)
4. GÉNÈRE le plan COMPLET sur cette durée avec tableaux markdown pour CHAQUE semaine

IMPORTANT: Si objectif de temps donné, calcule une progression réaliste. Sinon, utilise durées standards selon l'objectif.

Sois précis, réaliste et justifie tes choix."""

        thread_id = f"plan-generation-{plan_request.user_id}"
        
        # Configuration standard
        config = {"configurable": {"thread_id": thread_id}}
        
        print(f"Génération plan pour user {plan_request.user_id}...")
        start_generation = time.time()
        
        # Utiliser invoke pour plus de vitesse
        result = self.coaching_agent.invoke({
            "messages": [HumanMessage(content=full_input)], 
            "mode": "plan_generator"
        }, config=config)
        
        # Extraire la réponse de l'agent
        full_response = ""
        if "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            if hasattr(last_message, 'content'):
                full_response = last_message.content
        
        generation_time = time.time() - start_generation
        print(f"Plan généré en {generation_time:.2f}s")
        
        if not full_response or len(full_response) < 50:
            print(f"Réponse trop courte: {full_response}")
            full_response = "Erreur: Plan non généré correctement"
        
        return {
            "success": True,
            "plan_content": full_response,
            "user_id": plan_request.user_id,
            "goal": plan_request.goal,
            "method": "invoke_optimized",
            "generation_time_seconds": round(generation_time, 2)
        }