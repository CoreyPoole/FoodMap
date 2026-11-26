import streamlit as st
import queries
import ui

conn = ui.setup("2 · No-vehicle gaps", "Areas with high no-vehicle rates and no fresh-produce store within walking distance of a transit stop.")

with st.form("q2_sql"):
    pct = st.number_input("Households without a vehicle above (%)", 0.0, 100.0, 10.0, 0.5)
    walk = st.number_input("Walking distance (meters)", 50, 2000, 800, 50)
    st.form_submit_button("Run query", type="primary")
df = queries.no_vehicle_no_walkable_fresh(conn, pct, walk)
st.subheader(f"{len(df)} matching record(s)")
if df.empty:
    st.info("No records match. Adjust the parameters and run again.")
else:
    st.dataframe(df, hide_index=True)
    st.download_button("Download CSV", df.to_csv(index=False), "no_vehicle_gaps.csv", "text/csv")
st.caption("Walking distance is estimated as straight-line distance × 1.3 (max stored: 2,000 m).")
ui.show_sql(queries.Q2_SQL)
