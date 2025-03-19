import os
from dotenv import load_dotenv
from pathlib import Path

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
DB_TYPE = os.environ.get("DB_TYPE", "sqlite")  # sqlite, postgresql, mysql
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "garmin_data")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")

# Construction de l'URL de la base de données
if DB_TYPE == "sqlite":
    DATABASE_URL = f"sqlite:///{DATA_DIR}/{DB_NAME}.db"
elif DB_TYPE == "postgresql":
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
else:
    raise ValueError(f"Type de base de données non pris en charge: {DB_TYPE}")

# Configuration de l'API
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", "8000"))
API_DEBUG = os.environ.get("API_DEBUG", "False").lower() == "true"

# Planification
FETCH_INTERVAL_HOURS = int(os.environ.get("FETCH_INTERVAL_HOURS", "12"))

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")