import streamlit as st
import queries
import ui

conn = ui.setup("4 · Store mix by county", "Supermarket vs. convenience/dollar share per county, ranked by fresh-produce share.")

with st.form("q4_sql"):
    min_stores = st.number_input("Minimum stores per county", 1, 10000, 10, 1)
    st.form_submit_button("Run query", type="primary")
df = queries.store_mix_by_county(conn, min_stores)
st.subheader(f"{len(df)} matching record(s)")
if df.empty:
    st.info("No records match. Adjust the parameters and run again.")
else:
    st.dataframe(df, hide_index=True)
    st.download_button("Download CSV", df.to_csv(index=False), "store_mix.csv", "text/csv")
if not df.empty:
    st.bar_chart(df.set_index("county")[["pct_supermarket", "pct_convenience_or_dollar", "pct_fresh"]])
ui.show_sql(queries.Q4_SQL)
