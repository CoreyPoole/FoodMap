import streamlit as st
import queries
import ui

conn = ui.setup("3 · SNAP stores near transit", "SNAP-accepting stores within walking distance of a stop, optionally filtered by ZIP.")
zips = [r[0] for r in conn.execute("SELECT DISTINCT zip_code FROM Areas ORDER BY zip_code")]
with st.form("q3_sql"):
    walk = st.number_input("Walking distance (meters)", 50, 2000, 500, 50)
    zip_code = st.selectbox("ZIP code", [""] + zips, format_func=lambda z: z or "All ZIP codes")
    st.form_submit_button("Run query", type="primary")
df = queries.snap_stores_near_transit(conn, walk, zip_code)
st.subheader(f"{len(df)} matching record(s)")
if df.empty:
    st.info("No records match. Adjust the parameters and run again.")
else:
    st.dataframe(df, hide_index=True)
    st.download_button("Download CSV", df.to_csv(index=False), "snap_near_transit.csv", "text/csv")

ui.show_sql(queries.Q3_SQL)
