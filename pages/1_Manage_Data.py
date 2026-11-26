import streamlit as st
import pandas as pd
import crud
import ui

conn = ui.setup("Manage Data", "Create, read, update, and delete Stores and Areas.", icon="🛠️")

def run(action, ok_msg, *args, **kw):
    try:
        action(conn, *args, **kw)
        st.success(ok_msg)
    except crud.ValidationError as e:
        st.error(str(e))

def store_form(prefix, d, types, areas, submit_label):
    with st.form(prefix):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name", d.get("name", ""))
        address = c2.text_input("Address", d.get("address", ""))
        c3, c4 = st.columns(2)
        lat = c3.number_input("Latitude", -90.0, 90.0, float(d.get("latitude", 40.1)), 0.0001, format="%.6f")
        lon = c4.number_input("Longitude", -180.0, 180.0, float(d.get("longitude", -99.9)), 0.0001, format="%.6f")
        type_ids = types["type_id"].tolist()
        type_names = dict(zip(types["type_id"], types["type_name"]))
        t_idx = type_ids.index(d["type_id"]) if d.get("type_id") in type_ids else 0
        type_id = st.selectbox("Store type", type_ids, t_idx, format_func=type_names.get)
        area_ids = areas["area_id"].tolist()
        area_labels = dict(zip(areas["area_id"], areas["label"]))
        a_idx = area_ids.index(d["area_id"]) if d.get("area_id") in area_ids else 0
        area_id = st.selectbox("Area", area_ids, a_idx, format_func=area_labels.get)
        snap = st.checkbox("Accepts SNAP", bool(d.get("accepts_snap", 0)))
        submitted = st.form_submit_button(submit_label, type="primary")
    return submitted, dict(name=name, address=address, latitude=lat, longitude=lon,
                           accepts_snap=snap, area_id=area_id, type_id=type_id)

def area_form(prefix, d, submit_label):
    with st.form(prefix):
        c1, c2 = st.columns(2)
        zip_code = c1.text_input("ZIP code (5 digits)", d.get("zip_code", ""))
        county = c2.text_input("County", d.get("county", ""))
        c3, c4 = st.columns(2)
        pop = c3.number_input("Population", 1, 10_000_000, int(d.get("population", 5000)), 100)
        inc = c4.number_input("Median household income ($)", 0.0, 1_000_000.0,
                              float(d.get("median_income", 45000.0)), 500.0)
        c5, c6 = st.columns(2)
        pov = c5.number_input("Poverty rate (%)", 0.0, 100.0, float(d.get("poverty_rate", 15.0)), 0.5)
        nov = c6.number_input("Households without a vehicle (%)", 0.0, 100.0,
                              float(d.get("pct_households_no_vehicle", 8.0)), 0.5)
        submitted = st.form_submit_button(submit_label, type="primary")
    return submitted, dict(zip_code=zip_code, county=county, population=pop, median_income=inc,
                           poverty_rate=pov, pct_households_no_vehicle=nov)

tab_stores, tab_areas, tab_lookup = st.tabs(["Stores", "Areas", "Read-only tables"])
with tab_stores:
    mode = st.radio("Action", ["Browse", "Add", "Edit", "Delete"], horizontal=True, key="store_mode")
    types, areas = crud.store_types(conn), crud.area_options(conn)
    if mode == "Browse":
        q = st.text_input("Search name, address, ZIP, or type", key="store_search")
        df = crud.list_stores(conn, q)
        st.caption(f"{len(df):,} store(s)")
        st.dataframe(df, hide_index=True)
    elif mode == "Add":
        if areas.empty or types.empty:
            st.info("Create an area before adding a store.")
        else:
            go, vals = store_form("store_add", {}, types, areas, "Add store")
            if go:
                run(crud.create_store, "Store added.", **vals)
    else:
        stores = crud.list_stores(conn)
        labels = {r.store_id: f"#{r.store_id} · {r.name}" for r in stores.itertuples()}
        sid = st.selectbox("Choose a store", list(labels), format_func=labels.get, key=f"store_pick_{mode}")
        if sid is not None and mode == "Edit":
            go, vals = store_form(f"store_edit_{sid}", crud.get_store(conn, sid), types, areas, "Save changes")
            if go:
                run(crud.update_store, "Store updated (walking links recalculated).", sid, **vals)
        elif sid is not None:
            st.warning("Deleting a store also removes its store–stop walking links.")
            if st.checkbox("Confirm store deletion", key=f"store_confirm_{sid}") and st.button("Delete store"):
                run(crud.delete_store, "Store deleted.", sid)

with tab_areas:
    mode = st.radio("Action", ["Browse", "Add", "Edit", "Delete"], horizontal=True, key="area_mode")
    if mode == "Browse":
        q = st.text_input("Search ZIP or county", key="area_search")
        df = crud.list_areas(conn, q)
        st.caption(f"{len(df):,} area(s)")
        st.dataframe(df, hide_index=True)
    elif mode == "Add":
        go, vals = area_form("area_add", {}, "Add area")
        if go:
            run(crud.create_area, "Area added.", **vals)
    else:
        df = crud.list_areas(conn)
        labels = {r.area_id: f"#{r.area_id} · {r.zip_code} · {r.county}" for r in df.itertuples()}
        aid = st.selectbox("Choose an area", list(labels), format_func=labels.get, key=f"area_pick_{mode}")
        if aid is not None and mode == "Edit":
            go, vals = area_form(f"area_edit_{aid}", crud.get_area(conn, aid), "Save changes")
            if go:
                run(crud.update_area, "Area updated.", aid, **vals)
        elif aid is not None:
            st.warning("An area can only be deleted when it has no stores or transit stops.")
            if st.checkbox("Confirm area deletion", key=f"area_confirm_{aid}") and st.button("Delete area"):
                run(crud.delete_area, "Area deleted.", aid)

with tab_lookup:
    for title, sql in [
        ("Store types", "SELECT * FROM StoreTypes ORDER BY type_id"),
        ("Transit stops", "SELECT * FROM TransitStops ORDER BY stop_id"),
        ("Store–stop access", "SELECT x.*, s.name AS store_name, t.stop_name FROM StoreStopAccess x JOIN Stores s USING (store_id) JOIN TransitStops t USING (stop_id) ORDER BY x.store_id, x.walk_distance_m")]:
        st.subheader(title)
        st.dataframe(pd.read_sql_query(sql, conn), hide_index=True)
