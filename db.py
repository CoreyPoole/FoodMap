import os
import sqlite3
from pathlib import Path

BASE = Path(__file__).parent
DB_PATH = Path(os.environ.get("FOODMAP_DB", BASE / "foodmap.db"))

def get_conn(path=None):
    conn = sqlite3.connect(path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def ensure_db(path=None):
    path = Path(path or DB_PATH)
    if not path.exists():
        from generate_sample_data import generate
        from load_data import build_database
        data_dir = BASE / "data"
        if not (data_dir / "areas.csv").exists():
            generate(data_dir)
        build_database(path, data_dir)
    return path
