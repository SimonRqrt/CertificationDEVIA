import logging
import os
from typing import List, Dict, Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert

log = logging.getLogger(__name__)

# Configuration de la base de données directe depuis l'environnement
def get_database_url():
    DB_TYPE = os.getenv("DB_TYPE", "postgresql")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "coach_ia_db")
    DB_USER = os.getenv("DB_USER", "coach_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "coach_password")
    
    if DB_TYPE == "postgresql":
        return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    elif DB_TYPE == "sqlite":
        return f"sqlite:///./data/{DB_NAME}.db"
    else:
        raise ValueError(f"Type de base de données non supporté: {DB_TYPE}")

def create_db_engine(db_url=None):
    if db_url is None:
        db_url = get_database_url()
    
    try:
        engine_kwargs = {
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
        
        if 'postgresql' in db_url:
            engine_kwargs['connect_args'] = {
                'connect_timeout': 10,
                'sslmode': 'disable'
            }
        
        engine = sa.create_engine(db_url, **engine_kwargs)
        log.info(f"✅ Connexion à la base de données réussie: {db_url.split('@')[0]}@***")
        return engine
    except Exception as e:
        log.error(f"❌ Erreur connexion base de données: {e}")
        raise

def create_tables(engine):
    """
    Crée les tables nécessaires si elles n'existent pas
    """
    metadata = sa.MetaData()
    
    # Table des utilisateurs
    users_table = sa.Table(
        'users',
        metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('email', sa.String(100), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Table des activités simplifiée
    activities_table = sa.Table(
        'activities',
        metadata,
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('activity_type', sa.String(50)),
        sa.Column('start_time', sa.DateTime),
        sa.Column('duration_seconds', sa.Integer),
        sa.Column('distance_meters', sa.Float),
        sa.Column('calories', sa.Integer),
        sa.Column('avg_heart_rate', sa.Integer),
        sa.Column('max_heart_rate', sa.Integer),
        sa.Column('created_at', sa.DateTime, default=sa.func.now())
    )
    
    try:
        metadata.create_all(engine)
        log.info("✅ Tables créées ou vérifiées avec succès")
    except Exception as e:
        log.error(f"❌ Erreur lors de la création des tables: {e}")
        raise

def save_activities_to_db(engine, activities: List[Dict[str, Any]], user_id: int) -> int:
    """
    Sauvegarde les activités dans la base de données
    """
    if not activities:
        log.warning("Aucune activité à sauvegarder")
        return 0
    
    try:
        with engine.connect() as conn:
            # Préparer les données
            activities_data = []
            for activity in activities:
                activity_data = {
                    'user_id': user_id,
                    'name': activity.get('activityName', ''),
                    'activity_type': activity.get('activityType', {}).get('typeKey', ''),
                    'start_time': activity.get('startTimeLocal'),
                    'duration_seconds': activity.get('duration', 0),
                    'distance_meters': activity.get('distance', 0.0),
                    'calories': activity.get('calories', 0),
                    'avg_heart_rate': activity.get('averageHR', 0),
                    'max_heart_rate': activity.get('maxHR', 0)
                }
                activities_data.append(activity_data)
            
            # Insertion avec gestion des doublons pour PostgreSQL
            if 'postgresql' in str(engine.url):
                stmt = pg_insert(sa.text('activities')).values(activities_data)
                stmt = stmt.on_conflict_do_nothing(index_elements=['user_id', 'start_time'])
                result = conn.execute(stmt)
            else:
                # Pour SQLite - insertion simple
                result = conn.execute(
                    sa.text("""INSERT OR IGNORE INTO activities 
                              (user_id, name, activity_type, start_time, duration_seconds, 
                               distance_meters, calories, avg_heart_rate, max_heart_rate) 
                              VALUES (:user_id, :name, :activity_type, :start_time, :duration_seconds,
                                      :distance_meters, :calories, :avg_heart_rate, :max_heart_rate)"""),
                    activities_data
                )
            
            conn.commit()
            saved_count = len(activities_data)
            log.info(f"✅ {saved_count} activités sauvegardées en base de données")
            return saved_count
            
    except Exception as e:
        log.error(f"❌ Erreur lors de la sauvegarde: {e}")
        raise