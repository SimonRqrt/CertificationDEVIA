
import sqlite3

def export_sqlite_to_sqlite_dump(sqlite_db_path, output_file):
    conn = sqlite3.connect(sqlite_db_path)
    with open(output_file, 'w') as f:
        for line in conn.iterdump():
            f.write(f"{line}\n")
    conn.close()
    print(f"Dump SQLite exporté dans {output_file}")

if __name__ == "__main__":
    sqlite_db_path = "data/garmin_data.db"  # Chemin vers votre base de données SQLite
    output_file = "data/garmin_data_dump.sql"  # Chemin vers le fichier de sortie
    
    export_sqlite_to_sqlite_dump(sqlite_db_path, output_file)