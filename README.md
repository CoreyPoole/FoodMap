# FoodMap: A Food Access Tracker for Detecting Food Deserts
CSCI 3304 Term Project (Data for Breaking Barriers) · Alexis Roel and Corey Poole

FoodMap uses SQLite and Streamlit to identify possible food-access gaps caused by income, store availability and transportation barriers.

## Start the application (macOS / Linux)
Use Python 3.11 or 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The default app builds a reproducible synthetic demonstration database on first launch. No Internet connection is needed after installing dependencies. This is a demonstration, not a real assessment.

## Real data: San Antonio-area counties
The application includes a public-source importer for Bexar, Comal and Guadalupe counties, using the 2020–2024 ACS 5-year estimates, 2024 Census tract boundaries, 2020 ZCTA boundaries, USDA SNAP retailer authorization records as of December 31, 2025, VIA GTFS stops, and the 2025 USDA Food Access Research Atlas SRAM.

Read [VIA's developer license](https://www.viainfo.net/developers-license-agreement/) first. If you accept its terms, run:

```bash
python import_real_data.py --accept-via-terms
FOODMAP_DB=foodmap_real.db python -m streamlit run app.py
```

The importer downloads source files to raw_data/, converts them into CSVs under real_data/, and builds foodmap_real.db and a source manifest. A Census API key is not required. Downloads can be large. If a provider changes or blocks its URL, obtain the corresponding official source file listed in import_real_data.py, save it under the matching filename in raw_data/, and rerun. Existing cached files are reused. A failed or incomplete import must not be treated as real data. The importer refuses to overwrite an existing database.

See [data_sources.md](data_sources.md) for exact source definitions and limitations. Imported data covers SNAP retailers only. Fresh-produce availability is inferred from store type; ZIPs approximate tract locations. Walking distances are estimates. USDA atlas records are retained as a separate reference CSV rather than changing the five-table proposal schema. OpenStreetMap was optional and is not included. The full public-source import and Streamlit startup succeeded on macOS on November 25, 2026. The local automated suite reported 34 passed in 2.90 seconds. See [data_sources.md](data_sources.md) for the observed import counts.

## Project requirements

| Requirement | Implementation |
|---|---|
| Five normalized relational tables | schema.sql |
| Full Stores and Areas CRUD | crud.py and Manage Data |
| Low-income, low fresh-store density | Query 1 |
| High no-vehicle rate with no walkable produce store | Query 2 |
| SNAP stores near transit, filtered by area ZIP | Query 3 |
| Store-type mix by county | Query 4 |
| Top N access-gap areas | Query 5 |
| Extra-credit maps and charts | Map & Charts |
| Public-source processing | import_real_data.py |
| ER diagram, normalization, demo sequence | [project_design.md](project_design.md) |

All analytical queries use bound SQL parameters; the results can be exported as CSV. Stores and Areas support validated creation, search, editing and deletion. A store's walking links are recomputed when its coordinates change. A store deletion cascades to walking links; deleting an area with dependent stores or stops is restricted.

## Test and reset

```bash
python -m pytest -q
```

The suite includes query tests, CRUD and integrity checks, an offline source-import integration test and smoke tests for every Streamlit page. Streamlit smoke tests require Streamlit to be installed.

Reset the synthetic demo only (this replaces existing demo edits):

```bash
python load_data.py --regenerate
```

See [project_design.md](project_design.md) for the demonstration checklist. Do not submit synthetic results as factual findings. The final course rubric was not provided; confirm submission requirements beyond the approved proposal with the instructor.
