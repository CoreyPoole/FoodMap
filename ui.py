import json
from pathlib import Path
import streamlit as st
from db import ensure_db, get_conn, DB_PATH

def setup(title, caption=None, icon="🥕"):
    st.set_page_config(page_title=f"FoodMap – {title}", page_icon=icon, layout="wide")
    ensure_db()
    st.title(f"{icon} {title}")
    if caption:
        st.caption(caption)
    manifest_path = Path(str(DB_PATH)+".sources.json")
    if manifest_path.exists():
        meta=json.loads(manifest_path.read_text())
        st.info("Public-source dataset: "+meta["region"]+" | "+meta["acs"]+" | SNAP as of "+meta["snap_as_of"]+". Data provided by VIA Metropolitan Transit. "+meta["limitations"])
    elif DB_PATH.name=="foodmap.db":
        st.info("Synthetic demonstration data; not verified real-world food access data. See README for real-data import.")
    else:
        st.warning("Database provenance not recorded. Do not assume records are verified real-world data.")
    return get_conn()

def show_sql(sql):
    with st.expander("View the SQL for this query"):
        st.code(sql.strip(), language="sql")
