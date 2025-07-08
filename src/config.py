import os
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote_plus

# Charger les variables d'environnement
load_dotenv()

# Chemins
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Créer le répertoire de données s'il n'existe pas
DATA_DIR.mkdir(exist_ok=True)

# Configuration Garmin
GARMIN_EMAIL = os.environ.get("GARMIN_EMAIL")
GARMIN_PASSWORD = os.environ.get("GARMIN_PASSWORD")

# Configuration de la base de données
DB_TYPE = os.getenv("DB_TYPE") 
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Construction de l'URL de la base de données
if DB_TYPE == "sqlite":
    DATABASE_URL = f"sqlite:///{DATA_DIR}/{DB_NAME}.db"
elif DB_TYPE == "sqlserver":
    encoded_password = quote_plus(DB_PASSWORD)
    DATABASE_URL = ( 
        f"mssql+pyodbc://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?driver=ODBC+Driver+17+for+SQL+Server"
    )
else:
    raise ValueError(f"Type de base de données non pris en charge: {DB_TYPE}")

# Configuration de l'API
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", "8000"))
API_DEBUG = os.environ.get("API_DEBUG", "False").lower() == "true"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")

# Planification
FETCH_INTERVAL_HOURS = int(os.environ.get("FETCH_INTERVAL_HOURS", "12"))

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

USER_ID = 1  # ou la valeur que tu veux