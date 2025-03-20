import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import folium_static

# URL de l'API FastAPI
API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Activités Sportives", layout="wide")

# Barre latérale pour la navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Aller à", ["Liste des Activités", "Carte GPS"])

if page == "Liste des Activités":
    st.title("📋 Liste des Activités")
    
    # Récupérer les activités
    response = requests.get(f"{API_URL}/activities?skip=0&limit=500")
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        st.dataframe(df)  # Afficher le tableau des activités
    else:
        st.error("Erreur lors de la récupération des activités.")

elif page == "Carte GPS":
    st.title("🗺️ Carte des Activités")
    
    activity_id = st.number_input("ID de l'activité :", min_value=1, step=1)
    
    if st.button("Charger la carte"):
        response = requests.get(f"{API_URL}/activities/{activity_id}/gps")
        
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            
            if df.empty:
                st.warning("Aucune donnée GPS disponible pour cette activité.")
            else:
                m = folium.Map(location=[df["latitude"].mean(), df["longitude"].mean()], zoom_start=13)
                points = list(zip(df["latitude"], df["longitude"]))
                folium.PolyLine(points, color="blue", weight=2.5, opacity=1).add_to(m)
                folium_static(m)
        else:
            st.error("Erreur lors de la récupération des données GPS.")
