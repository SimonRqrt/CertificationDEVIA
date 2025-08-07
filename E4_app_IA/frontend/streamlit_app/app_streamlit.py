import streamlit as st
import requests
import pandas as pd
import json

# \--- Configuration de la Page ---

st.set_page_config(
    page_title="Coach AI",
    page_icon="🏃",
    layout="wide"
)

# \--- Constantes et Configuration ---

# L'URL de votre API. Assurez-vous que le service FastAPI tourne.

# Configuration adaptée selon l'environnement (local vs Docker)
import os
if os.getenv('DOCKER_ENV') == 'true':
    # Architecture unifiée PostgreSQL - FastAPI comme point d'accès principal
    FASTAPI_URL = "http://fastapi:8000"     # API unifiée (données + IA)
    DJANGO_URL = "http://django:8002"       # Backup et admin
else:
    # Architecture unifiée PostgreSQL - FastAPI comme point d'accès principal  
    FASTAPI_URL = "http://localhost:8000"   # API unifiée (données + IA)
    DJANGO_URL = "http://localhost:8002"    # Backup et admin

# Architecture unifiée : FastAPI comme point d'accès unique
API_URL = FASTAPI_URL  # FastAPI unifié avec PostgreSQL Django

# On récupère la clé API depuis les secrets de Streamlit

try:
    API_KEY = st.secrets["API_KEY"]
except FileNotFoundError:
    st.error("Fichier secrets.toml non trouvé. Veuillez suivre les instructions du README pour le créer.")
    st.stop()
except KeyError:
    st.error("Clé API_KEY non trouvée dans secrets.toml.")
    st.stop()

HEADERS = {"X-API-Key": API_KEY}

# \--- Barre latérale de Navigation ---

st.sidebar.title("Navigation")

# Navigation avec architecture unifiée

page = st.sidebar.radio("Aller à", [
    "Coach AI", 
    "Liste des Activités", 
    "Statistiques Utilisateur"
])

# \==============================================================================

# PAGE 1 : COACH AI (Nouvelle Page)

# \==============================================================================

if page == "Coach AI":
    st.title("🤖 Coach AI")
    st.markdown("Votre assistant personnel pour analyser vos performances et préparer vos objectifs.")

# Initialisation de l'historique du chat dans l'état de la session
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Bonjour ! Comment puis-je vous aider aujourd'hui ?"}]

# Affichage des messages de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Champ de saisie pour l'utilisateur
if prompt := st.chat_input("Posez votre question sur votre entraînement..."):
    # Ajout du message de l'utilisateur à l'historique et affichage
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)








    # Affichage de la réponse de l'assistant en streaming
    with st.chat_message("assistant"):
        full_response = ""
        message_placeholder = st.empty()
        
        # Construction de la requête pour l'API
        chat_payload = {
            "user_id": 1, # Pour l'instant, on utilise un ID fixe
            "message": prompt
        }
        
        try:
            # Appel de l'API en mode streaming
            response = requests.post(
                f"{API_URL}/v1/coaching/chat-legacy", 
                headers=HEADERS, 
                json=chat_payload, 
                stream=True
            )
            response.raise_for_status() # Lève une exception si le status n'est pas 2xx

            # Itération sur les lignes de la réponse streaming (format ndjson)
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if data["type"] == "content":
                        full_response += data["data"]
                        message_placeholder.markdown(full_response + "▌") # Affiche un curseur
            
            message_placeholder.markdown(full_response)
            
        except requests.exceptions.RequestException as e:
            full_response = f"Erreur de connexion à l'API : {e}"
            message_placeholder.error(full_response)
        except Exception as e:
            full_response = f"Une erreur inattendue est survenue : {e}"
            message_placeholder.error(full_response)

    # Ajout de la réponse complète de l'assistant à l'historique
    st.session_state.messages.append({"role": "assistant", "content": full_response})

    # \==============================================================================

    # PAGE 2 : LISTE DES ACTIVITÉS

    # \==============================================================================

elif page == "Liste des Activités":
    st.title("📋 Liste des Activités Récentes")

    # Configuration fixe pour l'utilisateur principal
    user_id = 2  # Utilisateur principal du système
    limit = 50   # Nombre fixe d'activités à afficher

    try:
        # Utilisation de l'API FastAPI unifiée avec PostgreSQL
        response = requests.get(f"{API_URL}/v1/activities/{user_id}?limit={limit}", headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        if data.get("activities"):
            # Transformation des données pour un affichage optimal
            activities_list = data["activities"]
            df = pd.DataFrame(activities_list)
            
            # Colonnes à afficher (sélection des plus importantes)
            display_columns = [
                'activity_name', 'activity_type', 'start_time', 
                'distance_km', 'duration_seconds', 'calories', 
                'average_hr', 'pace_per_km'
            ]
            
            # Filtrage des colonnes existantes
            available_columns = [col for col in display_columns if col in df.columns]
            df_display = df[available_columns].copy()
            
            # Formatage pour l'affichage
            if 'start_time' in df_display.columns:
                df_display['start_time'] = pd.to_datetime(df_display['start_time'], format='ISO8601').dt.strftime('%Y-%m-%d %H:%M')
            
            if 'duration_seconds' in df_display.columns:
                df_display['duration_min'] = (df_display['duration_seconds'] / 60).round(1)
                df_display = df_display.drop('duration_seconds', axis=1)
            
            st.success(f"✅ {data['total_returned']} activités récupérées depuis PostgreSQL")
            st.dataframe(df_display, use_container_width=True)
            
            # Statistiques rapides
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total activités", data['total_returned'])
            with col2:
                total_distance = df['distance_km'].sum() if 'distance_km' in df.columns else 0
                st.metric("Distance totale (km)", f"{total_distance:.1f}")
            with col3:
                avg_hr = df['average_hr'].mean() if 'average_hr' in df.columns else 0
                st.metric("FC moyenne", f"{avg_hr:.0f}" if avg_hr > 0 else "N/A")
            with col4:
                total_calories = df['calories'].sum() if 'calories' in df.columns else 0
                st.metric("Calories totales", f"{total_calories:.0f}")
        else:
            st.warning("Aucune activité trouvée pour cet utilisateur")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion à l'API FastAPI : {e}")
        st.info("💡 Vérifiez que le serveur FastAPI est démarré sur localhost:8000")
    except Exception as e:
        st.error(f"Erreur lors du traitement des données : {e}")

# \==============================================================================

# PAGE 3 : STATISTIQUES UTILISATEUR

# \==============================================================================

elif page == "Statistiques Utilisateur":
    st.title("📊 Statistiques Utilisateur")

    # Configuration fixe pour l'utilisateur principal
    user_id = 2  # Utilisateur principal du système

    try:
        # Récupération des statistiques via FastAPI unifiée
        response = requests.get(f"{API_URL}/v1/stats/{user_id}", headers=HEADERS)
        response.raise_for_status()
        stats_data = response.json()
        
        if stats_data.get("stats"):
            stats = stats_data["stats"]
            
            st.success("✅ Statistiques récupérées depuis PostgreSQL")
            
            # Métriques principales
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Activités", stats.get("total_activities", 0))
            with col2:
                st.metric("Distance Totale", f"{stats.get('total_distance_km', 0):.1f} km")
            with col3:
                st.metric("Temps Total", f"{stats.get('total_duration_hours', 0):.1f}h")
            with col4:
                st.metric("Calories Totales", f"{stats.get('total_calories', 0):,}")
            
            # Métriques avancées
            col5, col6, col7 = st.columns(3)
            with col5:
                avg_hr = stats.get('avg_heart_rate')
                st.metric("FC Moyenne", f"{avg_hr} bpm" if avg_hr else "N/A")
            with col6:
                st.metric("Distance Max", f"{stats.get('max_distance_km', 0):.1f} km")
            with col7:
                st.metric("Durée Max", f"{stats.get('max_duration_hours', 0):.1f}h")
            
            # Répartition par type d'activité
            if stats.get("activity_types"):
                st.subheader("🏃 Répartition par Type d'Activité")
                
                activity_types = stats["activity_types"]
                types_df = pd.DataFrame([
                    {
                        "Type": activity_type.replace("_", " ").title(),
                        "Nombre": data["count"],
                        "Distance (km)": data["total_distance_km"]
                    }
                    for activity_type, data in activity_types.items()
                ])
                
                # Tri par nombre d'activités
                types_df = types_df.sort_values("Nombre", ascending=False)
                st.dataframe(types_df, use_container_width=True)
                
                # Graphique en barres
                st.bar_chart(types_df.set_index("Type")["Nombre"])
                
        else:
            st.warning("Aucune statistique trouvée pour cet utilisateur")
            
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion à l'API : {e}")
    except Exception as e:
        st.error(f"Erreur lors du traitement des statistiques : {e}")


