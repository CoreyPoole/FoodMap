import pandas as pd
import pytest
import geopandas as gpd
from shapely.geometry import box
import zipfile
from import_real_data import import_sources, TABLES
from db import get_conn

@pytest.mark.parametrize('split_address', [False, True])
def test_offline_import(tmp_path, split_address):
    cache=tmp_path/'raw'; cache.mkdir()
    ids=['48029000100','48091000100']
    polys=[box(-99,29,-98.9,29.1),box(-98.9,29,-98.8,29.1)]
    for name, fields in [('tracts', {'GEOID':ids,'COUNTYFP':['029','091']}), ('zcta', {'GEOID20':['78201','78130']})]:
        gpd.GeoDataFrame(fields,geometry=polys,crs=4326).to_file(cache/(name+'.shp'))
        with zipfile.ZipFile(cache/(name+'.zip'),'w') as z:
            for f in cache.glob(name+'.*'):
                if f.suffix!='.zip': z.write(f,f.name)
    for table, numbers in TABLES.items():
        d={'GEO_ID':['1400000US'+i for i in ids]}
        for n in numbers: d[f'{table}_E{n:03d}']=[1000 if n==1 else 100]*2
        pd.DataFrame(d).to_csv(cache/(table+'.dat'),sep='|',index=False)
    def write_zip(name, member, text):
        with zipfile.ZipFile(cache/name,'w') as z: z.writestr(member,text)
    if split_address:
        write_zip('snap.zip','retail.csv','Record ID,Store Name,Store Type,Street Number,Street Name,Additional Address,City,State,Zip Code,Zip4,County,Latitude,Longitude,Authorization Date,End Date\n1,Test Mart,Supermarket,1,Main,Suite A,Test,TX,78201,,Bexar,29.05,-98.95,01/01/2020,\n2,Closed,Supermarket,2,Main,,Test,TX,78201,,Bexar,29.05,-98.95,01/01/2020,01/01/2021\n')
    else:
        write_zip('snap.zip','retail.csv','Store Name,Store Street Address,City,State,Zip Code,Store Type,Latitude,Longitude,Authorization Date,End Date\nTest Mart,1 Main,Test,TX,78201,Supermarket,29.05,-98.95,01/01/2020,\nClosed,2 Main,Test,TX,78201,Supermarket,29.05,-98.95,01/01/2020,01/01/2021\n')
    write_zip('via.zip','stops.txt','stop_id,stop_name,stop_lat,stop_lon,location_type\n1,Test stop,29.05,-98.95,0\n')
    write_zip('atlas.zip','atlas.csv','CensusTract,LowAccess\n48029000100,1\n48091000100,0\n')
    db=tmp_path/'real.db'
    counts=import_sources(cache,tmp_path/'processed',db)
    assert counts['Areas']==2 and counts['Stores']==1 and counts['TransitStops']==1 and counts['StoreStopAccess']==1
    with get_conn(db) as c:
        assert c.execute('SELECT address FROM Stores').fetchone()[0] == ('1 Main Suite A, Test, TX 78201' if split_address else '1 Main, Test, TX 78201')
        assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        assert not c.execute('PRAGMA foreign_key_check').fetchall()
