import queries

def test_q1_food_desert_candidates(conn):
    df = queries.food_desert_candidates(conn, 30000, 1)
    assert df["area_id"].tolist() == [1]
    df = queries.food_desert_candidates(conn, 30000, 3)
    assert sorted(df["area_id"]) == [1, 3]
    assert queries.food_desert_candidates(conn, 10000, 3).empty

def test_q2_no_vehicle_no_walkable_fresh(conn):
    assert sorted(queries.no_vehicle_no_walkable_fresh(conn, 20, 1000)["area_id"]) == [1, 3]
    assert queries.no_vehicle_no_walkable_fresh(conn, 20, 2000)["area_id"].tolist() == [1]
    assert queries.no_vehicle_no_walkable_fresh(conn, 99, 1000).empty

def test_q3_snap_near_transit(conn):
    df = queries.snap_stores_near_transit(conn, 500)
    assert df["store_id"].tolist() == [2, 5]
    assert queries.snap_stores_near_transit(conn, 500, "11111")["store_id"].tolist() == [2]
    assert queries.snap_stores_near_transit(conn, 500, "00000").empty

def test_q4_store_mix_by_county(conn):
    df = queries.store_mix_by_county(conn, 1)
    assert df["county"].tolist() == ["Birch", "Alder"]
    assert df["pct_fresh"].tolist() == [50.0, 33.3]
    assert df["rank_by_fresh_share"].tolist() == [1, 2]
    assert queries.store_mix_by_county(conn, 3)["county"].tolist() == ["Alder"]

def test_q5_access_gap_ranking(conn):
    df = queries.access_gap_ranking(conn, 3)
    assert df["area_id"].tolist() == [1, 3, 2]
    assert df["access_gap_score"].tolist() == [49.5, 35.2, 25.4]
    assert len(queries.access_gap_ranking(conn, 1)) == 1

def test_queries_are_injection_safe(conn):
    assert queries.snap_stores_near_transit(conn, 500, "' OR '1'='1").empty
