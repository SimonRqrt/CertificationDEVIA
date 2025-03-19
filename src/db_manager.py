import sqlalchemy as sa
from .config import DATABASE_URL

def create_db_engine(db_url=DATABASE_URL):
    """Crée une connexion à la base de données"""
    engine = sa.create_engine(db_url)
    return engine

def create_tables(engine):
    """Crée les tables nécessaires si elles n'existent pas"""
    metadata = sa.MetaData()
    
    # Définir la table des activités
    activities_table = sa.Table(
        "activities", metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("activity_id", sa.BigInteger, unique=True),
        sa.Column("activity_name", sa.String(255)),
        sa.Column("activity_type", sa.String(50)),
        sa.Column("start_time", sa.String(50)),  # Stocké comme string pour plus de simplicité
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
        sa.Column("created_timestamp", sa.String(50))  # Stocké comme string pour plus de simplicité
    )

    gps_data = sa.Table(
        "gps_data",metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("activity_id", sa.Integer, sa.ForeignKey("activities.id")),
        sa.Column("latitude", sa.Float),
        sa.Column("longitude", sa.Float),
        sa.Column("timestamp", sa.DateTime),
    )

    
    metadata.create_all(engine)
    return {"activities": activities_table,
            "gps_data": gps_data}

def store_activities_in_db(engine, tables, processed_data):
    """Stocke les activités dans la base de données"""
    with engine.connect() as conn:
        for activity in processed_data:
            # Vérifier si l'activité existe déjà
            select_stmt = sa.select(tables["activities"]).where(
                tables["activities"].c.activity_id == activity["activity_id"]
            )
            result = conn.execute(select_stmt).fetchone()
            
            if result is None:
                # Insérer une nouvelle activité
                insert_stmt = tables["activities"].insert().values(**activity)
                conn.execute(insert_stmt)
                conn.commit()
                print(f"Activité {activity['activity_id']} ajoutée à la base de données")
            else:
                print(f"Activité {activity['activity_id']} déjà présente dans la base de données")

def get_activities_from_db(engine, tables, limit=10, offset=0):
    """Récupère les activités depuis la base de données"""
    with engine.connect() as conn:
        select_stmt = sa.select(tables["activities"]).limit(limit).offset(offset)
        result = conn.execute(select_stmt).fetchall()
        return result

def get_activity_by_id(engine, tables, activity_id):
    """Récupère une activité spécifique par son ID"""
    with engine.connect() as conn:
        select_stmt = sa.select(tables["activities"]).where(
            tables["activities"].c.activity_id == activity_id
        )
        result = conn.execute(select_stmt).fetchone()
        return result