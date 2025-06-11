import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import folium_static
import json

# \--- Configuration de la Page ---

st.set_page_config(
    page_title="Coach AI",
    page_icon="🏃",
    layout="wide"
)

# \--- Constantes et Configuration ---

# L'URL de votre API. Assurez-vous que le service FastAPI tourne.

API_URL = "http://127.0.0.1:8000"

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

# On ajoute la page 'Coach AI' et on la met en premier

page = st.sidebar.radio("Aller à", ["Coach AI", "Liste des Activités", "Carte GPS"])

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
            f"{API_URL}/v1/coaching/chat", 
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

try:
response = requests.get(f"{API_URL}/activities?skip=0&amp;limit=500", headers=HEADERS)
response.raise_for_status()
data = response.json()
df = pd.DataFrame(data)
st.dataframe(df)
except requests.exceptions.RequestException as e:
st.error(f"Erreur lors de la récupération des activités : {e}")


# \==============================================================================

# PAGE 3 : CARTE GPS

# \==============================================================================

elif page == "Carte GPS":
st.title("🗺️ Affichage d'un Parcours GPS")

On pourrait remplacer ce champ par un sélecteur basé sur la liste des activités
activity_id = st.number_input("Entrez l'ID de l'activité :", min_value=1, step=1, value=None)

if activity_id and st.button("Charger le parcours"):
try:
# Note: L'API de données devrait aussi être sécurisée.
# Pour l'instant on ajoute l'en-tête, mais il faudrait l'implémenter dans l'API.
response = requests.get(f"{API_URL}/gps_data/{activity_id}/gps", headers=HEADERS) # Endpoint à créer
response.raise_for_status()

    data = response.json()
    df_gps = pd.DataFrame(data)
    
    if df_gps.empty:
        st.warning("Aucune donnée GPS disponible pour cette activité.")
    else:
        # Création de la carte
        m = folium.Map(location=[df_gps["latitude"].mean(), df_gps["longitude"].mean()], zoom_start=14)
        points = list(zip(df_gps["latitude"], df_gps["longitude"]))
        folium.PolyLine(points, color="red", weight=3, opacity=0.8).add_to(m)
        
        # Ajout de marqueurs de début et de fin
        folium.Marker(points[0], popup="Début", icon=folium.Icon(color="green")).add_to(m)
        folium.Marker(points[-1], popup="Fin", icon=folium.Icon(color="red")).add_to(m)
        
        # Affichage de la carte dans Streamlit
        folium_static(m, width=700, height=500)

except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        st.error("Activité ou données GPS non trouvées. Vérifiez l'ID.")
    else:
        st.error(f"Erreur HTTP : {e}")
except requests.exceptions.RequestException as e:
    st.error(f"Erreur de connexion à l'API : {e}")