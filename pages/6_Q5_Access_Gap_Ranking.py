import streamlit as st
import queries
import ui

conn = ui.setup("5 · Access-gap ranking", "Top N areas by combined poverty, vehicle access, and fresh-store density.")
d = queries.DEFAULT_WEIGHTS
with st.form("q5_sql"):
    top_n = st.number_input("Show the top N areas", 1, 500, 10, 1)
    with st.expander("Score settings"):
        w_p = st.number_input("Weight: poverty", 0.0, 1.0, d["w_poverty"], 0.05)
        w_v = st.number_input("Weight: no vehicle", 0.0, 1.0, d["w_vehicle"], 0.05)
        w_s = st.number_input("Weight: store scarcity", 0.0, 1.0, d["w_stores"], 0.05)
        ref = st.number_input("Adequate fresh stores per 10k", 0.5, 50.0, queries.DEFAULT_REF_DENSITY, 0.5)
    st.form_submit_button("Run query", type="primary")
df = queries.access_gap_ranking(conn, top_n, ref, w_poverty=w_p, w_vehicle=w_v, w_stores=w_s)
st.subheader(f"{len(df)} matching record(s)")
if df.empty:
    st.info("No records match. Adjust the parameters and run again.")
else:
    st.dataframe(df, hide_index=True)
    st.download_button("Download CSV", df.to_csv(index=False), "access_gap_ranking.csv", "text/csv")
if not df.empty:
    chart = df.assign(area=df["zip_code"] + " (#" + df["area_id"].astype(str) + ")").set_index("area")
    st.bar_chart(chart["access_gap_score"])
st.caption("Score = weighted poverty + no-vehicle percentage + fresh-store scarcity. Higher = larger gap.")
ui.show_sql(queries.Q5_SQL)
