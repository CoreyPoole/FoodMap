import pandas as pd
import streamlit as st
import queries
import ui

conn = ui.setup("Map & Charts", "Explore store locations, food-desert candidates, and access-gap rankings.", icon="📍")
stores = pd.read_sql_query(
    "SELECT s.latitude, s.longitude, st.sells_fresh_produce AS fresh FROM Stores s "
    "JOIN StoreTypes st ON st.type_id = s.type_id", conn)
stores["color"] = stores["fresh"].map({1: "#2e9e4f", 0: "#d9531e"})
st.subheader("Stores")
st.caption("Green = fresh produce · Orange = no fresh produce")
if not stores.empty:
    st.map(stores, latitude="latitude", longitude="longitude", color="color", size=60)
else:
    st.info("No stores to map.")
centroids = pd.read_sql_query(
    "SELECT area_id, AVG(latitude) AS latitude, AVG(longitude) AS longitude FROM "
    "(SELECT area_id, latitude, longitude FROM Stores UNION ALL "
    " SELECT area_id, latitude, longitude FROM TransitStops) GROUP BY area_id", conn)
st.subheader("Food-desert candidates (Query 1)")
c1, c2 = st.columns(2)
income = c1.number_input("Median income below ($)", 0.0, 500000.0, 40000.0, 1000.0)
density = c2.number_input("Fresh stores per 10,000 below", 0.0, 100.0, 2.0, 0.25)
candidates = queries.food_desert_candidates(conn, income, density)
pts = candidates.merge(centroids, on="area_id")
st.caption(f"{len(candidates)} candidates; {len(pts)} can be mapped using average store/stop coordinates. Markers are approximate centers, not area boundaries or USDA classifications.")
if not pts.empty:
    st.map(pts, latitude="latitude", longitude="longitude", size=180, color="#c0152f")
else:
    st.info("No candidates with location data to map.")
st.dataframe(candidates, hide_index=True)
ui.show_sql(queries.Q1_SQL)
st.subheader("Highest access-gap areas (Query 5)")
top_n = st.slider("Areas to highlight", 3, 30, 10)
gap = queries.access_gap_ranking(conn, top_n)
if not gap.empty:
    chart = gap.assign(area=gap["zip_code"] + " (#" + gap["area_id"].astype(str) + ")").set_index("area")
    st.bar_chart(chart["access_gap_score"])
else:
    st.info("No areas to rank.")
ui.show_sql(queries.Q5_SQL)
