#!/usr/bin/env python3
"""
Phase 0: Data Preparation
Cleans, filters, and standardises all input layers for the Indigenous spatial analysis.
Outputs analysis-ready files to analysis/data/.

Run this script first. All subsequent phases depend on its outputs.
"""

import os
import warnings
import pandas as pd
import geopandas as gpd
import shapely
from neo4j import GraphDatabase

warnings.filterwarnings('ignore')

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'analysis', 'data')
SASK_RESERVES_DIR = os.path.join(BASE_DIR, 'Sask_Reserves')
METIS_DIR = os.path.join(BASE_DIR, 'SK_Metis_Communities')
URBAN_DIR = os.path.join(BASE_DIR, 'Urban_Munis')

TARGET_CRS = 'EPSG:3347'  # NAD83 / Statistics Canada Lambert

# --- Neo4j ---
NEO4J_URI = 'bolt://localhost:7687'
NEO4J_PASSWORD = '11069173'


# =============================================================================
# Loaders
# =============================================================================

def get_neo4j_settlements():
    """Retrieve all Settlement records from Neo4j, including commercial type."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=('neo4j', NEO4J_PASSWORD))
    query = """
        MATCH (s:Settlement)
        OPTIONAL MATCH (s)-[:IS_TYPE]->(ct:SettlementType)
        RETURN
            s.census_id       AS census_id,
            s.census_name     AS census_name,
            s.csd_type        AS csd_type,
            s.founded         AS founded,
            s.incorporated    AS incorporated,
            s.population_1921 AS population_1921,
            s.latitude        AS latitude,
            s.longitude       AS longitude,
            ct.name           AS commercial_type
        ORDER BY s.census_id
    """
    with driver.session() as session:
        records = [dict(r) for r in session.run(query)]
    driver.close()
    df = pd.DataFrame(records)
    print(f"  Neo4j: {len(df)} settlement records")
    return df


def load_urban_municipalities(neo4j_df):
    """Load the full SK 1921 CSD GeoJSON, strip field prefixes, filter to 429."""
    path = os.path.join(URBAN_DIR, 'Sask_1921_Urban_Muni_Full.geojson')
    gdf = gpd.read_file(path)

    # Strip ArcGIS export field name prefixes.
    # The GeoJSON has two sets of columns: L0Sask1921Full.* (spatial layer) and
    # UrbanSaskHist - Final.csv.* (joined CSV). After stripping both prefixes the
    # names collide. Keep only the L0Sask1921Full columns plus geometry.
    spatial_cols = [c for c in gdf.columns if c.startswith('L0Sask1921Full.') or c == 'geometry']
    gdf = gdf[spatial_cols].copy()
    gdf.columns = [c.replace('L0Sask1921Full.', '') for c in gdf.columns]

    print(f"  Urban CSD layer: {len(gdf)} total features")

    # Filter to 429 urban municipalities using Neo4j TCPUIDs as authority
    valid_tcpuids = set(neo4j_df['census_id'].dropna())
    gdf_filtered = gdf[gdf['TCPUID_CSD_1921'].isin(valid_tcpuids)].copy()
    print(f"  After TCPUID filter: {len(gdf_filtered)} urban municipalities")

    # Report any Neo4j TCPUIDs missing from the GeoJSON
    missing = valid_tcpuids - set(gdf_filtered['TCPUID_CSD_1921'])
    if missing:
        print(f"  WARNING: {len(missing)} Neo4j TCPUIDs not found in GeoJSON:")
        for t in sorted(missing)[:10]:
            print(f"    {t}")

    gdf_filtered = gdf_filtered.to_crs(TARGET_CRS)
    return gdf_filtered


def load_surrenders():
    """Load and clean the reserve surrenders layer."""
    path = os.path.join(SASK_RESERVES_DIR, 'SK_ReserveSurrenders_1933.geojson')
    gdf = gpd.read_file(path)
    print(f"  Surrender parcels: {len(gdf)} features")

    # Force 2D geometry (in case of Z coordinates)
    gdf['geometry'] = gdf['geometry'].apply(
        lambda g: shapely.force_2d(g) if g is not None else g
    )

    # Create a clean surrender year field
    # YR_SUR is the primary clean field; YEAR_SURR can have -99 sentinels
    gdf['year_surr_clean'] = pd.to_numeric(gdf['YR_SUR'], errors='coerce')
    missing_yr = gdf['year_surr_clean'].isna()
    fallback = pd.to_numeric(gdf.loc[missing_yr, 'YEAR_SURR'], errors='coerce').replace(-99, pd.NA)
    gdf.loc[missing_yr, 'year_surr_clean'] = fallback
    gdf['year_surr_clean'] = gdf['year_surr_clean'].astype('Int64')

    # Extract base UNIQUE_ID (strip sub-parcel suffix like -3)
    gdf['UNIQUE_ID_BASE'] = gdf['UNIQUE_ID'].str.split('-').str[0]

    null_yr = gdf['year_surr_clean'].isna().sum()
    yr_min = gdf['year_surr_clean'].dropna().min()
    yr_max = gdf['year_surr_clean'].dropna().max()
    print(f"  Surrender year: {len(gdf) - null_yr} of {len(gdf)} have year data ({yr_min}–{yr_max})")

    gdf = gdf.to_crs(TARGET_CRS)
    return gdf


def load_initial_survey():
    """Load the initial reserve survey polygons and normalise the join key."""
    path = os.path.join(SASK_RESERVES_DIR, 'Reserves_Initial_Survey.geojson')
    gdf = gpd.read_file(path)
    print(f"  Initial survey: {len(gdf)} reserve polygons")

    # Rename UniqueD_1902 to UNIQUE_ID to match all other layers
    if 'UniqueD_1902' in gdf.columns:
        gdf = gdf.rename(columns={'UniqueD_1902': 'UNIQUE_ID'})

    gdf = gdf.to_crs(TARGET_CRS)
    return gdf


def load_reserves_master():
    """Load the master reserves Excel table and produce a long-format surrender table."""
    path = os.path.join(SASK_RESERVES_DIR, 'Sask_Reserves_1931.xlsx')
    df = pd.read_excel(path, sheet_name='Sheet1')
    print(f"  Reserves master table: {len(df)} records")

    # Identify per-year surrender columns
    surr_cols = [
        c for c in df.columns
        if str(c).startswith('SURR_') and str(c) != 'SURR_ND_ACRES'
    ]
    print(f"  Surrender year columns: {len(surr_cols)} ({surr_cols[0]}–{surr_cols[-1]})")

    # Melt to long format — one row per (reserve, year) with non-zero acreage
    id_cols = [c for c in ['UNIQUE_ID', 'RSRV_NAME', 'ORIG_ACRE', 'ACRES_1902',
                            'TSURR_BY_1933', 'Data_Certainty'] if c in df.columns]
    long_df = df.melt(
        id_vars=id_cols,
        value_vars=surr_cols,
        var_name='surr_year_col',
        value_name='acres_surrendered'
    )
    long_df['year'] = long_df['surr_year_col'].str.replace('SURR_', '').astype(int)
    long_df = long_df.dropna(subset=['acres_surrendered'])
    long_df = long_df[long_df['acres_surrendered'] > 0].copy()
    long_df = long_df.drop(columns=['surr_year_col'])
    print(f"  Long-format surrender table: {len(long_df)} reserve-year events")

    return df, long_df


def load_metis_communities():
    """Load Métis GeoJSON and Excel table, join on UNIQUE_ID."""
    geojson_path = os.path.join(METIS_DIR, 'Metis_Community.geojson')
    gdf = gpd.read_file(geojson_path)
    print(f"  Métis georeferenced: {len(gdf)} communities")

    # Force 2D (hasZ=true in this layer)
    gdf['geometry'] = gdf['geometry'].apply(
        lambda g: shapely.force_2d(g) if g is not None else g
    )

    # Excel master table (113 communities with temporal data)
    xlsx_path = os.path.join(METIS_DIR, 'Métis_Communities.xlsx')
    df_all = pd.read_excel(xlsx_path, sheet_name='Sheet1')
    print(f"  Métis full table: {len(df_all)} communities")

    # Rename GeoJSON Name field and drop xlsx NAME column before merge to avoid
    # collision (GeoJSON has 'Name', xlsx has 'NAME'; also 'NAME' is reserved in OGR)
    gdf = gdf.rename(columns={'Name': 'community_name'})
    gdf_joined = gdf.merge(
        df_all.drop(columns=['NAME', 'Name'], errors='ignore'),
        on='UNIQUE_ID',
        how='left'
    )

    # Unlocated communities — in xlsx but not georeferenced
    located_ids = set(gdf['UNIQUE_ID'])
    unlocated = df_all[~df_all['UNIQUE_ID'].isin(located_ids)].copy()
    print(f"  Métis located: {len(gdf_joined)} | unlocated: {len(unlocated)}")

    gdf_joined = gdf_joined.to_crs(TARGET_CRS)
    return gdf_joined, df_all, unlocated


def load_reference_layers():
    """Load boundary changes and CD_1921 as reference layers."""
    changes = gpd.read_file(
        os.path.join(SASK_RESERVES_DIR, 'Reserve_Boundary_Changes.geojson')
    ).to_crs(TARGET_CRS)
    cd_1921 = gpd.read_file(
        os.path.join(SASK_RESERVES_DIR, 'Reserves_CD_1921.geojson')
    ).to_crs(TARGET_CRS)
    print(f"  Boundary changes: {len(changes)} | Reserve CD 1921: {len(cd_1921)}")
    return changes, cd_1921


# =============================================================================
# Validation
# =============================================================================

def validate(surrenders_gdf, reserves_master_df, neo4j_df):
    print("\n--- Validation ---")

    # Surrender ↔ master table join check
    surr_ids = set(surrenders_gdf['UNIQUE_ID_BASE'].dropna())
    master_ids = set(reserves_master_df['UNIQUE_ID'].dropna())
    unmatched = surr_ids - master_ids
    if unmatched:
        print(f"  WARNING: {len(unmatched)} surrender IDs not in master table: {sorted(unmatched)}")
    else:
        print(f"  Surrender ↔ master table: all {len(surr_ids)} IDs matched")

    # Null surrender years
    null_yr = surrenders_gdf['year_surr_clean'].isna().sum()
    print(f"  Surrender year nulls: {null_yr} of {len(surrenders_gdf)}")

    # Null founded years
    null_founded = neo4j_df['founded'].isna().sum()
    print(f"  Settlement 'founded' nulls: {null_founded} of {len(neo4j_df)}")

    print(f"  All layers reprojected to {TARGET_CRS}: confirmed")


# =============================================================================
# Main
# =============================================================================

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    print("=" * 50)
    print("Phase 0: Data Preparation")
    print("=" * 50)

    print("\n[1/7] Neo4j settlements")
    neo4j_df = get_neo4j_settlements()

    print("\n[2/7] Urban municipalities")
    urban_gdf = load_urban_municipalities(neo4j_df)

    print("\n[3/7] Reserve surrenders")
    surrenders_gdf = load_surrenders()

    print("\n[4/7] Initial reserve survey")
    initial_gdf = load_initial_survey()

    print("\n[5/7] Reserves master table")
    reserves_master_df, surrenders_long_df = load_reserves_master()

    print("\n[6/7] Métis communities")
    metis_gdf, metis_full_df, metis_unlocated_df = load_metis_communities()

    print("\n[7/7] Reference layers")
    boundary_changes_gdf, reserves_cd_gdf = load_reference_layers()

    validate(surrenders_gdf, reserves_master_df, neo4j_df)

    print("\n--- Writing outputs ---")

    urban_gdf.to_file(os.path.join(DATA_DIR, 'urban_429.gpkg'), driver='GPKG')
    print(f"  urban_429.gpkg ({len(urban_gdf)} features)")

    surrenders_gdf.to_file(os.path.join(DATA_DIR, 'surrenders_clean.gpkg'), driver='GPKG')
    print(f"  surrenders_clean.gpkg ({len(surrenders_gdf)} features)")

    initial_gdf.to_file(os.path.join(DATA_DIR, 'reserves_initial.gpkg'), driver='GPKG')
    print(f"  reserves_initial.gpkg ({len(initial_gdf)} features)")

    reserves_master_df.to_csv(os.path.join(DATA_DIR, 'reserves_master.csv'), index=False)
    print(f"  reserves_master.csv ({len(reserves_master_df)} rows)")

    surrenders_long_df.to_csv(os.path.join(DATA_DIR, 'surrenders_long.csv'), index=False)
    print(f"  surrenders_long.csv ({len(surrenders_long_df)} rows)")

    metis_gdf.to_file(os.path.join(DATA_DIR, 'metis_located.gpkg'), driver='GPKG')
    print(f"  metis_located.gpkg ({len(metis_gdf)} features)")

    metis_full_df.to_csv(os.path.join(DATA_DIR, 'metis_full.csv'), index=False)
    print(f"  metis_full.csv ({len(metis_full_df)} rows)")

    metis_unlocated_df.to_csv(os.path.join(DATA_DIR, 'metis_unlocated.csv'), index=False)
    print(f"  metis_unlocated.csv ({len(metis_unlocated_df)} rows)")

    neo4j_df.to_csv(os.path.join(DATA_DIR, 'neo4j_settlements.csv'), index=False)
    print(f"  neo4j_settlements.csv ({len(neo4j_df)} rows)")

    print("\n" + "=" * 50)
    print("Phase 0 complete.")
    print("=" * 50)


if __name__ == '__main__':
    main()
