import streamlit as st
import ui

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
- **3 · SNAP near transit** – SNAP stores near stops, by ZIP
- **4 · Store mix by county** – supermarket vs. convenience/dollar
- **5 · Access-gap ranking** – top N areas by combined access-gap score
- **Map & Charts** – store and food-desert maps and gap-score charts
""")
