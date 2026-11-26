"""Build a separate San Antonio-area SQLite database from official public files."""
import argparse, json, zipfile
from datetime import date
from pathlib import Path
import geopandas as gpd
import pandas as pd
import requests
from load_data import build_database

COUNTIES = {'029': 'Bexar', '091': 'Comal', '187': 'Guadalupe'}
ACS = 'https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/'
URLS = {
    'tracts.zip': 'https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_48_tract.zip',
    'zcta.zip': 'https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_us_zcta520_500k.zip',
    'snap.zip': 'https://fns-prod.azureedge.us/sites/default/files/resource-files/snap-retailer-locator-data2005-2025.zip',
    'via.zip': 'https://www.viainfo.net/BusService/google_transit.zip',
    'atlas.zip': 'https://www.ers.usda.gov/media/29395/2025-snap-authorized-retailer-access-map-sram-data.zip?v=60625',
}
TABLES = {'B01003': [1], 'B19013': [1], 'B17001': [1, 2], 'B08201': [1, 2]}
URLS.update({t+'.dat': ACS+'acsdt5y2024-'+t.lower()+'.dat' for t in TABLES})

def download(cache, name):
    path = cache/name
    if not path.exists():
        print('Downloading', name, flush=True)
        tmp = path.with_suffix(path.suffix+'.part')
        with requests.get(URLS[name], stream=True, timeout=(30, 180), headers={'User-Agent':'FoodMap student research/1.0'}) as r:
            r.raise_for_status()
            with tmp.open('wb') as f:
                for chunk in r.iter_content(1024*1024): f.write(chunk)
        tmp.replace(path)
    return path

def norm(s): return ''.join(c for c in str(s).lower() if c.isalnum())

def field(df, *names):
    cols = {norm(c): c for c in df.columns}
    for name in names:
        if norm(name) in cols: return cols[norm(name)]
    raise ValueError(f'Missing expected column {names}; available: {list(df.columns)}')

def street_address(df):
    """Support USDA split street fields and older combined-address exports."""
    cols = {norm(c): c for c in df.columns}
    def part(*names):
        for name in names:
            if norm(name) in cols:
                return df[cols[norm(name)]].fillna('').astype(str).str.strip()
        return pd.Series('', index=df.index, dtype=str)
    combined_names = ('Store Street Address', 'Store Street', 'Street Address')
    if any(norm(n) in cols for n in combined_names):
        street = part(*combined_names)
    else:
        number = part('Street Number')
        name = df[field(df, 'Street Name')].fillna('').astype(str).str.strip()
        street = (number + ' ' + name).str.strip()
    additional = part('Additional Address')
    street = (street + ' ' + additional).str.strip()
    return street.replace('', pd.NA)

def csv_zip(path, member=None, **kwargs):
    with zipfile.ZipFile(path) as z:
        candidates = [n for n in z.namelist() if n.lower().endswith('.csv') and 'lookup' not in n.lower() and 'readme' not in n.lower()]
        name = next((n for n in z.namelist() if n.rsplit('/',1)[-1] == member), None) if member else max(candidates, key=lambda n: z.getinfo(n).file_size)
        if not name: raise ValueError(f'Missing {member} in {path}')
        # Some official USDA CSVs use Windows-1252 rather than UTF-8.
        for encoding in ('utf-8-sig', 'cp1252', 'latin-1'):
            try:
                with z.open(name) as f:
                    return pd.read_csv(f, low_memory=False, encoding=encoding, **kwargs)
            except UnicodeDecodeError:
                if encoding == 'latin-1':
                    raise


def atlas_reference(path):
    """Join available SRAM tract tables without relying on archive file size."""
    with zipfile.ZipFile(path) as z:
        members = [n for n in z.namelist() if n.lower().endswith('.csv')]
    preferred = []
    for label in ('general tract characteristics', 'straight line distance', 'driving distance'):
        matches = [n for n in members if label in n.lower()]
        if matches:
            preferred.append(matches[0].rsplit('/', 1)[-1])
    frames = []
    for member in preferred or [None]:
        df = csv_zip(path, member, dtype=str)
        key = field(df, 'CensusTract20', 'CensusTract', 'GEOID', 'Tract',
                    'Tract ID', 'Census Tract ID', 'GEOID20', 'TractFIPS',
                    'Census Tract GEOID', 'GEOID_TRACT_20')
        ids = df[key].str.strip().str.removesuffix('.0').str.zfill(11)
        df = df.rename(columns={key: 'CensusTract20'})
        df['CensusTract20'] = ids
        df = df[ids.str[:5].isin({'48'+c for c in COUNTIES})].copy()
        if df.empty:
            raise ValueError(f'No selected-county tract records in atlas table {member}')
        if df['CensusTract20'].duplicated().any():
            raise ValueError(f'Duplicate census tracts in atlas table {member}')
        frames.append(df)
    atlas = frames[0]
    for df in frames[1:]:
        new_cols = ['CensusTract20'] + [c for c in df.columns if c not in atlas.columns]
        atlas = atlas.merge(df[new_cols], on='CensusTract20', how='outer', validate='one_to_one')
    return atlas

def acs_values(cache, ids):
    out = pd.DataFrame(index=pd.Index(sorted(ids), name='geoid'))
    for table, numbers in TABLES.items():
        cols = [f'{table}_E{n:03d}' for n in numbers]
        parts = []
        for chunk in pd.read_csv(cache/(table+'.dat'), sep='|', dtype=str, usecols=['GEO_ID']+cols, chunksize=50000):
            chunk['geoid'] = chunk.GEO_ID.str.split('US').str[-1]
            parts.append(chunk[chunk.geoid.isin(ids)].set_index('geoid')[cols])
        data = pd.concat(parts)
        if data.index.has_duplicates: raise ValueError(f'Duplicate geography in {table}')
        out = out.join(data.apply(pd.to_numeric, errors='coerce'))
    return out

def classify(kind, name):
    n, k = name.lower(), kind.lower()
    if any(x in n for x in ('dollar general','family dollar','dollar tree')): return 5
    if k in ('super store','supermarket'): return 1
    if 'grocery' in k: return 2
    if 'farmer' in k: return 3
    if 'convenience' in k: return 4
    return 6

def locate(df, tracts):
    df = df.copy()
    df['latitude'] = pd.to_numeric(df.latitude, errors='coerce')
    df['longitude'] = pd.to_numeric(df.longitude, errors='coerce')
    df = df[df.latitude.between(-90,90) & df.longitude.between(-180,180)]
    points = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude,df.latitude), crs=4326)
    joined = gpd.sjoin(points, tracts[['area_id','geometry']], predicate='intersects', how='inner')
    return joined.sort_values('area_id').loc[lambda x: ~x.index.duplicated(keep='first')]

def import_sources(cache, output, db_path):
    output.mkdir(parents=True, exist_ok=True)
    if (output/'store_stop_access.csv').exists(): raise ValueError('Choose a clean output directory; stale walking links would be unsafe.')
    tracts = gpd.read_file(cache/'tracts.zip').to_crs(4326)
    tracts = tracts[tracts.COUNTYFP.isin(COUNTIES)].copy()
    tracts['area_id'] = tracts.GEOID.astype('int64')
    bounds = tracts.total_bounds
    zcta = gpd.read_file(cache/'zcta.zip', bbox=tuple(bounds)).to_crs(4326)
    zcta['zip_code'] = zcta[field(zcta,'ZCTA5CE20','GEOID20','GEOID')].astype(str).str.zfill(5)
    centers = tracts[['area_id','geometry']].to_crs(26914)
    centers.geometry = centers.geometry.representative_point()
    nearest = gpd.sjoin_nearest(centers,zcta[['zip_code','geometry']].to_crs(26914),how='left')
    zip_map = nearest.sort_values('zip_code').drop_duplicates('area_id').set_index('area_id').zip_code
    stats = acs_values(cache, set(tracts.GEOID))
    areas=[]
    for r in tracts.itertuples():
        p,i,pd_,pn,vd,vn = stats.loc[r.GEOID, ['B01003_E001','B19013_E001','B17001_E001','B17001_E002','B08201_E001','B08201_E002']]
        if not (p>0 and i>=0 and pd_>0 and vd>0 and 0<=pn<=pd_ and 0<=vn<=vd): continue
        areas.append((r.area_id,zip_map[r.area_id],COUNTIES[r.COUNTYFP],int(p),float(i),round(100*pn/pd_,2),round(100*vn/vd,2)))
    area_df = pd.DataFrame(areas,columns=['area_id','zip_code','county','population','median_income','poverty_rate','pct_households_no_vehicle'])
    tracts = tracts[tracts.area_id.isin(area_df.area_id)]
    if area_df.empty: raise ValueError('No valid ACS tracts')
    snap = csv_zip(cache/'snap.zip', dtype=str)
    state=field(snap,'State','State Abbreviation','State Abbr')
    snap=snap[snap[state].str.upper().eq('TX')].copy()
    start=pd.to_datetime(snap[field(snap,'Authorization Date','Auth Date')],errors='coerce',format='mixed')
    end_raw=snap[field(snap,'End Date','Authorization End Date')]
    end=pd.to_datetime(end_raw,errors='coerce',format='mixed')
    asof=pd.Timestamp('2025-12-31')
    snap=snap[(start<=asof)&(end_raw.isna()|end_raw.str.strip().eq('')|(end>=asof))]
    snap_df=pd.DataFrame({'name':snap[field(snap,'Store Name')], 'street':street_address(snap), 'city':snap[field(snap,'City')], 'zip':snap[field(snap,'Zip Code','Zip')], 'kind':snap[field(snap,'Store Type')], 'latitude':snap[field(snap,'Latitude')], 'longitude':snap[field(snap,'Longitude')]})
    snap_df=snap_df.dropna(subset=['name','street','kind']).drop_duplicates(['name','street','city','latitude','longitude']).reset_index(drop=True)
    stores=locate(snap_df,tracts).copy().reset_index(drop=True)
    stores['store_id']=stores.index+1
    stores['address']=stores.street.fillna('')+', '+stores.city.fillna('')+', TX '+stores.zip.fillna('')
    stores['type_id']=[classify(k,n) for k,n in zip(stores.kind,stores.name)]
    stores['accepts_snap']=1
    gtfs=csv_zip(cache/'via.zip','stops.txt',dtype=str)
    if 'location_type' in gtfs: gtfs=gtfs[gtfs.location_type.fillna('0').isin(['','0'])]
    stops=locate(gtfs.rename(columns={'stop_lat':'latitude','stop_lon':'longitude'}).dropna(subset=['stop_name']).drop_duplicates('stop_id').reset_index(drop=True),tracts).copy().reset_index(drop=True)
    stops['stop_id']=stops.index+1
    if stores.empty or stops.empty: raise ValueError('No matched stores or stops; check inputs')
    types=pd.DataFrame([(1,'supermarket',1),(2,'small grocery',1),(3,'farmers market',1),(4,'convenience store',0),(5,'dollar store',0),(6,'other / unknown',0)],columns=['type_id','type_name','sells_fresh_produce'])
    area_df.to_csv(output/'areas.csv',index=False)
    types.to_csv(output/'store_types.csv',index=False)
    stores[['store_id','name','address','latitude','longitude','accepts_snap','area_id','type_id']].to_csv(output/'stores.csv',index=False)
    stops[['stop_id','stop_name','latitude','longitude','area_id']].to_csv(output/'transit_stops.csv',index=False)
    atlas=atlas_reference(cache/'atlas.zip')
    atlas.to_csv(output/'usda_atlas_reference.csv',index=False)
    counts=build_database(db_path,output)
    manifest={'mode':'real','region':'Bexar, Comal and Guadalupe counties, Texas','acs':'2020–2024 ACS 5-year','snap_as_of':'2025-12-31','import_date':str(date.today()),'counts':counts,'atlas_rows':len(atlas),'atlas_reference':str((output/'usda_atlas_reference.csv').resolve()),'excluded_tracts':len(stats)-len(areas),'sources':URLS,'limitations':'SNAP-authorized retailers only; fresh produce inferred from store type; ZIP is a nearest ZCTA proxy for tract; walking distances estimated; data vintages differ.'}
    Path(str(db_path)+'.sources.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))
    return counts

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache',type=Path,default=Path('raw_data'))
    p.add_argument('--output',type=Path,default=Path('real_data'))
    p.add_argument('--db',type=Path,default=Path('foodmap_real.db'))
    p.add_argument('--accept-via-terms',action='store_true',help='Read VIA developer license before using its data')
    a=p.parse_args()
    if not a.accept_via_terms: p.error('Read https://www.viainfo.net/developers-license-agreement/ and pass --accept-via-terms if you accept.')
    if a.db.exists(): p.error('Database exists; choose a new --db path or back up and remove it first.')
    a.cache.mkdir(parents=True,exist_ok=True)
    for name in URLS: download(a.cache,name)
    import_sources(a.cache,a.output,a.db)

if __name__=='__main__': main()
