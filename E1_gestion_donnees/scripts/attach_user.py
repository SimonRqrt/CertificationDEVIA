import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from E1_gestion_donnees.db_manager import create_db_engine, create_tables

if __name__ == "__main__":
    user_id = 1

    engine = create_db_engine()
    tables = create_tables(engine)

    with engine.connect() as conn:
        update_stmt = tables["activities"].update()\
            .where(tables["activities"].c.user_id == None)\
            .values(user_id=user_id)
        
        result = conn.execute(update_stmt)
        conn.commit()
        print(f"{result.rowcount} activités mises à jour avec user_id={user_id}.")
