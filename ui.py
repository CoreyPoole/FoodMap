import streamlit as st
from db import ensure_db, get_conn

def setup(title, caption=None, icon="🥕"):
    st.set_page_config(page_title=f"FoodMap – {title}", page_icon=icon, layout="wide")
    ensure_db()
    st.title(f"{icon} {title}")
    if caption:
        st.caption(caption)
    st.info("The bundled dataset is synthetic demonstration data, not verified real-world food access data.")
    return get_conn()

def show_sql(sql):
    with st.expander("View the SQL for this query"):
        st.code(sql.strip(), language="sql")
