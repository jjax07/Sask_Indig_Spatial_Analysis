#!/usr/bin/env python3
"""
Phase 1: Spatial Proximity Analysis
For each of the 429 urban municipalities, computes distances to all 54 surrendered
reserve parcels and derives temporal sequencing fields.

Depends on: Phase 0 outputs in analysis/data/
Outputs:
  analysis/01_proximity_results.xlsx  — 6-sheet ranked results workbook
  analysis/01_proximity_map.geojson   — 429 municipalities with proximity fields, EPSG:4326
"""

import json
import os
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'analysis', 'data')
OUT_DIR = os.path.join(BASE_DIR, 'analysis')

DIST_IMMEDIATE = 5_000    # 5 km
DIST_NEAR_URBAN = 25_000  # 25 km


# =============================================================================
# Helpers
# =============================================================================

def load_neo4j_settlements():
    """Load neo4j_settlements.csv and deduplicate on census_id.

    Phase 0 returns 818 rows because each Settlement can have multiple IS_TYPE
    relationships. Deduplicate here, aggregating commercial_type as a
    comma-joined string of distinct values. All other fields are stable per
    Settlement so we take first non-null.
    """
    df = pd.read_csv(os.path.join(DATA_DIR, 'neo4j_settlements.csv'))
    print(f"  Neo4j: {len(df)} rows before dedup")

    # Aggregate commercial_type; take first non-null for all other fields
    def first_non_null(s):
        s = s.dropna()
        return s.iloc[0] if len(s) else None

    agg_rules = {c: first_non_null for c in df.columns if c not in ('census_id', 'commercial_type')}
    agg_rules['commercial_type'] = lambda s: ', '.join(sorted(s.dropna().unique()))

    df_dedup = df.groupby('census_id', sort=False).agg(agg_rules).reset_index()
    print(f"  Neo4j: {len(df_dedup)} rows after dedup on census_id")

    # Effective founding year: prefer founded, fall back to incorporated
    df_dedup['founded_num'] = pd.to_numeric(df_dedup['founded'], errors='coerce')
    df_dedup['incorporated_num'] = pd.to_numeric(df_dedup['incorporated'], errors='coerce')
    df_dedup['effective_founded'] = df_dedup['founded_num'].combine_first(df_dedup['incorporated_num'])

    null_eff = df_dedup['effective_founded'].isna().sum()
    print(f"  Effective_founded nulls after fallback: {null_eff} of {len(df_dedup)}")

    return df_dedup


def build_distance_matrix(urban_gdf, surrenders_gdf):
    """Return (distance_matrix, overlap_matrix) both shaped (n_urban, n_surr).

    Distances are in metres (EPSG:3347). Overlap is True where geometries
    intersect or touch (distance == 0 and actual geometric intersection).
    """
    urban_geoms = urban_gdf.geometry.values
    surr_geoms = surrenders_gdf.geometry.values
    n_u = len(urban_geoms)
    n_s = len(surr_geoms)

    dist_matrix = np.empty((n_u, n_s), dtype=np.float64)
    overlap_matrix = np.zeros((n_u, n_s), dtype=bool)

    for j, sg in enumerate(surr_geoms):
        dist_matrix[:, j] = shapely.distance(urban_geoms, sg)
        overlap_matrix[:, j] = shapely.intersects(urban_geoms, sg)

    return dist_matrix, overlap_matrix


def build_proximity_record(i, dist_row, overlap_row, surrenders_gdf):
    """Build the proximity fields for municipality at index i."""
    nearest_j = int(dist_row.argmin())
    surr = surrenders_gdf.iloc[nearest_j]

    mask_5km = dist_row <= DIST_IMMEDIATE
    mask_25km = dist_row <= DIST_NEAR_URBAN

    # JSON list of all parcels within 25 km
    nearby = []
    for j in np.where(mask_25km)[0]:
        s = surrenders_gdf.iloc[int(j)]
        nearby.append({
            'UNIQUE_ID': s['UNIQUE_ID'],
            'reserve': s['RSRVE_NAME'],
            'year': int(s['year_surr_clean']) if pd.notna(s['year_surr_clean']) else None,
            'dist_m': round(float(dist_row[j]), 1),
            'acres': float(s['ACRES_SURR']) if pd.notna(s.get('ACRES_SURR')) else None,
            'notes': s.get('Notes') or s.get('NOTES_1') or None,
        })
    nearby.sort(key=lambda x: x['dist_m'])

    return {
        'min_dist_m': round(float(dist_row[nearest_j]), 1),
        'nearest_surrender_uid': surr['UNIQUE_ID'],
        'nearest_surrender_reserve': surr['RSRVE_NAME'],
        'nearest_surrender_year': int(surr['year_surr_clean']) if pd.notna(surr['year_surr_clean']) else None,
        'nearest_surrender_acres': float(surr['ACRES_SURR']) if pd.notna(surr.get('ACRES_SURR')) else None,
        'nearest_surrender_notes': (surr.get('Notes') or '').strip() or None,
        'n_surrenders_5km': int(mask_5km.sum()),
        'n_surrenders_25km': int(mask_25km.sum()),
        'overlap_flag': bool(overlap_row.any()),
        'all_nearby_surrenders': json.dumps(nearby) if nearby else '[]',
    }


def add_temporal_columns(results_df, neo4j_df):
    """Join effective_founded from neo4j and compute temporal gap columns."""
    neo4j_sub = neo4j_df[['census_id', 'effective_founded', 'founded_num',
                           'incorporated_num', 'commercial_type',
                           'population_1921']].copy()
    merged = results_df.merge(neo4j_sub, left_on='TCPUID_CSD_1921',
                              right_on='census_id', how='left')

    merged['nearest_surrender_year'] = pd.to_numeric(
        merged['nearest_surrender_year'], errors='coerce'
    )
    merged['effective_founded'] = pd.to_numeric(
        merged['effective_founded'], errors='coerce'
    )

    # years_gap: positive = surrender happened after municipal founding
    #            negative = municipality founded after surrender
    merged['years_gap'] = merged['nearest_surrender_year'] - merged['effective_founded']

    merged['founding_before_surrender'] = (
        merged['effective_founded'] < merged['nearest_surrender_year']
    ).where(
        merged['effective_founded'].notna() & merged['nearest_surrender_year'].notna()
    )

    merged['surrender_before_founding'] = (
        merged['nearest_surrender_year'] < merged['effective_founded']
    ).where(
        merged['effective_founded'].notna() & merged['nearest_surrender_year'].notna()
    )

    # Distance band (categorical for visualisation)
    def dist_band(d):
        if d == 0:
            return 'Overlap'
        elif d <= DIST_IMMEDIATE:
            return 'Within 5km'
        elif d <= DIST_NEAR_URBAN:
            return 'Within 25km'
        else:
            return 'Beyond 25km'

    merged['min_dist_band'] = merged['min_dist_m'].apply(dist_band)

    return merged


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 55)
    print("Phase 1: Spatial Proximity Analysis")
    print("=" * 55)

    print("\n[1/5] Loading Phase 0 outputs")
    urban_gdf = gpd.read_file(os.path.join(DATA_DIR, 'urban_429.gpkg'))
    surrenders_gdf = gpd.read_file(os.path.join(DATA_DIR, 'surrenders_clean.gpkg'))
    neo4j_df = load_neo4j_settlements()

    print(f"  Urban municipalities: {len(urban_gdf)}")
    print(f"  Surrender parcels: {len(surrenders_gdf)}")
    assert urban_gdf.crs.to_epsg() == 3347, "urban_429 must be EPSG:3347"
    assert surrenders_gdf.crs.to_epsg() == 3347, "surrenders_clean must be EPSG:3347"

    print("\n[2/5] Building distance matrix (429 × 54 = 23,166 pairs)")
    dist_matrix, overlap_matrix = build_distance_matrix(urban_gdf, surrenders_gdf)
    print(f"  Distance matrix shape: {dist_matrix.shape}")
    print(f"  Overlapping pairs: {overlap_matrix.sum()}")
    print(f"  Municipalities with any overlap: {(overlap_matrix.any(axis=1)).sum()}")
    print(f"  Municipalities within 5 km of any surrender: "
          f"{((dist_matrix <= DIST_IMMEDIATE).any(axis=1)).sum()}")
    print(f"  Municipalities within 25 km of any surrender: "
          f"{((dist_matrix <= DIST_NEAR_URBAN).any(axis=1)).sum()}")

    print("\n[3/5] Computing per-municipality proximity fields")
    records = []
    for i in range(len(urban_gdf)):
        row_meta = {
            'TCPUID_CSD_1921': urban_gdf.iloc[i]['TCPUID_CSD_1921'],
            'Name_CSD_1921': urban_gdf.iloc[i]['Name_CSD_1921'],
            'CSD_TYPE': urban_gdf.iloc[i]['CSD_TYPE'],
            'POP_TOT_1921': urban_gdf.iloc[i]['POP_TOT_1921'],
        }
        prox = build_proximity_record(i, dist_matrix[i], overlap_matrix[i], surrenders_gdf)
        records.append({**row_meta, **prox})

    results_df = pd.DataFrame(records)

    print("\n[4/5] Adding temporal gap columns")
    results_df = add_temporal_columns(results_df, neo4j_df)
    results_df = results_df.sort_values('min_dist_m').reset_index(drop=True)

    # Summary statistics
    n_before = results_df['founding_before_surrender'].sum()
    n_after = results_df['surrender_before_founding'].sum()
    print(f"  Pressure-then-surrender candidates (founding_before_surrender): {int(n_before)}")
    print(f"  Surrender-then-municipality: {int(n_after)}")
    print(f"  Temporal relationship indeterminate (null founded or surrender year): "
          f"{results_df['years_gap'].isna().sum()}")

    print("\n[5/5] Writing outputs")

    # --- Excel workbook ---
    out_xlsx = os.path.join(OUT_DIR, '01_proximity_results.xlsx')

    # Columns for display (all_nearby_surrenders is long; keep in Ranked_All)
    display_cols = [
        'TCPUID_CSD_1921', 'Name_CSD_1921', 'CSD_TYPE', 'POP_TOT_1921',
        'commercial_type', 'effective_founded', 'incorporated_num',
        'min_dist_m', 'min_dist_band',
        'nearest_surrender_uid', 'nearest_surrender_reserve',
        'nearest_surrender_year', 'nearest_surrender_acres', 'nearest_surrender_notes',
        'n_surrenders_5km', 'n_surrenders_25km', 'overlap_flag',
        'years_gap', 'founding_before_surrender', 'surrender_before_founding',
        'all_nearby_surrenders',
    ]
    # Only keep columns that exist (graceful if a column was dropped upstream)
    display_cols = [c for c in display_cols if c in results_df.columns]
    brief_cols = [c for c in display_cols if c != 'all_nearby_surrenders']

    within_5km = results_df[results_df['min_dist_m'] <= DIST_IMMEDIATE].copy()
    overlapping = results_df[results_df['overlap_flag'] == True].copy()
    pressure_df = results_df[results_df['founding_before_surrender'] == True].copy()
    after_surr_df = results_df[results_df['surrender_before_founding'] == True].copy()

    methodology_rows = [
        ['Parameter', 'Value'],
        ['CRS for distance calculation', 'EPSG:3347 (NAD83 / Statistics Canada Lambert)'],
        ['Distance: overlap / contiguous', '0 m (geometric intersection)'],
        ['Distance: immediate proximity', f'{DIST_IMMEDIATE:,} m ({DIST_IMMEDIATE//1000} km)'],
        ['Distance: near-urban influence', f'{DIST_NEAR_URBAN:,} m ({DIST_NEAR_URBAN//1000} km)'],
        ['Distance type', 'Polygon boundary-to-boundary (not centroid)'],
        ['Urban municipalities', f'{len(urban_gdf)} (filtered from 1921 SK CSD layer by Neo4j TCPUID)'],
        ['Surrender parcels', f'{len(surrenders_gdf)} (SK_ReserveSurrenders_1933.geojson)'],
        ['Surrender year field', 'year_surr_clean (YR_SUR primary; YEAR_SURR fallback; -99 treated as null)'],
        ['Municipal year field', 'effective_founded (founded primary; incorporated fallback)'],
        ['years_gap', 'nearest_surrender_year minus effective_founded; positive = surrender after founding'],
        ['founding_before_surrender', 'True where municipality founded before nearest surrender year (pressure → surrender signal)'],
        ['Caveat: municipal geometry', '1921 extent, not founding-year extent — overlap should be read as "later incorporated"'],
        ['Caveat: surrender coverage', '54 formal documented surrenders only; informal encroachments not captured'],
        ['Caveat: large cities', 'Large polygons (Regina, Prince Albert) show smaller distances to all features'],
    ]
    methodology_df = pd.DataFrame(methodology_rows[1:], columns=methodology_rows[0])

    with pd.ExcelWriter(out_xlsx, engine='openpyxl') as writer:
        results_df[display_cols].to_excel(writer, sheet_name='Ranked_All', index=False)
        within_5km[brief_cols].to_excel(writer, sheet_name='Within_5km', index=False)
        overlapping[brief_cols].to_excel(writer, sheet_name='Overlapping', index=False)
        pressure_df[brief_cols].sort_values('years_gap', ascending=False).to_excel(
            writer, sheet_name='Pressure_Then_Surrender', index=False
        )
        after_surr_df[brief_cols].sort_values('years_gap').to_excel(
            writer, sheet_name='Surrender_Then_Muni', index=False
        )
        methodology_df.to_excel(writer, sheet_name='Methodology', index=False)

    print(f"  {out_xlsx}")
    print(f"    Ranked_All: {len(results_df)} rows")
    print(f"    Within_5km: {len(within_5km)} rows")
    print(f"    Overlapping: {len(overlapping)} rows")
    print(f"    Pressure_Then_Surrender: {len(pressure_df)} rows")
    print(f"    Surrender_Then_Muni: {len(after_surr_df)} rows")

    # --- GeoJSON for visualisation (EPSG:4326) ---
    # Attach proximity fields to the urban polygon geometry
    viz_cols = [c for c in brief_cols if c != 'all_nearby_surrenders']
    urban_viz = urban_gdf[['TCPUID_CSD_1921', 'geometry']].merge(
        results_df[viz_cols], on='TCPUID_CSD_1921', how='left'
    )
    urban_viz = urban_viz.to_crs('EPSG:4326')

    out_geojson = os.path.join(OUT_DIR, '01_proximity_map.geojson')
    urban_viz.to_file(out_geojson, driver='GeoJSON')
    print(f"  {out_geojson} ({len(urban_viz)} features, EPSG:4326)")

    print("\n" + "=" * 55)
    print("Phase 1 complete.")
    print("=" * 55)


if __name__ == '__main__':
    main()
