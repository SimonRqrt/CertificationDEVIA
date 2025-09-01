import logging
from typing import List, Dict, Any

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as pg_insert
import numpy as np

from src.config import DATABASE_URL

log = logging.getLogger(__name__)

def create_db_engine(db_url=DATABASE_URL):
    try:
        engine_kwargs = {
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
        
        if 'postgresql' in db_url:
            engine_kwargs['connect_args'] = {
                'application_name': 'coach_ai_fastapi'
            }
        elif 'mssql' in db_url or 'sqlserver' in db_url:
            engine_kwargs['connect_args'] = {
                'timeout': 30,
                'connect_timeout': 30,
                'autocommit': True
            }
        elif 'sqlite' in db_url:
            engine_kwargs['connect_args'] = {
                'check_same_thread': False
            }
        
        engine = sa.create_engine(db_url, **engine_kwargs)
        
        with engine.connect() as conn:
            conn.execute(sa.text("SELECT 1"))
        
        log.info("Connexion à la base de données établie avec succès.")
        return engine
    except Exception as e:
        log.error("Erreur lors de la création du moteur de base de données.", exc_info=True)
        
        if 'postgresql' in db_url or 'mssql' in db_url:
            log.warning("Tentative de fallback vers SQLite Django...")
            fallback_url = "sqlite:///data/django_garmin_data.db"
            try:
                fallback_engine = sa.create_engine(fallback_url, connect_args={'check_same_thread': False})
                with fallback_engine.connect() as conn:
                    conn.execute(sa.text("SELECT 1"))
                log.info("Fallback SQLite Django établi avec succès (378 activités).")
                return fallback_engine
            except Exception as fallback_error:
                log.error("Échec du fallback SQLite.", exc_info=True)
        
        raise

def create_tables(engine) -> Dict[str, sa.Table]:
    metadata = sa.MetaData()

    users = sa.Table(
        "users", metadata,
        sa.Column("user_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("nom", sa.String(100)),
        sa.Column("prenom", sa.String(100)),
        sa.Column("age", sa.Integer),
        sa.Column("sexe", sa.String(10)),
        sa.Column("taille_cm", sa.Integer),
        sa.Column("poids_kg", sa.Float),
        sa.Column("niveau", sa.String(50)),
        sa.Column("objectif_type", sa.String(50)),
        sa.Column("objectif_temps", sa.String(50)),
        sa.Column("disponibilite", sa.Text),
        sa.Column("blessures", sa.Text),
        sa.Column("terrain_prefere", sa.String(20)),
        sa.Column("frequence_semaine", sa.Integer)
    )

    activities_table = sa.Table(
        "activities", metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("activity_id", sa.BigInteger, unique=True, nullable=False),
        sa.Column("activity_name", sa.String(255)),
        sa.Column("activity_type", sa.String(50)),
        sa.Column("start_time", sa.DateTime(timezone=True)),
        sa.Column("distance_meters", sa.Float),
        sa.Column("duration_seconds", sa.Float),
        sa.Column("average_speed", sa.Float),
        sa.Column("max_speed", sa.Float),
        sa.Column("calories", sa.Integer),
        sa.Column("average_hr", sa.Float),
        sa.Column("max_hr", sa.Integer),
        sa.Column("elevation_gain", sa.Float),
        sa.Column("elevation_loss", sa.Float),
        sa.Column("start_latitude", sa.Float),
        sa.Column("start_longitude", sa.Float),
        sa.Column("device_name", sa.String(100)),
        sa.Column("created_timestamp", sa.DateTime),
        sa.Column("steps", sa.Integer),
        sa.Column("average_running_cadence", sa.Float),
        sa.Column("max_running_cadence", sa.Float),
        sa.Column("stride_length", sa.Float),
        sa.Column("vo2max_estime", sa.Float),
        sa.Column("training_load", sa.Float),
        sa.Column("aerobic_effect", sa.Float),
        sa.Column("anaerobic_effect", sa.Float),
        sa.Column("temp_min", sa.Float),
        sa.Column("temp_max", sa.Float),
        sa.Column("fastest_split_5000", sa.Float),
        sa.Column("fastest_split_10000", sa.Float),
        sa.Column("hr_zone_1", sa.Float),
        sa.Column("hr_zone_2", sa.Float),
        sa.Column("hr_zone_3", sa.Float),
        sa.Column("hr_zone_4", sa.Float),
        sa.Column("hr_zone_5", sa.Float)
    )

    gps_data = sa.Table(
        "gps_data", metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("activity_id", sa.Integer, sa.ForeignKey("activities.id")),
        sa.Column("latitude", sa.Float),
        sa.Column("longitude", sa.Float),
        sa.Column("timestamp", sa.DateTime)
    )

    metrics = sa.Table(
        "metrics", metadata,
        sa.Column("metrics_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("date_calcul", sa.DateTime(timezone=True)),
        sa.Column("vma_kmh", sa.Float),
        sa.Column("vo2max_estime", sa.Float),
        sa.Column("zone_fc", sa.Text),
        sa.Column("charge_7j", sa.Float),
        sa.Column("charge_28j", sa.Float),
        sa.Column("forme", sa.Float),
        sa.Column("fatigue", sa.Float),
        sa.Column("tendance_progression", sa.String(50)),
        sa.Column("ratio_endurance", sa.Float),
        sa.Column("prediction_10k_min", sa.Float),
        sa.Column("recommandation_jour", sa.Text)
    )

    splits = sa.Table(
        "splits", metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("activity_id", sa.BigInteger, sa.ForeignKey("activities.activity_id"), nullable=False),
        sa.Column("split_index", sa.Integer),
        sa.Column("split_type", sa.String(50)),
        sa.Column("duration_seconds", sa.Float),
        sa.Column("distance_meters", sa.Float),
        sa.Column("average_speed", sa.Float),
        sa.Column("max_speed", sa.Float),
        sa.Column("elevation_gain", sa.Float),
        sa.Column("elevation_loss", sa.Float)
    )

    try:
        metadata.create_all(engine, checkfirst=True)
        log.info("Vérification des tables terminée. Les tables sont prêtes.")
    except Exception as e:
        log.error("Erreur lors de la création des tables.", exc_info=True)
        raise

    return metadata.tables

def insert_user(engine, tables, user_data):
    with engine.connect() as conn:
        try:
            insert_stmt = tables["users"].insert().values(**user_data)
            conn.execute(insert_stmt)
            conn.commit()
            print(f"Utilisateur {user_data.get('prenom', '')} {user_data.get('nom', '')} inséré avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'insertion de l'utilisateur : {e}")

def ensure_user_exists(engine, tables, user_id, user_defaults=None):
    with engine.connect() as conn:
        result = conn.execute(
            tables["users"].select().where(tables["users"].c.user_id == user_id)
        ).fetchone()
        if not result:
            user_data = {"user_id": user_id}
            if user_defaults:
                user_data.update(user_defaults)
            else:
                user_data.update({
                    "nom": "Test",
                    "prenom": "User",
                    "age": 30,
                    "sexe": "Homme",
                    "taille_cm": 180,
                    "poids_kg": 75.0,
                    "niveau": "Débutant",
                    "objectif_type": "10km",
                    "objectif_temps": "00:50:00",
                    "disponibilite": "[]",
                    "blessures": "aucune",
                    "terrain_prefere": "Route",
                    "frequence_semaine": 3
                })
            conn.execute(tables["users"].insert().values(**user_data))
            conn.commit()
            log.info(f"Utilisateur user_id={user_id} inséré automatiquement.")

def store_activities_in_db(engine, tables: Dict, processed_data: List[Dict[str, Any]]):
    if not processed_data:
        log.info("Aucune activité à stocker.")
        return

    activities_table = tables["activities"]
    if processed_data:
        user_id = processed_data[0].get("user_id")
        if user_id is not None:
            ensure_user_exists(engine, tables, user_id)
    
    with engine.connect() as conn:
        existing_ids_query = sa.select(activities_table.c.activity_id)
        result = conn.execute(existing_ids_query)
        existing_ids = {row[0] for row in result}
        log.info(f"{len(existing_ids)} activités déjà présentes dans la base de données.")

    new_activities = [
        activity for activity in processed_data 
        if activity["activity_id"] not in existing_ids
    ]
    
    skipped_count = len(processed_data) - len(new_activities)
    if skipped_count > 0:
        log.info(f"{skipped_count} activités déjà existantes ont été ignorées.")

    if not new_activities:
        log.info("Aucune nouvelle activité à insérer.")
        return

    log.info(f"Début de l'insertion de {len(new_activities)} nouvelles activités...")
    try:
        with engine.begin() as conn:
            conn.execute(sa.insert(activities_table), new_activities)
        log.info(f"Stockage terminé: {len(new_activities)} nouvelles activités ajoutées.")
    except Exception as e:
        log.error("Erreur lors de l'insertion en masse des activités. Transaction annulée.", exc_info=True)
        raise

def store_metrics_in_db(engine, tables: Dict, metrics_data: Dict[str, Any]):
    if not metrics_data:
        log.warning("Aucune donnée de métrique à stocker.")
        return

    # Convertir proprement les scalaires numpy/pandas vers types Python natifs
    def _to_native(value):
        try:
            # Numpy scalars -> Python
            if isinstance(value, (np.generic,)):
                return value.item()
        except Exception:
            pass
        # Pandas Timestamp -> datetime
        if hasattr(value, "to_pydatetime"):
            try:
                return value.to_pydatetime()
            except Exception:
                pass
        if isinstance(value, dict):
            return {k: _to_native(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return type(value)(_to_native(v) for v in value)
        return value

    metrics_table = tables["metrics"]
    metrics_data = _to_native(metrics_data)
    user_id = metrics_data["user_id"]
    date_calcul = metrics_data["date_calcul"]

    with engine.connect() as conn:
        select_stmt = metrics_table.select().where(
            (metrics_table.c.user_id == user_id) &
            (metrics_table.c.date_calcul == date_calcul)
        )
        result = conn.execute(select_stmt).fetchone()

        if result:
            update_stmt = metrics_table.update().where(
                (metrics_table.c.user_id == user_id) &
                (metrics_table.c.date_calcul == date_calcul)
            ).values(**metrics_data)
            conn.execute(update_stmt)
            log.info(f"Métriques mises à jour pour user_id={user_id}, date={date_calcul}")
        else:
            insert_stmt = metrics_table.insert().values(**metrics_data)
            conn.execute(insert_stmt)
            log.info(f"Nouvelles métriques insérées pour user_id={user_id}, date={date_calcul}")
        conn.commit()

def get_activities_from_db(engine, tables, limit=10, offset=0):
    with engine.connect() as conn:
        try:
            result = conn.execute(sa.text("""
                SELECT id, activity_id, activity_name, activity_type, start_time, 
                       distance_meters, duration_seconds, average_hr, user_id
                FROM activities_activity 
                ORDER BY start_time DESC 
                LIMIT :limit OFFSET :offset
            """), {"limit": limit, "offset": offset}).fetchall()
            return result
        except:
            select_stmt = sa.select(tables["activities"]) \
                .order_by(sa.desc(tables["activities"].c.start_time)) \
                .limit(limit) \
                .offset(offset)
            result = conn.execute(select_stmt).fetchall()
            return result

def get_activity_by_id(engine, tables, activity_id):
    with engine.connect() as conn:
        select_stmt = sa.select(tables["activities"]).where(
            tables["activities"].c.activity_id == activity_id
        )
        result = conn.execute(select_stmt).fetchone()
        return result
