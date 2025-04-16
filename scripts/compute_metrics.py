import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.data_manager import compute_metrics

if __name__ == "__main__":
    compute_metrics(user_id=1)
