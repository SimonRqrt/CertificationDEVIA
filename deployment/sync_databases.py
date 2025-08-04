#!/usr/bin/env python3
"""
Script de synchronisation entre SQLite local et Supabase PostgreSQL
Utile pour maintenir la cohérence entre développement et production
"""

import os
import sys
import sqlite3
import psycopg2
from pathlib import Path

def load_env_vars():
    """Charge les variables d'environnement"""
    env_file = Path(__file__).parent.parent / '.env'
    
    if not env_file.exists():
        print("❌ Fichier .env introuvable")
        return False
        
    with open(env_file, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value
    
    return True

def get_sqlite_connection():
    """Connexion SQLite locale"""
    db_path = Path(__file__).parent.parent / 'data' / 'django_garmin_data.db'
    
    if not db_path.exists():
        print(f"❌ Base SQLite introuvable: {db_path}")
        return None
    
    return sqlite3.connect(str(db_path))

def get_postgresql_connection():
    """Connexion PostgreSQL Supabase"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL non définie")
            return None
            
        return psycopg2.connect(database_url)
    except Exception as e:
        print(f"❌ Erreur connexion PostgreSQL: {e}")
        return None

def compare_databases():
    """Compare les données entre SQLite et PostgreSQL"""
    print("\n=== COMPARAISON BASES DE DONNÉES ===")
    
    sqlite_conn = get_sqlite_connection()
    pg_conn = get_postgresql_connection()
    
    if not sqlite_conn or not pg_conn:
        return False
    
    try:
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        # Tables à comparer
        tables = [
            'activities_activity',
            'auth_user',
            'coaching_trainingplan',
            'coaching_goal'
        ]
        
        comparison = {}
        
        for table in tables:
            try:
                # Count SQLite
                sqlite_cursor.execute(f'SELECT COUNT(*) FROM {table}')
                sqlite_count = sqlite_cursor.fetchone()[0]
                
                # Count PostgreSQL
                pg_cursor.execute(f'SELECT COUNT(*) FROM {table}')
                pg_count = pg_cursor.fetchone()[0]
                
                comparison[table] = {
                    'sqlite': sqlite_count,
                    'postgresql': pg_count,
                    'diff': pg_count - sqlite_count
                }
                
                status = "✅" if sqlite_count == pg_count else "⚠️"
                print(f"{status} {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")
                
            except Exception as e:
                print(f"❌ Erreur table {table}: {e}")
                comparison[table] = {'error': str(e)}
        
        return comparison
        
    finally:
        sqlite_conn.close()
        pg_conn.close()

def sync_sqlite_to_postgresql():
    """Synchronise SQLite vers PostgreSQL (données manquantes)"""
    print("\n=== SYNCHRONISATION SQLite → PostgreSQL ===")
    
    sqlite_conn = get_sqlite_connection()
    pg_conn = get_postgresql_connection()
    
    if not sqlite_conn or not pg_conn:
        return False
    
    try:
        sqlite_cursor = sqlite_conn.cursor()
        pg_cursor = pg_conn.cursor()
        
        # Synchroniser les activités (exemple)
        print("Synchronisation activités...")
        
        # Récupérer les activités SQLite pas encore dans PostgreSQL
        sqlite_cursor.execute("""
            SELECT id, activity_id, name, start_time, total_distance, 
                   avg_heart_rate, max_heart_rate, avg_speed, max_speed,
                   calories, created_at, updated_at
            FROM activities_activity 
            ORDER BY id DESC LIMIT 10
        """)
        
        sqlite_activities = sqlite_cursor.fetchall()
        
        synced = 0
        for activity in sqlite_activities:
            try:
                # Vérifier si l'activité existe déjà
                pg_cursor.execute(
                    "SELECT id FROM activities_activity WHERE activity_id = %s",
                    (activity[1],)
                )
                
                if not pg_cursor.fetchone():
                    # Insérer l'activité
                    pg_cursor.execute("""
                        INSERT INTO activities_activity 
                        (activity_id, name, start_time, total_distance, 
                         avg_heart_rate, max_heart_rate, avg_speed, max_speed,
                         calories, created_at, updated_at, user_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
                    """, activity[1:-1])  # Exclure id et ajouter user_id=1
                    
                    synced += 1
                    
            except Exception as e:
                print(f"⚠️ Erreur sync activité {activity[0]}: {e}")
        
        pg_conn.commit()
        print(f"✅ {synced} activités synchronisées")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur synchronisation: {e}")
        return False
        
    finally:
        sqlite_conn.close()
        pg_conn.close()

def backup_postgresql():
    """Sauvegarde PostgreSQL vers SQLite (rollback)"""
    print("\n=== SAUVEGARDE PostgreSQL → SQLite ===")
    
    sqlite_conn = get_sqlite_connection()
    pg_conn = get_postgresql_connection()
    
    if not sqlite_conn or not pg_conn:
        return False
    
    try:
        # Exemple : sauvegarder les plans d'entraînement
        pg_cursor = pg_conn.cursor()
        sqlite_cursor = sqlite_conn.cursor()
        
        pg_cursor.execute("""
            SELECT id, name, description, duration_weeks, difficulty_level,
                   goal_type, created_at, updated_at, user_id
            FROM coaching_trainingplan
            ORDER BY created_at DESC
        """)
        
        plans = pg_cursor.fetchall()
        backed_up = 0
        
        for plan in plans:
            try:
                sqlite_cursor.execute("""
                    INSERT OR REPLACE INTO coaching_trainingplan
                    (id, name, description, duration_weeks, difficulty_level,
                     goal_type, created_at, updated_at, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, plan)
                backed_up += 1
                
            except Exception as e:
                print(f"⚠️ Erreur backup plan {plan[0]}: {e}")
        
        sqlite_conn.commit()
        print(f"✅ {backed_up} plans sauvegardés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur sauvegarde: {e}")
        return False
        
    finally:
        sqlite_conn.close()
        pg_conn.close()

def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        print("Usage: python3 sync_databases.py [compare|sync|backup]")
        print("  compare: Compare les deux bases")
        print("  sync: SQLite → PostgreSQL") 
        print("  backup: PostgreSQL → SQLite")
        sys.exit(1)
    
    action = sys.argv[1]
    
    print("🔄 SYNCHRONISATION BASES DE DONNÉES")
    print("=" * 40)
    
    if not load_env_vars():
        sys.exit(1)
    
    if action == 'compare':
        comparison = compare_databases()
        if comparison:
            print("\n📊 Résumé comparaison:")
            for table, data in comparison.items():
                if 'error' not in data:
                    diff = data['diff']
                    if diff > 0:
                        print(f"  ➡️ {table}: +{diff} dans PostgreSQL")
                    elif diff < 0:
                        print(f"  ⬅️ {table}: {abs(diff)} manquants dans PostgreSQL")
                    else:
                        print(f"  ✅ {table}: Synchronisé")
    
    elif action == 'sync':
        if sync_sqlite_to_postgresql():
            print("\n✅ Synchronisation terminée")
        else:
            print("\n❌ Échec synchronisation")
            sys.exit(1)
    
    elif action == 'backup':
        if backup_postgresql():
            print("\n✅ Sauvegarde terminée") 
        else:
            print("\n❌ Échec sauvegarde")
            sys.exit(1)
    
    else:
        print(f"❌ Action inconnue: {action}")
        sys.exit(1)

if __name__ == '__main__':
    main()