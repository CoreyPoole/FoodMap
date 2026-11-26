import streamlit as st
import queries
import ui

conn = ui.setup("1 · Food-desert candidates", "Areas with low income and few fresh-produce stores per 10,000 residents.")

with st.form("q1_sql"):
    max_income = st.number_input("Median income below ($)", 0.0, 500000.0, 40000.0, 1000.0)
    max_per_10k = st.number_input("Fresh-produce stores per 10,000 residents below", 0.0, 100.0, 2.0, 0.25)
    st.form_submit_button("Run query", type="primary")
df = queries.food_desert_candidates(conn, max_income, max_per_10k)
st.subheader(f"{len(df)} matching record(s)")
if df.empty:
    st.info("No records match. Adjust the parameters and run again.")
else:
    st.dataframe(df, hide_index=True)
    st.download_button("Download CSV", df.to_csv(index=False), "food_desert_candidates.csv", "text/csv")

ui.show_sql(queries.Q1_SQL)
