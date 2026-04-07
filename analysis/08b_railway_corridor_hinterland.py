#!/usr/bin/env python3
"""
Query 8b — Railway corridor hinterland around RSC/LSC/City settlements

Identifies which Type A small settlements (farm clusters, farm-service towns, etc.)
share a railway corridor with each RSC/LSC/City hub, using two methods:

PRIMARY: Borealis historical railway shapefile (HR_rails_NEW.shp)
  - Filters to pre-1921 Saskatchewan lines
  - Spatially snaps each settlement to line segments within 5km
  - Two settlements share a corridor if they match the same Borealis line segment

FALLBACK: settlement_connections.json (Sask_Railway_Visualizations)
  - Used for settlements not snapped by Borealis (e.g. M&NWR gaps)
  - Matches on shared_railway company + railway_distance_km threshold
  - Does NOT overwrite any existing settlement data

Outputs:
  analysis/08b_corridor_hinterland_results.csv  — one row per hub
  analysis/08b_corridor_detail.csv              — one row per hub-satellite pair
"""

import json
import re
import warnings
warnings.filterwarnings('ignore')

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from neo4j import GraphDatabase

# --- Config ---
BOREALIS_SHP  = '/Users/baebot/Documents/ClaudeCode/KnowledgeGraph/gis_data/doi-10.5683-sp2-uccfvq/extracted/HR_rails_NEW.shp'
CONNECTIONS_JSON = '/Users/baebot/Documents/ClaudeCode/Sask_Railway_Visualizations/data/settlement_connections.json'
NEO4J_URI     = 'bolt://localhost:7687'
NEO4J_AUTH    = ('neo4j', '11069173')

# Pre-1921 Saskatchewan builder codes (date-bounded and spatially confirmed)
SK_CODES      = ['1', '5', '2', '49', '49A', '49B', '53P', '53R', '14C']
MAX_YEAR      = 1921
SK_BOUNDS     = (-110.0, 49.0, -101.3, 60.0)   # W, S, E, N
SNAP_M        = 5000   # snap settlement to Borealis line within 5km

# Fallback: max railway distance (km) along network for same-company connections
FALLBACK_RAIL_KM = 200

HUB_TYPES = ['Regional Service Centre', 'Local Service Centre', 'City']
SAT_TYPES  = [
    'Farm Cluster', 'Farm-Service Town', 'Small Service Centre',
    'Railway Town', 'Organized/Ethnic Settlement',
]


# ── 1. Load Borealis lines ────────────────────────────────────────────────────

print("Loading Borealis railway shapefile...")
gdf_raw = gpd.read_file(BOREALIS_SHP)
gdf_wgs  = gdf_raw.to_crs('EPSG:4326')

# Clip to Saskatchewan extent and filter by builder code + year
W, S, E, N = SK_BOUNDS
sk_lines = gdf_wgs.cx[W:E, S:N].copy()
sk_lines = sk_lines[
    sk_lines['BLDR_CODE'].isin(SK_CODES) &
    (sk_lines['CNSTRCTD'] > 0) &
    (sk_lines['CNSTRCTD'] <= MAX_YEAR)
].copy()
sk_lines = sk_lines.reset_index(drop=True)

# Reproject to a metre-based CRS for buffering
sk_lines_m = sk_lines.to_crs('EPSG:3400')   # NAD83 / Alberta 10-TM Forest — reasonable for SK
print(f"  {len(sk_lines)} pre-1921 Borealis line segments in Saskatchewan extent")


# ── 2. Load settlements from Neo4j ───────────────────────────────────────────

print("Loading settlements from Neo4j...")
driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

query = """
MATCH (s:Settlement)
OPTIONAL MATCH (s)-[:IS_TYPE]->(ct:SettlementType)
RETURN
  s.census_name             AS name,
  s.latitude                AS lat,
  s.longitude               AS lon,
  s.temporal_type           AS temporal_type,
  s.min_dist_to_surrender_m AS dist_to_surrender_m,
  s.first_railway           AS first_railway,
  s.railway_arrives         AS railway_arrives,
  collect(ct.name)          AS commercial_types
"""

rows = []
with driver.session() as session:
    for r in session.run(query):
        rows.append(dict(r))
driver.close()

settlements = pd.DataFrame(rows)

# Short name (strip ", VL" etc) for joining with connections.json
settlements['short_name'] = settlements['name'].str.replace(
    r',\s*(VL|T-V|C|RM|TV)$', '', regex=True).str.strip()

print(f"  {len(settlements)} settlements loaded")


# ── 3. Snap each settlement to Borealis lines ─────────────────────────────────

print("Snapping settlements to Borealis lines...")

# Build GeoDataFrame of settlement points
gdf_sett = gpd.GeoDataFrame(
    settlements,
    geometry=[Point(row.lon, row.lat) for row in settlements.itertuples()],
    crs='EPSG:4326'
).to_crs('EPSG:3400')

# For each settlement, find all Borealis line OBJECTIDs within SNAP_M
sett_lines = {}   # short_name -> set of Borealis OBJECTIDs
for sett in gdf_sett.itertuples():
    if pd.isna(sett.lat) or pd.isna(sett.lon):
        sett_lines[sett.short_name] = set()
        continue
    pt   = sett.geometry
    buf  = pt.buffer(SNAP_M)
    hits = sk_lines_m[sk_lines_m.intersects(buf)]['OBJECTID'].tolist()
    sett_lines[sett.short_name] = set(hits)

n_borealis = sum(1 for v in sett_lines.values() if v)
print(f"  {n_borealis} settlements snapped to at least one Borealis line")
print(f"  {len(settlements) - n_borealis} settlements will use fallback")


# ── 4. Load fallback connections ──────────────────────────────────────────────

print("Loading settlement_connections.json fallback...")
with open(CONNECTIONS_JSON) as f:
    conn_data = json.load(f)
connections = conn_data['connections']   # dict: settlement_short_name -> list of conn dicts


# ── 5. Classify each settlement ───────────────────────────────────────────────

def is_hub(row):
    return any(t in HUB_TYPES for t in row['commercial_types'])

def is_satellite(row):
    return any(t in SAT_TYPES for t in row['commercial_types'])

settlements['is_hub']       = settlements.apply(is_hub, axis=1)
settlements['is_satellite'] = settlements.apply(is_satellite, axis=1)
settlements['borealis_matched'] = settlements['short_name'].map(
    lambda n: bool(sett_lines.get(n)))

hubs = settlements[settlements['is_hub'] & (settlements['temporal_type'] == 'A')]
sats = settlements[settlements['is_satellite'] & (settlements['temporal_type'] == 'A')]

print(f"  Type A hubs: {len(hubs)}  |  Type A satellites: {len(sats)}")


# ── 6. Build corridor pairs ───────────────────────────────────────────────────

print("Building corridor pairs...")

detail_rows = []

for _, hub in hubs.iterrows():
    hub_short   = hub['short_name']
    hub_lines   = sett_lines.get(hub_short, set())
    hub_railway = hub['first_railway']

    for _, sat in sats.iterrows():
        if sat['name'] == hub['name']:
            continue

        sat_short   = sat['short_name']
        sat_lines   = sett_lines.get(sat_short, set())
        sat_railway = sat['first_railway']

        method = None

        # Primary: shared Borealis line segment
        if hub_lines and sat_lines and hub_lines & sat_lines:
            method = 'borealis'

        # Fallback: settlement_connections.json same-railway within distance threshold
        elif not method:
            hub_conns = connections.get(hub_short, [])
            for conn in hub_conns:
                if (conn.get('to') == sat_short
                        and conn.get('shared_railway') == hub_railway == sat_railway
                        and conn.get('shared_railway') not in (None, 'Interchange')
                        and (conn.get('railway_distance_km') or 9999) <= FALLBACK_RAIL_KM):
                    method = 'fallback'
                    break

        if method:
            detail_rows.append({
                'hub':                   hub['name'],
                'hub_dist_to_surrender': hub['dist_to_surrender_m'],
                'hub_railway':           hub_railway,
                'satellite':             sat['name'],
                'sat_dist_to_surrender': sat['dist_to_surrender_m'],
                'sat_railway':           sat_railway,
                'method':                method,
            })

detail = pd.DataFrame(detail_rows)
print(f"  {len(detail)} hub-satellite corridor pairs found")


# ── 7. Aggregate to hub level ─────────────────────────────────────────────────

agg = (
    detail.groupby('hub')
    .agg(
        hub_dist_to_surrender  = ('hub_dist_to_surrender', 'first'),
        hub_railway            = ('hub_railway', 'first'),
        n_corridor_satellites  = ('satellite', 'nunique'),
        n_borealis             = ('method', lambda x: (x == 'borealis').sum()),
        n_fallback             = ('method', lambda x: (x == 'fallback').sum()),
        avg_sat_dist_surrender = ('sat_dist_to_surrender', 'mean'),
        min_sat_dist_surrender = ('sat_dist_to_surrender', 'min'),
        satellite_sample       = ('satellite', lambda x: ', '.join(list(x.unique())[:6])),
    )
    .reset_index()
    .sort_values('n_corridor_satellites', ascending=False)
)

# ── 8. Output ─────────────────────────────────────────────────────────────────

out_dir = '/Users/baebot/Documents/ClaudeCode/Reserves_Urban_Spaces/analysis'
agg.to_csv(f'{out_dir}/08b_corridor_hinterland_results.csv', index=False)
detail.to_csv(f'{out_dir}/08b_corridor_detail.csv', index=False)

print("\n── Results ──────────────────────────────────────────────────────────────")
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 160)
pd.set_option('display.float_format', '{:.0f}'.format)
print(agg[['hub','hub_railway','hub_dist_to_surrender','n_corridor_satellites',
           'n_borealis','n_fallback','avg_sat_dist_surrender','min_sat_dist_surrender',
           'satellite_sample']].to_string(index=False))

print(f"\nResults saved to analysis/08b_corridor_hinterland_results.csv")
print(f"Detail saved to analysis/08b_corridor_detail.csv")
