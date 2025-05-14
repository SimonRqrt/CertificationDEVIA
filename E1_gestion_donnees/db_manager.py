import sqlalchemy as sa
from src.config import DATABASE_URL  # Mise à jour du chemin pour config

def create_db_engine(db_url=DATABASE_URL):
    """Crée une connexion à la base de données"""
    engine = sa.create_engine(db_url)
    return engine

def create_tables(engine):
    """Crée les tables nécessaires si elles n'existent pas"""
    metadata = sa.MetaData()

    # Table des utilisateurs
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

    # Activités (déjà présentes)
    activities_table = sa.Table(
        "activities", metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.user_id")),
        sa.Column("activity_id", sa.BigInteger, unique=True),
        sa.Column("activity_name", sa.String(255)),
        sa.Column("activity_type", sa.String(50)),
        sa.Column("start_time", sa.String(50)),
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
        sa.Column("created_timestamp", sa.String(50)),
        # Données complémentaires Garmin
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

    # GPS (déjà présent)
    gps_data = sa.Table(
        "gps_data", metadata,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("activity_id", sa.Integer, sa.ForeignKey("activities.id")),
        sa.Column("latitude", sa.Float),
        sa.Column("longitude", sa.Float),
        sa.Column("timestamp", sa.DateTime)
    )

    # Table des métriques calculées
    metrics = sa.Table(
        "metrics", metadata,
        sa.Column("metrics_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.user_id")),
        sa.Column("date_calcul", sa.String(50)),
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

    metadata.create_all(engine)

    return {
        "users": users,
        "activities": activities_table,
        "gps_data": gps_data,
        "metrics": metrics
    }

def insert_user(engine, tables, user_data):
    """Insère un nouvel utilisateur dans la table users"""
    with engine.connect() as conn:
        try:
            insert_stmt = tables["users"].insert().values(**user_data)
            conn.execute(insert_stmt)
            conn.commit()
            print(f"Utilisateur {user_data.get('prenom', '')} {user_data.get('nom', '')} inséré avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'insertion de l'utilisateur : {e}")


def store_activities_in_db(engine, tables, processed_data):
    """Stocke les activités dans la base de données"""
    print(f"Début du stockage de {len(processed_data)} activités")
    inserted_count = 0
    skipped_count = 0
    
    with engine.connect() as conn:
        for activity in processed_data:
            # Vérifier si l'activité existe déjà
            select_stmt = sa.select(tables["activities"]).where(
                tables["activities"].c.activity_id == activity["activity_id"]
            )
            result = conn.execute(select_stmt).fetchone()
            
            if result is None:
                # Insérer une nouvelle activité
                try:
                    insert_stmt = tables["activities"].insert().values(**activity)
                    conn.execute(insert_stmt)
                    conn.commit()
                    inserted_count += 1
                    print(f"Activité {activity['activity_id']} ({activity['start_time']}) ajoutée")
                except Exception as e:
                    print(f"Erreur lors de l'insertion de l'activité {activity['activity_id']}: {e}")
            else:
                skipped_count += 1
                print(f"Activité {activity['activity_id']} déjà présente (date: {activity['start_time']})")
    
    print(f"Stockage terminé: {inserted_count} activités ajoutées, {skipped_count} ignorées")

def get_activities_from_db(engine, tables, limit=10, offset=0):
    """Récupère les activités depuis la base de données"""
    with engine.connect() as conn:
        # Ajouter ORDER BY start_time DESC pour trier par date décroissante
        select_stmt = sa.select(tables["activities"]) \
            .order_by(sa.desc(tables["activities"].c.start_time)) \
            .limit(limit) \
            .offset(offset)
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
