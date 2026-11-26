"""Build SQLite database from CSV inputs."""
import argparse
import csv
import sqlite3
from pathlib import Path
from geo import CIRCUITY, MAX_WALK_M, haversine_m

BASE = Path(__file__).parent

def init_schema(conn):
    conn.executescript((BASE / "schema.sql").read_text())

def _read(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

def _insert(conn, table, cols, rows, casts):
    data = [[cast(r[c]) for c, cast in zip(cols, casts)] for r in rows]
    conn.executemany(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})", data)

def compute_access(conn, max_walk_m=MAX_WALK_M):
    stores = conn.execute("SELECT store_id, latitude, longitude FROM Stores").fetchall()
    stops = conn.execute("SELECT stop_id, latitude, longitude FROM TransitStops").fetchall()
    rows = []
    for sid, slat, slon in stores:
        for tid, tlat, tlon in stops:
            d = round(haversine_m(slat, slon, tlat, tlon) * CIRCUITY)
            if d <= max_walk_m:
                rows.append((sid, tid, d))
    conn.executemany("INSERT INTO StoreStopAccess VALUES (?, ?, ?)", rows)
    return len(rows)

def build_database(db_path, data_dir, max_walk_m=MAX_WALK_M):
    db_path, data_dir = Path(db_path), Path(data_dir)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    init_schema(conn)
    i, f = int, float
    _insert(conn, "Areas", ["area_id", "zip_code", "county", "population", "median_income",
            "poverty_rate", "pct_households_no_vehicle"], _read(data_dir / "areas.csv"), [i, str, str, i, f, f, f])
    _insert(conn, "StoreTypes", ["type_id", "type_name", "sells_fresh_produce"],
            _read(data_dir / "store_types.csv"), [i, str, i])
    _insert(conn, "Stores", ["store_id", "name", "address", "latitude", "longitude", "accepts_snap",
            "area_id", "type_id"], _read(data_dir / "stores.csv"), [i, str, str, f, f, i, i, i])
    _insert(conn, "TransitStops", ["stop_id", "stop_name", "latitude", "longitude", "area_id"],
            _read(data_dir / "transit_stops.csv"), [i, str, f, f, i])
    access_csv = data_dir / "store_stop_access.csv"
    if access_csv.exists():
        _insert(conn, "StoreStopAccess", ["store_id", "stop_id", "walk_distance_m"], _read(access_csv), [i, i, f])
    else:
        compute_access(conn, max_walk_m)
    conn.commit()
    counts = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ["Areas", "StoreTypes", "Stores", "TransitStops", "StoreStopAccess"]}
    conn.close()
    return counts

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=str(BASE / "data"))
    ap.add_argument("--db", default=str(BASE / "foodmap.db"))
    ap.add_argument("--max-walk", type=float, default=MAX_WALK_M)
    ap.add_argument("--regenerate", action="store_true")
    a = ap.parse_args()
    if a.regenerate or not (Path(a.data_dir) / "areas.csv").exists():
        from generate_sample_data import generate
        print("Generated sample data:", generate(a.data_dir))
    print("Loaded rows:", build_database(a.db, a.data_dir, a.max_walk))
