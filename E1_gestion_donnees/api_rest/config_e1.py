"""
Configuration pour l'API E1 - Version simplifiée
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration de la base de données
DB_TYPE = os.getenv("DB_TYPE", "postgresql")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "coach_ia_db")
DB_USER = os.getenv("DB_USER", "coach_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "coach_password")

# Construction de l'URL de la base de données
if DB_TYPE == "postgresql":
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
elif DB_TYPE == "sqlite":
    DATABASE_URL = f"sqlite:///./data/{DB_NAME}.db"
else:
    raise ValueError(f"Type de base de données non supporté: {DB_TYPE}")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")