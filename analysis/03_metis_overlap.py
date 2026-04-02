#!/usr/bin/env python3
"""
Phase 3: Métis Overlap Analysis
Identifies spatial co-location and temporal overlap between Métis communities
and urban municipalities, and profiles road allowance communities.

Depends on: Phase 0 outputs in analysis/data/
Outputs:
  analysis/03_metis_results.xlsx  — 5-sheet Métis overlap workbook
"""

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
METIS_DIR = os.path.join(BASE_DIR, 'SK_Metis_Communities')

# Name pairs where a Métis community name corresponds to a known urban municipality.
# Checked against both datasets — these are the candidates for displacement analysis.
KNOWN_OVERLAP_NAMES = {
    'Regina': 'Regina',
    'Saskatoon': 'Saskatoon',
    'Prince Albert': 'Prince Albert',
    'Battleford': 'Battleford',
    'North Battleford': 'North Battleford',
    'Moose Jaw': 'Moose Jaw',
    'Estevan': 'Estevan',
    'Qu\'Appelle': 'Qu\'Appelle',
    'Portage la Prairie': 'Portage la Prairie',
    'Duck Lake': 'Duck Lake',
    'Lebret': 'Lebret',
}


# =============================================================================
# Helpers
# =============================================================================

def name_matches_municipality(community_name, muni_names_set):
    """Return True if community_name partially matches any municipal name."""
    if not isinstance(community_name, str):
        return False
    cn_lower = community_name.lower().strip()
    for m in muni_names_set:
        if not isinstance(m, str):
            continue
        m_lower = m.lower().strip()
        if cn_lower in m_lower or m_lower in cn_lower:
            return True
    return False


def find_matching_municipality(community_name, urban_gdf):
    """Return the TCPUID and name of the closest matching municipality by name."""
    if not isinstance(community_name, str):
        return None, None
    cn_lower = community_name.lower().strip()
    for _, row in urban_gdf.iterrows():
        mname = str(row.get('Name_CSD_1921', '') or '')
        if cn_lower in mname.lower() or mname.lower() in cn_lower:
            return row['TCPUID_CSD_1921'], row['Name_CSD_1921']
    return None, None


def clean_year(val):
    """Convert a year value to int, handling floats and strings with ~."""
    if pd.isna(val):
        return None
    s = str(val).replace('~', '').replace('c.', '').strip()
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


# =============================================================================
# Main analysis
# =============================================================================

def main():
    print("=" * 55)
    print("Phase 3: Métis Overlap Analysis")
    print("=" * 55)

    print("\n[1/5] Loading inputs")
    metis_gdf = gpd.read_file(os.path.join(DATA_DIR, 'metis_located.gpkg'))
    urban_gdf = gpd.read_file(os.path.join(DATA_DIR, 'urban_429.gpkg'))
    metis_full_df = pd.read_csv(os.path.join(DATA_DIR, 'metis_full.csv'))
    metis_unlocated_df = pd.read_csv(os.path.join(DATA_DIR, 'metis_unlocated.csv'))

    print(f"  Métis located: {len(metis_gdf)}")
    print(f"  Métis unlocated: {len(metis_unlocated_df)}")
    print(f"  Urban municipalities: {len(urban_gdf)}")

    assert metis_gdf.crs.to_epsg() == 3347
    assert urban_gdf.crs.to_epsg() == 3347

    # --- Clean year fields ---
    for col in ['Y_FOUND', 'Y_DEPART']:
        if col in metis_gdf.columns:
            metis_gdf[col + '_clean'] = metis_gdf[col].apply(clean_year)

    print("\n[2/5] Computing distances from Métis communities to municipality boundaries")

    metis_geoms = metis_gdf.geometry.values
    urban_geoms = urban_gdf.geometry.values

    # Distance matrix: (42 × 429)
    dist_matrix = np.empty((len(metis_gdf), len(urban_gdf)), dtype=np.float64)
    within_matrix = np.zeros((len(metis_gdf), len(urban_gdf)), dtype=bool)

    for j, ug in enumerate(urban_geoms):
        dist_matrix[:, j] = shapely.distance(metis_geoms, ug)
        within_matrix[:, j] = shapely.within(metis_geoms, ug)

    # Per-community proximity fields
    proximity_records = []
    muni_names_set = set(urban_gdf['Name_CSD_1921'].dropna())

    for i in range(len(metis_gdf)):
        row = metis_gdf.iloc[i]
        nearest_j = int(dist_matrix[i].argmin())
        nearest_muni = urban_gdf.iloc[nearest_j]
        within_any = bool(within_matrix[i].any())
        if within_any:
            containing_j = int(np.where(within_matrix[i])[0][0])
            containing_muni_name = urban_gdf.iloc[containing_j]['Name_CSD_1921']
            containing_muni_tcpuid = urban_gdf.iloc[containing_j]['TCPUID_CSD_1921']
        else:
            containing_muni_name = None
            containing_muni_tcpuid = None

        name_match_tcpuid, name_match_muni = find_matching_municipality(
            row.get('community_name'), urban_gdf
        )

        proximity_records.append({
            'UNIQUE_ID': row['UNIQUE_ID'],
            'community_name': row.get('community_name'),
            'TYPE': row.get('TYPE'),
            'Y_FOUND': row.get('Y_FOUND'),
            'Y_FOUND_clean': row.get('Y_FOUND_clean'),
            'Y_DEPART': row.get('Y_DEPART'),
            'Y_DEPART_clean': row.get('Y_DEPART_clean'),
            'POP_1860': row.get('POP_1860'),
            'POP_1880': row.get('POP_1880'),
            'POP_1900': row.get('POP_1900'),
            'POP_1921_CSD': row.get('POP_1921_CSD'),
            'POP_1940': row.get('POP-1940'),
            'nearest_muni_name': nearest_muni['Name_CSD_1921'],
            'nearest_muni_tcpuid': nearest_muni['TCPUID_CSD_1921'],
            'nearest_muni_dist_m': round(float(dist_matrix[i, nearest_j]), 1),
            'within_muni': within_any,
            'containing_muni_name': containing_muni_name,
            'containing_muni_tcpuid': containing_muni_tcpuid,
            'name_match_muni': name_match_muni,
            'name_match_tcpuid': name_match_tcpuid,
            'is_road_allowance': str(row.get('TYPE', '')).strip().lower() == 'road allowance',
            'notes': row.get('NOTES'),
        })

    proximity_df = pd.DataFrame(proximity_records)
    print(f"  Communities within a municipal boundary: {proximity_df['within_muni'].sum()}")
    print(f"  Name matches with urban municipalities: {proximity_df['name_match_muni'].notna().sum()}")
    print(f"  Road allowance communities: {proximity_df['is_road_allowance'].sum()}")

    print("\n[3/5] Building displacement case profiles")

    # Displacement cases: name match OR within a municipality boundary
    disp_mask = proximity_df['name_match_muni'].notna() | proximity_df['within_muni']
    displacement_df = proximity_df[disp_mask].copy()

    # Join urban founding year for side-by-side timeline
    neo_path = os.path.join(DATA_DIR, 'neo4j_settlements.csv')
    neo_df = pd.read_csv(neo_path)
    neo_df = neo_df.drop_duplicates(subset='census_id', keep='first')
    neo_df['founded_num'] = pd.to_numeric(neo_df['founded'], errors='coerce')
    neo_df['incorporated_num'] = pd.to_numeric(neo_df['incorporated'], errors='coerce')
    neo_df['muni_effective_founded'] = neo_df['founded_num'].combine_first(neo_df['incorporated_num'])

    # Join on name_match_tcpuid (prefer named match) or containing_muni_tcpuid
    displacement_df['join_tcpuid'] = displacement_df['name_match_tcpuid'].combine_first(
        displacement_df['containing_muni_tcpuid']
    )
    displacement_df = displacement_df.merge(
        neo_df[['census_id', 'muni_effective_founded']],
        left_on='join_tcpuid', right_on='census_id', how='left'
    )

    # Displacement signal: Métis community founded before municipality AND departed
    # around or after municipal founding
    displacement_df['metis_preceded_muni'] = (
        (displacement_df['Y_FOUND_clean'] < displacement_df['muni_effective_founded'])
        .where(displacement_df['Y_FOUND_clean'].notna() &
               displacement_df['muni_effective_founded'].notna())
    )
    displacement_df['depart_after_muni_founded'] = (
        (displacement_df['Y_DEPART_clean'] >= displacement_df['muni_effective_founded'])
        .where(displacement_df['Y_DEPART_clean'].notna() &
               displacement_df['muni_effective_founded'].notna())
    )

    print(f"  Displacement case candidates: {len(displacement_df)}")
    print(f"  Métis community preceded municipality: "
          f"{displacement_df['metis_preceded_muni'].sum()}")

    print("\n[4/5] Road allowance profile")
    # Road allowance communities are in a separate geojson — not in Metis_Community.geojson
    ra_path = os.path.join(METIS_DIR, 'Metis_RoadAllowance.geojson')
    ra_gdf = gpd.read_file(ra_path)
    ra_gdf['geometry'] = ra_gdf['geometry'].apply(
        lambda g: shapely.force_2d(g) if g is not None else g
    )
    ra_gdf = ra_gdf.to_crs('EPSG:3347')

    # Join temporal data from metis_full
    ra_gdf = ra_gdf.merge(
        metis_full_df[['UNIQUE_ID', 'TYPE', 'Y_FOUND', 'Y_DEPART', 'LOCATION',
                        'POP_1860', 'POP_1880', 'POP_1900', 'POP_1921_CSD',
                        'POP-1940', 'NOTES']].rename(columns={'NAME': 'community_name_full'}),
        on='UNIQUE_ID', how='left'
    )
    ra_gdf['Y_FOUND_clean'] = ra_gdf['Y_FOUND'].apply(clean_year)
    ra_gdf['Y_DEPART_clean'] = ra_gdf['Y_DEPART'].apply(clean_year)

    # Compute distance to nearest urban municipality
    ra_geoms = ra_gdf.geometry.values
    ra_dist = np.empty((len(ra_gdf), len(urban_gdf)), dtype=np.float64)
    for j, ug in enumerate(urban_geoms):
        ra_dist[:, j] = shapely.distance(ra_geoms, ug)

    road_allowance_records = []
    for i in range(len(ra_gdf)):
        row = ra_gdf.iloc[i]
        nearest_j = int(ra_dist[i].argmin())
        nearest_muni = urban_gdf.iloc[nearest_j]
        road_allowance_records.append({
            'community_name': row.get('NAME'),
            'UNIQUE_ID': row['UNIQUE_ID'],
            'LOCATION': row.get('LOCATION'),
            'Y_FOUND_clean': row.get('Y_FOUND_clean'),
            'Y_DEPART_clean': row.get('Y_DEPART_clean'),
            'nearest_muni_name': nearest_muni['Name_CSD_1921'],
            'nearest_muni_tcpuid': nearest_muni['TCPUID_CSD_1921'],
            'nearest_muni_dist_m': round(float(ra_dist[i, nearest_j]), 1),
            'POP_1860': row.get('POP_1860'),
            'POP_1880': row.get('POP_1880'),
            'POP_1900': row.get('POP_1900'),
            'POP_1921_CSD': row.get('POP_1921_CSD'),
            'POP_1940': row.get('POP-1940'),
            'notes': row.get('NOTES'),
        })
    road_allowance_df = pd.DataFrame(road_allowance_records)

    print(f"  Road allowance communities: {len(road_allowance_df)}")
    if len(road_allowance_df):
        print(f"  Median distance to nearest municipality: "
              f"{road_allowance_df['nearest_muni_dist_m'].median():.0f} m")
        print(f"  All distances (m): {sorted(road_allowance_df['nearest_muni_dist_m'].tolist())}")

    print("\n[5/5] Writing outputs")

    # Unlocated — add TYPE and LOCATION columns for reference
    unlocated_cols = [c for c in ['UNIQUE_ID', 'NAME', 'TYPE', 'LOCATION', 'Y_FOUND',
                                   'Y_DEPART', 'NOTES'] if c in metis_unlocated_df.columns]
    unlocated_display = metis_unlocated_df[unlocated_cols].copy()
    road_allowance_unlocated = unlocated_display[
        unlocated_display.get('TYPE', pd.Series(dtype=str)).str.lower().str.strip()
        == 'road allowance'
    ] if 'TYPE' in unlocated_display.columns else pd.DataFrame()

    disp_cols = [
        'community_name', 'TYPE', 'Y_FOUND_clean', 'Y_DEPART_clean',
        'name_match_muni', 'within_muni', 'containing_muni_name',
        'muni_effective_founded',
        'metis_preceded_muni', 'depart_after_muni_founded',
        'nearest_muni_dist_m',
        'POP_1860', 'POP_1880', 'POP_1900', 'POP_1921_CSD', 'POP_1940',
        'UNIQUE_ID', 'notes',
    ]
    disp_cols = [c for c in disp_cols if c in displacement_df.columns]

    road_cols = [
        'community_name', 'UNIQUE_ID', 'LOCATION',
        'Y_FOUND_clean', 'Y_DEPART_clean',
        'nearest_muni_name', 'nearest_muni_tcpuid', 'nearest_muni_dist_m',
        'POP_1860', 'POP_1880', 'POP_1900', 'POP_1921_CSD', 'POP_1940',
        'notes',
    ]
    road_cols = [c for c in road_cols if c in road_allowance_df.columns]

    prox_cols = [
        'community_name', 'UNIQUE_ID', 'TYPE',
        'Y_FOUND_clean', 'Y_DEPART_clean',
        'nearest_muni_name', 'nearest_muni_tcpuid', 'nearest_muni_dist_m',
        'within_muni', 'name_match_muni',
        'is_road_allowance',
        'POP_1860', 'POP_1880', 'POP_1900', 'POP_1921_CSD', 'POP_1940',
        'notes',
    ]
    prox_cols = [c for c in prox_cols if c in proximity_df.columns]

    methodology_rows = [
        ['Parameter', 'Value'],
        ['Métis communities (georeferenced)', str(len(metis_gdf))],
        ['Métis communities (unlocated)', str(len(metis_unlocated_df))],
        ['Urban municipalities', str(len(urban_gdf))],
        ['CRS for distance calculation', 'EPSG:3347 (NAD83 / Statistics Canada Lambert)'],
        ['Distance type', 'Point to polygon boundary (0 if point is inside polygon)'],
        ['Displacement case criteria', 'Community name matches municipal name (substring) OR community point falls within municipal polygon'],
        ['Displacement signal', 'Métis Y_FOUND < municipal effective_founded AND Y_DEPART >= municipal effective_founded'],
        ['Road allowance identification', 'TYPE field == "Road Allowance" in Métis_Communities.xlsx'],
        ['Caveat: 71 unlocated communities', 'Cannot be included in spatial analysis — road allowance communities are likely underrepresented in georeferenced set'],
        ['Caveat: Y_FOUND / Y_DEPART', 'Approximate dates; wintering sites have highest precision'],
        ['Caveat: name matching', 'String substring match only; manual verification required for each displacement case'],
        ['Caveat: within_muni', 'Uses 1921 municipal boundary extent — boundary may postdate Métis presence'],
    ]
    methodology_df = pd.DataFrame(methodology_rows[1:], columns=methodology_rows[0])

    out_xlsx = os.path.join(OUT_DIR, '03_metis_results.xlsx')
    with pd.ExcelWriter(out_xlsx, engine='openpyxl') as writer:
        displacement_df[disp_cols].to_excel(writer, sheet_name='Displacement_Cases', index=False)
        road_allowance_df[road_cols].to_excel(writer, sheet_name='Road_Allowance_Profile', index=False)
        unlocated_display.to_excel(writer, sheet_name='Unlocated_Communities', index=False)
        proximity_df[prox_cols].sort_values('nearest_muni_dist_m').to_excel(
            writer, sheet_name='All_Located_Proximity', index=False
        )
        methodology_df.to_excel(writer, sheet_name='Methodology', index=False)

    print(f"  {out_xlsx}")
    print(f"    Displacement_Cases: {len(displacement_df)} rows")
    print(f"    Road_Allowance_Profile: {len(road_allowance_df)} rows")
    print(f"    Unlocated_Communities: {len(unlocated_display)} rows")
    print(f"    All_Located_Proximity: {len(proximity_df)} rows")

    print("\n" + "=" * 55)
    print("Phase 3 complete.")
    print("=" * 55)


if __name__ == '__main__':
    main()
