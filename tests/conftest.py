import sqlite3
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from load_data import init_schema

@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    init_schema(c)
    c.executescript("""
    INSERT INTO Areas VALUES (1,'11111','Alder',10000,20000,30,25),
                             (2,'22222','Alder',10000,90000,5,3),
                             (3,'33333','Birch',5000,25000,28,30);
    INSERT INTO StoreTypes VALUES (1,'supermarket',1),(2,'convenience store',0),
                                  (3,'dollar store',0),(4,'farmers market',1);
    INSERT INTO Stores VALUES (1,'S1','a',40.5,-100.5,1,2,1),
                              (2,'S2','a',40.0,-100.0,1,1,2),
                              (3,'S3','a',40.0,-100.0,0,1,3),
                              (4,'S4','a',40.0,-100.0,1,3,1),
                              (5,'S5','a',40.0,-100.0,1,3,2);
    INSERT INTO TransitStops VALUES (1,'T1',40.0,-100.0,1),(2,'T2',40.0,-100.0,3);
    INSERT INTO StoreStopAccess VALUES (2,1,200),(3,1,350),(4,2,1500),(5,2,300);
    """)
    c.commit()
    yield c
    c.close()
