PRAGMA foreign_keys = ON;
CREATE TABLE Areas (
    area_id INTEGER PRIMARY KEY,
    zip_code TEXT NOT NULL CHECK (length(zip_code) = 5),
    county TEXT NOT NULL,
    population INTEGER NOT NULL CHECK (population > 0),
    median_income REAL NOT NULL CHECK (median_income >= 0),
    poverty_rate REAL NOT NULL CHECK (poverty_rate BETWEEN 0 AND 100),
    pct_households_no_vehicle REAL NOT NULL CHECK (pct_households_no_vehicle BETWEEN 0 AND 100)
);
CREATE TABLE StoreTypes (
    type_id INTEGER PRIMARY KEY,
    type_name TEXT NOT NULL UNIQUE,
    sells_fresh_produce INTEGER NOT NULL CHECK (sells_fresh_produce IN (0, 1))
);
CREATE TABLE Stores (
    store_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    latitude REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    accepts_snap INTEGER NOT NULL CHECK (accepts_snap IN (0, 1)),
    area_id INTEGER NOT NULL REFERENCES Areas(area_id) ON DELETE RESTRICT,
    type_id INTEGER NOT NULL REFERENCES StoreTypes(type_id) ON DELETE RESTRICT
);
CREATE TABLE TransitStops (
    stop_id INTEGER PRIMARY KEY,
    stop_name TEXT NOT NULL,
    latitude REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    area_id INTEGER NOT NULL REFERENCES Areas(area_id) ON DELETE RESTRICT
);
CREATE TABLE StoreStopAccess (
    store_id INTEGER NOT NULL REFERENCES Stores(store_id) ON DELETE CASCADE,
    stop_id INTEGER NOT NULL REFERENCES TransitStops(stop_id) ON DELETE CASCADE,
    walk_distance_m REAL NOT NULL CHECK (walk_distance_m >= 0),
    PRIMARY KEY (store_id, stop_id)
);
CREATE INDEX idx_stores_area ON Stores(area_id);
CREATE INDEX idx_stores_type ON Stores(type_id);
CREATE INDEX idx_stops_area ON TransitStops(area_id);
CREATE INDEX idx_access_stop ON StoreStopAccess(stop_id);
CREATE INDEX idx_access_walk ON StoreStopAccess(walk_distance_m);
