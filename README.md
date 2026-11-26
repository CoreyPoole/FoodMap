# FoodMap: A Food Access Tracker for Detecting Food Deserts

CSCI 3304 Term Project (Data for Breaking Barriers) · Alexis Roel & Corey Poole

FoodMap combines food retailer locations, transit stops, SNAP acceptance and neighborhood demographics in a SQLite database with a Streamlit interface.

## Run locally

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

The application generates reproducible synthetic sample data and initializes the SQLite database on first launch. No actual USDA, ACS, GTFS or OpenStreetMap records have been imported. To reset the sample database, run `python3 load_data.py --regenerate`. To run tests, use `python3 -m pytest -q`.

## Features

- Five normalized relational tables with foreign keys and integrity checks.
- Full CRUD for Areas and Stores.
- Five parameterized analytical queries and CSV downloads.
- Store and food-desert maps and access-gap charts.

Walking distance is estimated using haversine distance times 1.3, not measured pedestrian routes. The food-desert candidates and access-gap scores are screening indicators, not official USDA classifications.

To use real data, replace the CSVs in `data/` with matching columns (see `generate_sample_data.py` and `load_data.py`), then run `python3 load_data.py`.
