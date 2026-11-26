import pytest
import crud

GOOD_STORE = dict(name="New Mart", address="1 Main", latitude=40.001, longitude=-100.0,
                  accepts_snap=True, area_id=1, type_id=1)
GOOD_AREA = dict(zip_code="44444", county="Cedar", population=1000, median_income=50000,
                 poverty_rate=10, pct_households_no_vehicle=5)

def test_create_store_computes_walking_links(conn):
    sid = crud.create_store(conn, **GOOD_STORE)
    rows = conn.execute("SELECT stop_id, walk_distance_m FROM StoreStopAccess WHERE store_id=?", (sid,)).fetchall()
    assert {r[0] for r in rows} == {1, 2} and all(r[1] < 300 for r in rows)

def test_update_store_moves_links(conn):
    sid = crud.create_store(conn, **GOOD_STORE)
    crud.update_store(conn, sid, **{**GOOD_STORE, "latitude": 41.0})
    assert conn.execute("SELECT COUNT(*) FROM StoreStopAccess WHERE store_id=?", (sid,)).fetchone()[0] == 0
    assert crud.get_store(conn, sid)["latitude"] == 41.0

def test_delete_store_cascades_links(conn):
    crud.delete_store(conn, 2)
    assert conn.execute("SELECT COUNT(*) FROM StoreStopAccess WHERE store_id=2").fetchone()[0] == 0
    with pytest.raises(crud.ValidationError):
        crud.delete_store(conn, 2)

@pytest.mark.parametrize("bad", [
    {"name": " "}, {"latitude": 95}, {"longitude": "abc"}, {"area_id": 999}, {"type_id": 999}])
def test_store_validation(conn, bad):
    with pytest.raises(crud.ValidationError):
        crud.create_store(conn, **{**GOOD_STORE, **bad})

def test_area_crud_roundtrip(conn):
    aid = crud.create_area(conn, **GOOD_AREA)
    crud.update_area(conn, aid, **{**GOOD_AREA, "county": "Dune"})
    assert crud.get_area(conn, aid)["county"] == "Dune"
    crud.delete_area(conn, aid)
    assert crud.get_area(conn, aid) is None

@pytest.mark.parametrize("bad", [
    {"zip_code": "123"}, {"zip_code": "abcde"}, {"population": 0}, {"poverty_rate": 101},
    {"pct_households_no_vehicle": -1}, {"median_income": -5}, {"county": ""}])
def test_area_validation(conn, bad):
    with pytest.raises(crud.ValidationError):
        crud.create_area(conn, **{**GOOD_AREA, **bad})

def test_cannot_delete_area_with_children(conn):
    with pytest.raises(crud.ValidationError, match="still has"):
        crud.delete_area(conn, 1)
    assert crud.get_area(conn, 1) is not None
