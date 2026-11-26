import json
from pathlib import Path
import pandas as pd
import streamlit as st
import ui
from db import DB_PATH

conn = ui.setup("FoodMap", "A food access tracker for detecting food deserts · CSCI 3304 Term Project", icon="🗺️")
st.markdown("FoodMap combines store locations, store types, SNAP acceptance, transit stops, and neighborhood demographics in one relational database to identify access gaps.")
for col, (label, table) in zip(st.columns(4), [("Areas", "Areas"), ("Stores", "Stores"),
                ("Transit stops", "TransitStops"), ("Store–stop walking links", "StoreStopAccess")]):
    col.metric(label, f"{conn.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]:,}")
st.subheader("Pages (sidebar)")
st.markdown("""
- **Manage Data** – add, edit, and delete Stores and Areas
- **1 · Food-desert candidates** – low income and few fresh-produce stores
- **2 · No-vehicle gaps** – no walkable fresh-produce stores
- **3 · SNAP near transit** – SNAP stores near stops, by area ZIP
- **4 · Store mix by county** – supermarket vs. convenience/dollar
- **5 · Access-gap ranking** – top N areas by combined access-gap score
- **Map & Charts** – store and food-desert maps and gap-score charts
""")
manifest = Path(str(DB_PATH)+".sources.json")
if manifest.exists():
    with st.expander("Data sources and USDA Atlas reference"):
        meta = json.loads(manifest.read_text())
        st.json(meta)
        atlas = Path(meta["atlas_reference"])
        if atlas.exists():
            st.dataframe(pd.read_csv(atlas, dtype=str), hide_index=True)
            st.download_button("Download USDA Atlas reference CSV", atlas.read_bytes(), "usda_atlas_reference.csv", "text/csv")
        else:
            st.warning("Atlas reference CSV was moved or is missing.")
        st.caption("Official Atlas indicators are separate from FoodMap's custom estimates.")
conn.close()
