"""Generate synthetic sample data with a fixed seed."""
import csv
import math
import random
from pathlib import Path

SEED = 3304
COLS, ROWS = 9, 7
LAT0, LON0 = 40.00, -100.00
CELL_LAT, CELL_LON = 0.020, 0.026
COUNTIES = ["Alder County", "Birch County", "Cedar County"]
STREETS = ["Oak", "Maple", "Pine", "Elm", "Cedar", "Lake", "Hill", "Park", "Mill", "River"]
STORE_TYPES = [(1, "supermarket", 1), (2, "small grocery", 1), (3, "farmers market", 1),
               (4, "convenience store", 0), (5, "dollar store", 0)]
SNAP_PROB = {1: 0.95, 2: 0.85, 3: 0.35, 4: 0.55, 5: 0.80}
PREFIX = {1: "Sample Supermarket", 2: "Sample Grocery", 3: "Sample Farmers Market",
          4: "Sample Convenience", 5: "Sample Dollar Store"}

def _poisson(rng, lam):
    limit, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1

def _clamp(x, lo, hi):
    return max(lo, min(hi, x))

def _write(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)

def generate(data_dir):
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    areas, stores, stops = [], [], []
    area_id = store_id = stop_id = 0
    for idx in range(COLS * ROWS):
        col, row = idx % COLS, idx // COLS
        area_id += 1
        affluence = _clamp(rng.betavariate(2, 2), 0.02, 0.98)
        poverty = _clamp(33 - 29 * affluence + rng.gauss(0, 3), 2, 45)
        no_vehicle = _clamp(poverty * 0.55 + rng.gauss(0, 3), 0.5, 40)
        income = _clamp(21000 + affluence * 72000 + rng.gauss(0, 4000), 15000, 150000)
        population = int(rng.uniform(1500, 9000))
        areas.append([area_id, f"{99100 + idx // 3}", COUNTIES[col // 3], population,
                      round(income, -2), round(poverty, 1), round(no_vehicle, 1)])
        lat_c, lon_c = LAT0 + row * CELL_LAT, LON0 + col * CELL_LON
        counts = {
            1: _poisson(rng, 0.15 + 1.6 * affluence * population / 5000),
            2: _poisson(rng, 0.3 + 0.7 * affluence),
            3: 1 if rng.random() < 0.10 + 0.30 * affluence else 0,
            4: _poisson(rng, 1.0 + 2.0 * (1 - affluence)),
            5: _poisson(rng, 0.3 + 1.5 * (1 - affluence)),
        }
        for type_id, n in counts.items():
            for _ in range(n):
                store_id += 1
                stores.append([
                    store_id, f"{PREFIX[type_id]} {store_id:03d}",
                    f"{rng.randint(100, 9999)} {rng.choice(STREETS)} St (sample)",
                    round(lat_c + rng.uniform(-CELL_LAT / 2, CELL_LAT / 2), 6),
                    round(lon_c + rng.uniform(-CELL_LON / 2, CELL_LON / 2), 6),
                    int(rng.random() < SNAP_PROB[type_id]), area_id, type_id])
        for _ in range(1 + _poisson(rng, 3.0)):
            stop_id += 1
            stops.append([stop_id, f"Sample Stop {stop_id:03d} - {rng.choice(STREETS)} St",
                          round(lat_c + rng.uniform(-CELL_LAT / 2, CELL_LAT / 2), 6),
                          round(lon_c + rng.uniform(-CELL_LON / 2, CELL_LON / 2), 6), area_id])
    _write(data_dir / "areas.csv", ["area_id", "zip_code", "county", "population", "median_income",
           "poverty_rate", "pct_households_no_vehicle"], areas)
    _write(data_dir / "store_types.csv", ["type_id", "type_name", "sells_fresh_produce"], STORE_TYPES)
    _write(data_dir / "stores.csv", ["store_id", "name", "address", "latitude", "longitude",
           "accepts_snap", "area_id", "type_id"], stores)
    _write(data_dir / "transit_stops.csv", ["stop_id", "stop_name", "latitude", "longitude", "area_id"], stops)
    return {"areas": len(areas), "stores": len(stores), "stops": len(stops)}

if __name__ == "__main__":
    print(generate(Path(__file__).parent / "data"))
