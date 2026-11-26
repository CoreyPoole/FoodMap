"""Five parameterized SQL queries."""
import pandas as pd

FRESH_COUNT = "COUNT(CASE WHEN st.sells_fresh_produce = 1 THEN 1 END)"
Q1_SQL = f"""
SELECT a.area_id, a.zip_code, a.county, a.population, a.median_income, a.poverty_rate,
       {FRESH_COUNT} AS fresh_stores,
       ROUND({FRESH_COUNT} * 10000.0 / a.population, 2) AS fresh_stores_per_10k
FROM Areas a
LEFT JOIN Stores s ON s.area_id = a.area_id
LEFT JOIN StoreTypes st ON st.type_id = s.type_id
WHERE a.median_income < :max_income
GROUP BY a.area_id
HAVING {FRESH_COUNT} * 10000.0 / a.population < :max_per_10k
ORDER BY fresh_stores_per_10k, a.median_income
"""
Q2_SQL = """
SELECT a.area_id, a.zip_code, a.county, a.population, a.pct_households_no_vehicle,
       (SELECT COUNT(*) FROM TransitStops t WHERE t.area_id = a.area_id) AS transit_stops,
       (SELECT COUNT(*) FROM Stores s JOIN StoreTypes st ON st.type_id = s.type_id
         WHERE s.area_id = a.area_id AND st.sells_fresh_produce = 1) AS fresh_stores_in_area
FROM Areas a
WHERE a.pct_households_no_vehicle > :min_pct_no_vehicle
  AND NOT EXISTS (
        SELECT 1 FROM Stores s
        JOIN StoreTypes st ON st.type_id = s.type_id
        JOIN StoreStopAccess x ON x.store_id = s.store_id
        WHERE s.area_id = a.area_id AND st.sells_fresh_produce = 1
          AND x.walk_distance_m <= :max_walk_m)
ORDER BY a.pct_households_no_vehicle DESC
"""
Q3_SQL = """
SELECT s.store_id, s.name, s.address, a.zip_code, st.type_name,
       t.stop_name AS nearest_stop, MIN(x.walk_distance_m) AS walk_distance_m
FROM Stores s
JOIN Areas a ON a.area_id = s.area_id
JOIN StoreTypes st ON st.type_id = s.type_id
JOIN StoreStopAccess x ON x.store_id = s.store_id
JOIN TransitStops t ON t.stop_id = x.stop_id
WHERE s.accepts_snap = 1 AND x.walk_distance_m <= :max_walk_m
  AND (:zip = '' OR a.zip_code = :zip)
GROUP BY s.store_id
ORDER BY walk_distance_m, s.name
"""
Q4_SQL = """
SELECT RANK() OVER (ORDER BY pct_fresh DESC) AS rank_by_fresh_share, *
FROM (
    SELECT a.county, COUNT(*) AS total_stores,
           SUM(st.type_name = 'supermarket') AS supermarkets,
           SUM(st.type_name IN ('convenience store', 'dollar store')) AS convenience_or_dollar,
           SUM(st.sells_fresh_produce) AS fresh_stores,
           ROUND(100.0 * SUM(st.type_name = 'supermarket') / COUNT(*), 1) AS pct_supermarket,
           ROUND(100.0 * SUM(st.type_name IN ('convenience store', 'dollar store')) / COUNT(*), 1)
               AS pct_convenience_or_dollar,
           ROUND(100.0 * SUM(st.sells_fresh_produce) / COUNT(*), 1) AS pct_fresh
    FROM Stores s
    JOIN Areas a ON a.area_id = s.area_id
    JOIN StoreTypes st ON st.type_id = s.type_id
    GROUP BY a.county
    HAVING COUNT(*) >= :min_stores
)
ORDER BY rank_by_fresh_share, county
"""
Q5_SQL = f"""
WITH density AS (
    SELECT a.area_id, a.zip_code, a.county, a.population, a.poverty_rate,
           a.pct_households_no_vehicle,
           {FRESH_COUNT} * 10000.0 / a.population AS fresh_per_10k
    FROM Areas a
    LEFT JOIN Stores s ON s.area_id = a.area_id
    LEFT JOIN StoreTypes st ON st.type_id = s.type_id
    GROUP BY a.area_id
)
SELECT area_id, zip_code, county, population, poverty_rate, pct_households_no_vehicle,
       ROUND(fresh_per_10k, 2) AS fresh_stores_per_10k,
       ROUND(:w_poverty * poverty_rate + :w_vehicle * pct_households_no_vehicle
           + :w_stores * 100.0 * MAX(0.0, 1.0 - fresh_per_10k / :ref_density), 1) AS access_gap_score
FROM density
ORDER BY access_gap_score DESC, area_id
LIMIT :top_n
"""
DEFAULT_WEIGHTS = {"w_poverty": 0.4, "w_vehicle": 0.3, "w_stores": 0.3}
DEFAULT_REF_DENSITY = 4.0

def _run(conn, sql, params):
    return pd.read_sql_query(sql, conn, params=params)

def food_desert_candidates(conn, max_income, max_per_10k):
    return _run(conn, Q1_SQL, {"max_income": max_income, "max_per_10k": max_per_10k})

def no_vehicle_no_walkable_fresh(conn, min_pct_no_vehicle, max_walk_m):
    return _run(conn, Q2_SQL, {"min_pct_no_vehicle": min_pct_no_vehicle, "max_walk_m": max_walk_m})

def snap_stores_near_transit(conn, max_walk_m, zip_code=""):
    return _run(conn, Q3_SQL, {"max_walk_m": max_walk_m, "zip": (zip_code or "").strip()})

def store_mix_by_county(conn, min_stores=1):
    return _run(conn, Q4_SQL, {"min_stores": min_stores})

def access_gap_ranking(conn, top_n, ref_density=DEFAULT_REF_DENSITY, **weights):
    return _run(conn, Q5_SQL, {**DEFAULT_WEIGHTS, **weights, "ref_density": ref_density, "top_n": int(top_n)})
