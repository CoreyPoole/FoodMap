"""Validated CRUD for Stores and Areas."""
import math
import re
import sqlite3
import pandas as pd
from geo import MAX_WALK_M, walking_distance_m

class ValidationError(ValueError):
    """User-correctable input or constraint error."""

def _text(v, label):
    v = (v or "").strip()
    if not v:
        raise ValidationError(f"{label} is required.")
    return v

def _num(v, label, lo=None, hi=None, integer=False):
    try:
        n = int(v) if integer else float(v)
    except (TypeError, ValueError, OverflowError):
        raise ValidationError(f"{label} must be a number.")
    if not math.isfinite(n) or (integer and float(v) != n):
        raise ValidationError(f"{label} must be a finite valid number.")
    if (lo is not None and n < lo) or (hi is not None and n > hi):
        raise ValidationError(f"{label} is outside the allowed range.")
    return n

def _clean_store(f):
    return {
        "name": _text(f.get("name"), "Name"),
        "address": _text(f.get("address"), "Address"),
        "latitude": _num(f.get("latitude"), "Latitude", -90, 90),
        "longitude": _num(f.get("longitude"), "Longitude", -180, 180),
        "accepts_snap": 1 if f.get("accepts_snap") else 0,
        "area_id": _num(f.get("area_id"), "Area", integer=True),
        "type_id": _num(f.get("type_id"), "Store type", integer=True),
    }

def _clean_area(f):
    zip_code = _text(f.get("zip_code"), "ZIP code")
    if not re.fullmatch(r"\d{5}", zip_code):
        raise ValidationError("ZIP code must be exactly 5 digits.")
    return {
        "zip_code": zip_code,
        "county": _text(f.get("county"), "County"),
        "population": _num(f.get("population"), "Population", 1, integer=True),
        "median_income": _num(f.get("median_income"), "Median income", 0),
        "poverty_rate": _num(f.get("poverty_rate"), "Poverty rate (%)", 0, 100),
        "pct_households_no_vehicle": _num(f.get("pct_households_no_vehicle"),
                                          "Households without a vehicle (%)", 0, 100),
    }

def store_types(conn):
    return pd.read_sql_query("SELECT * FROM StoreTypes ORDER BY type_id", conn)

def area_options(conn):
    return pd.read_sql_query(
        "SELECT area_id, zip_code || ' · ' || county || ' (#' || area_id || ')' AS label "
        "FROM Areas ORDER BY zip_code, area_id", conn)

def list_stores(conn, search=""):
    sql = """SELECT s.store_id, s.name, s.address, st.type_name, a.zip_code, a.county,
                    s.accepts_snap, s.latitude, s.longitude
             FROM Stores s JOIN StoreTypes st ON st.type_id = s.type_id
                           JOIN Areas a ON a.area_id = s.area_id
             WHERE s.name LIKE :q OR s.address LIKE :q OR a.zip_code LIKE :q OR st.type_name LIKE :q
             ORDER BY s.store_id"""
    return pd.read_sql_query(sql, conn, params={"q": f"%{search.strip()}%"})

def get_store(conn, store_id):
    row = conn.execute("SELECT * FROM Stores WHERE store_id = ?", (store_id,)).fetchone()
    return dict(row) if row else None

def refresh_store_access(conn, store_id, max_walk_m=MAX_WALK_M):
    row = conn.execute("SELECT latitude, longitude FROM Stores WHERE store_id = ?", (store_id,)).fetchone()
    conn.execute("DELETE FROM StoreStopAccess WHERE store_id = ?", (store_id,))
    if row is None:
        return 0
    rows = []
    for stop in conn.execute("SELECT stop_id, latitude, longitude FROM TransitStops"):
        d = walking_distance_m(row[0], row[1], stop[1], stop[2])
        if d <= max_walk_m:
            rows.append((store_id, stop[0], d))
    conn.executemany("INSERT INTO StoreStopAccess VALUES (?, ?, ?)", rows)
    return len(rows)

def create_store(conn, **fields):
    v = _clean_store(fields)
    try:
        cur = conn.execute(
            "INSERT INTO Stores (name, address, latitude, longitude, accepts_snap, area_id, type_id) "
            "VALUES (:name, :address, :latitude, :longitude, :accepts_snap, :area_id, :type_id)", v)
        refresh_store_access(conn, cur.lastrowid)
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValidationError(f"Could not add store: {e}")
    return cur.lastrowid

def update_store(conn, store_id, **fields):
    v = _clean_store(fields)
    try:
        cur = conn.execute(
            "UPDATE Stores SET name=:name, address=:address, latitude=:latitude, longitude=:longitude, "
            "accepts_snap=:accepts_snap, area_id=:area_id, type_id=:type_id WHERE store_id=:id",
            {**v, "id": store_id})
        if cur.rowcount == 0:
            raise ValidationError("That store no longer exists.")
        refresh_store_access(conn, store_id)
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValidationError(f"Could not update store: {e}")

def delete_store(conn, store_id):
    cur = conn.execute("DELETE FROM Stores WHERE store_id = ?", (store_id,))
    conn.commit()
    if cur.rowcount == 0:
        raise ValidationError("That store no longer exists.")

def list_areas(conn, search=""):
    sql = """SELECT a.*, (SELECT COUNT(*) FROM Stores s WHERE s.area_id = a.area_id) AS stores,
                    (SELECT COUNT(*) FROM TransitStops t WHERE t.area_id = a.area_id) AS transit_stops
             FROM Areas a WHERE a.zip_code LIKE :q OR a.county LIKE :q ORDER BY a.area_id"""
    return pd.read_sql_query(sql, conn, params={"q": f"%{search.strip()}%"})

def get_area(conn, area_id):
    row = conn.execute("SELECT * FROM Areas WHERE area_id = ?", (area_id,)).fetchone()
    return dict(row) if row else None

def create_area(conn, **fields):
    v = _clean_area(fields)
    try:
        cur = conn.execute(
            "INSERT INTO Areas (zip_code, county, population, median_income, poverty_rate, "
            "pct_households_no_vehicle) VALUES (:zip_code, :county, :population, :median_income, "
            ":poverty_rate, :pct_households_no_vehicle)", v)
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValidationError(f"Could not add area: {e}")
    return cur.lastrowid

def update_area(conn, area_id, **fields):
    v = _clean_area(fields)
    try:
        cur = conn.execute(
            "UPDATE Areas SET zip_code=:zip_code, county=:county, population=:population, "
            "median_income=:median_income, poverty_rate=:poverty_rate, "
            "pct_households_no_vehicle=:pct_households_no_vehicle WHERE area_id=:id", {**v, "id": area_id})
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValidationError(f"Could not update area: {e}")
    if cur.rowcount == 0:
        raise ValidationError("That area no longer exists.")

def delete_area(conn, area_id):
    stores = conn.execute("SELECT COUNT(*) FROM Stores WHERE area_id = ?", (area_id,)).fetchone()[0]
    stops = conn.execute("SELECT COUNT(*) FROM TransitStops WHERE area_id = ?", (area_id,)).fetchone()[0]
    if stores or stops:
        raise ValidationError(f"This area still has {stores} store(s) and {stops} transit stop(s). Delete or reassign them first.")
    cur = conn.execute("DELETE FROM Areas WHERE area_id = ?", (area_id,))
    conn.commit()
    if cur.rowcount == 0:
        raise ValidationError("That area no longer exists.")
