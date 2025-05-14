import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from E1_gestion_donnees.data_manager import fetch_and_process_garmin_data

if __name__ == "__main__":
    user_id = 1
    fetch_and_process_garmin_data(user_id)
