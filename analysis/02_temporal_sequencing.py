#!/usr/bin/env python3
"""
Phase 2: Temporal Sequencing Analysis
Reconstructs the progressive reduction of each reserve near urban municipalities
and classifies reserve-municipality pairs by temporal relationship.

Depends on: Phase 0 outputs in analysis/data/, Phase 1 analysis/01_proximity_results.xlsx
Outputs:
  analysis/02_temporal_results.xlsx  — 6-sheet temporal analysis workbook
"""

import json
import os
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'analysis', 'data')
OUT_DIR = os.path.join(BASE_DIR, 'analysis')
KG_WORKBOOK = os.path.join(BASE_DIR, '..', 'KnowledgeGraph',
                           'JJack_Urban_Sask_Knowledge_Graph_Feb_2026.xlsx')

# Decade boundaries for acreage reduction summaries
DECADES = [
    ('pre_1900',  None, 1899),
    ('1900_1909', 1900, 1909),
    ('1910_1919', 1910, 1919),
    ('1920_1933', 1920, 1933),
]

# Type B concurrent window (years either side of major surrender)
CONCURRENT_WINDOW = 5


# =============================================================================
# Loaders
# =============================================================================

def load_proximity_results():
    """Load Phase 1 Ranked_All and explode all_nearby_surrenders into pairs."""
    path = os.path.join(OUT_DIR, '01_proximity_results.xlsx')
    df = pd.read_excel(path, sheet_name='Ranked_All')
    print(f"  Phase 1 results: {len(df)} municipalities")

    # Keep only municipalities within 25 km of at least one surrender parcel
    within_25 = df[df['n_surrenders_25km'] > 0].copy()
    print(f"  Within 25 km of surrender land: {len(within_25)}")

    # Explode the JSON list into one row per (municipality, surrender parcel) pair
    pairs = []
    for _, row in within_25.iterrows():
        nearby = json.loads(row.get('all_nearby_surrenders') or '[]')
        for s in nearby:
            pairs.append({
                'TCPUID': row['TCPUID_CSD_1921'],
                'muni_name': row['Name_CSD_1921'],
                'CSD_TYPE': row['CSD_TYPE'],
                'POP_TOT_1921': row['POP_TOT_1921'],
                'muni_effective_founded': row.get('effective_founded'),
                'muni_incorporated': row.get('incorporated_num'),
                'UNIQUE_ID_parcel': s['UNIQUE_ID'],
                # Strip sub-parcel suffix to match master table
                'UNIQUE_ID_base': s['UNIQUE_ID'].split('-')[0],
                'reserve_name': s['reserve'],
                'surrender_year': s.get('year'),
                'dist_m': s['dist_m'],
                'surrender_notes': s.get('notes'),
            })

    pairs_df = pd.DataFrame(pairs)
    print(f"  Municipality–surrender pairs within 25 km: {len(pairs_df)}")
    return within_25, pairs_df


def load_railway_data():
    """Load railway arrival years from the KG workbook."""
    kg = pd.read_excel(KG_WORKBOOK, sheet_name='Sheet1',
                       usecols=['V1T27_1921', 'Railway_arrives'])
    kg = kg.rename(columns={'V1T27_1921': 'TCPUID', 'Railway_arrives': 'railway_arrival'})
    kg['railway_arrival'] = pd.to_numeric(kg['railway_arrival'], errors='coerce')
    nulls = kg['railway_arrival'].isna().sum()
    print(f"  Railway arrival: {len(kg) - nulls} of {len(kg)} have data")
    return kg


def load_surrender_long():
    """Load the long-format year-by-year surrender acreage table."""
    df = pd.read_csv(os.path.join(DATA_DIR, 'surrenders_long.csv'))
    print(f"  Surrenders long: {len(df)} reserve-year events across "
          f"{df['UNIQUE_ID'].nunique()} reserves")
    return df


# =============================================================================
# Analysis
# =============================================================================

def build_reserve_decade_summary(long_df, affected_ids):
    """Compute cumulative and per-decade surrender acreage for each affected reserve."""
    sub = long_df[long_df['UNIQUE_ID'].isin(affected_ids)].copy()

    rows = []
    for uid, grp in sub.groupby('UNIQUE_ID'):
        rec = {
            'UNIQUE_ID': uid,
            'reserve_name': grp['RSRV_NAME'].iloc[0],
            'orig_acres': grp['ORIG_ACRE'].iloc[0] if 'ORIG_ACRE' in grp.columns else None,
            'total_surrendered_1933': grp['acres_surrendered'].sum(),
            'first_surrender_year': int(grp['year'].min()),
            'last_surrender_year': int(grp['year'].max()),
            'major_surrender_year': int(grp.loc[grp['acres_surrendered'].idxmax(), 'year']),
            'major_surrender_acres': float(grp['acres_surrendered'].max()),
            'data_certainty': grp['Data_Certainty'].iloc[0] if 'Data_Certainty' in grp.columns else None,
        }
        # Per-decade acreage
        cumulative = 0
        for label, yr_from, yr_to in DECADES:
            if yr_from is None:
                mask = grp['year'] <= yr_to
            else:
                mask = (grp['year'] >= yr_from) & (grp['year'] <= yr_to)
            decade_acres = float(grp.loc[mask, 'acres_surrendered'].sum())
            rec[f'acres_{label}'] = decade_acres
            cumulative += decade_acres
            rec[f'cumulative_by_{yr_to}'] = cumulative

        # Percentage of original acreage surrendered by each decade
        if rec['orig_acres'] and rec['orig_acres'] > 0:
            for label, _, yr_to in DECADES:
                pct = rec[f'cumulative_by_{yr_to}'] / rec['orig_acres'] * 100
                rec[f'pct_surrendered_by_{yr_to}'] = round(pct, 1)

        rows.append(rec)

    return pd.DataFrame(rows).sort_values('UNIQUE_ID')


def classify_temporal_type(row):
    """Classify a reserve-municipality pair as Type A, B, C, or Indeterminate.

    Type A — Pre-emptive settlement:
        Municipality founded OR railway arrived before first surrender on this reserve.
        Strongest candidate for Raibmon/Waiser "pressure then surrender" argument.

    Type B — Concurrent:
        Municipality founded within CONCURRENT_WINDOW years of the major surrender year.
        (Only assigned if not Type A.)

    Type C — Post-surrender settlement:
        Municipality founded after all surrenders on this reserve were complete.
        Consistent with conventional "opened land was then settled" narrative.

    Indeterminate: Insufficient year data.
    """
    founded = row.get('muni_effective_founded')
    railway = row.get('railway_arrival')
    first_surr = row.get('first_surrender_year')
    last_surr = row.get('last_surrender_year')
    major_surr = row.get('major_surrender_year')

    has_muni_year = pd.notna(founded)
    has_railway = pd.notna(railway)
    has_surr_years = pd.notna(first_surr) and pd.notna(last_surr)

    if not has_surr_years:
        return 'Indeterminate'

    # Type A: any settlement indicator predates first surrender
    muni_before = has_muni_year and founded < first_surr
    railway_before = has_railway and railway < first_surr
    if muni_before or railway_before:
        return 'A'

    # Type B: founded within window of major surrender (if not A)
    if has_muni_year and pd.notna(major_surr):
        if abs(founded - major_surr) <= CONCURRENT_WINDOW:
            return 'B'

    # Type C: founded after all surrenders complete
    if has_muni_year and founded > last_surr:
        return 'C'

    # Founded after first but before or during last surrender, more than 5 years
    # from major surrender → treat as concurrent but beyond window
    if has_muni_year:
        return 'B'

    return 'Indeterminate'


def build_timeline_table(pairs_df, railway_df, reserve_summary_df):
    """Build the combined per-pair timeline table with Type classification."""
    # Join railway arrival
    df = pairs_df.merge(railway_df, on='TCPUID', how='left')

    # Join reserve temporal data
    surr_cols = ['UNIQUE_ID', 'reserve_name', 'first_surrender_year',
                 'last_surrender_year', 'major_surrender_year', 'major_surrender_acres',
                 'orig_acres', 'total_surrendered_1933', 'data_certainty']
    surr_cols = [c for c in surr_cols if c in reserve_summary_df.columns]
    df = df.merge(
        reserve_summary_df[surr_cols].rename(columns={'UNIQUE_ID': 'UNIQUE_ID_base',
                                                       'reserve_name': 'reserve_name_master'}),
        on='UNIQUE_ID_base', how='left'
    )

    # Classify
    df['temporal_type'] = df.apply(classify_temporal_type, axis=1)

    # Gap from effective founding to first surrender (negative = muni predates)
    df['years_to_first_surrender'] = (
        pd.to_numeric(df['first_surrender_year'], errors='coerce') -
        pd.to_numeric(df['muni_effective_founded'], errors='coerce')
    )
    df['years_to_major_surrender'] = (
        pd.to_numeric(df['major_surrender_year'], errors='coerce') -
        pd.to_numeric(df['muni_effective_founded'], errors='coerce')
    )

    return df


def compute_dispossession_intensity(pairs_df, reserve_summary_df):
    """Compute per-reserve dispossession intensity: fraction of original land
    surrendered, restricted to reserves near at least one urban municipality."""
    affected = reserve_summary_df[
        reserve_summary_df['UNIQUE_ID'].isin(pairs_df['UNIQUE_ID_base'])
    ].copy()

    affected['pct_surrendered_total'] = (
        affected['total_surrendered_1933'] / affected['orig_acres'] * 100
    ).where(affected['orig_acres'].notna() & (affected['orig_acres'] > 0))

    # Count how many municipalities are within 25 km
    muni_counts = (
        pairs_df.groupby('UNIQUE_ID_base')['TCPUID']
        .nunique()
        .reset_index()
        .rename(columns={'TCPUID': 'n_munis_within_25km', 'UNIQUE_ID_base': 'UNIQUE_ID'})
    )
    affected = affected.merge(muni_counts, on='UNIQUE_ID', how='left')

    return affected.sort_values('pct_surrendered_total', ascending=False, na_position='last')


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 55)
    print("Phase 2: Temporal Sequencing Analysis")
    print("=" * 55)

    print("\n[1/5] Loading inputs")
    within_25_df, pairs_df = load_proximity_results()
    railway_df = load_railway_data()
    long_df = load_surrender_long()

    print("\n[2/5] Building reserve decade summary")
    affected_ids = set(pairs_df['UNIQUE_ID_base'].dropna())
    print(f"  Affected reserves (within 25 km of any municipality): {len(affected_ids)}")
    reserve_summary_df = build_reserve_decade_summary(long_df, affected_ids)
    print(f"  Reserve summary rows: {len(reserve_summary_df)}")

    # Reserves in pairs but missing from long table (no year-by-year data)
    missing_long = affected_ids - set(reserve_summary_df['UNIQUE_ID'])
    if missing_long:
        print(f"  WARNING: {len(missing_long)} reserves in pairs but not in surrenders_long: "
              f"{sorted(missing_long)}")

    print("\n[3/5] Building combined timeline table")
    timeline_df = build_timeline_table(pairs_df, railway_df, reserve_summary_df)

    type_counts = timeline_df['temporal_type'].value_counts()
    print(f"  Type A (pre-emptive): {type_counts.get('A', 0)}")
    print(f"  Type B (concurrent):  {type_counts.get('B', 0)}")
    print(f"  Type C (post-surrender): {type_counts.get('C', 0)}")
    print(f"  Indeterminate: {type_counts.get('Indeterminate', 0)}")

    print("\n[4/5] Computing dispossession intensity index")
    intensity_df = compute_dispossession_intensity(pairs_df, reserve_summary_df)

    print("\n[5/5] Writing outputs")

    type_a = timeline_df[timeline_df['temporal_type'] == 'A'].sort_values('years_to_first_surrender')
    type_b = timeline_df[timeline_df['temporal_type'] == 'B'].sort_values('years_to_major_surrender')
    type_c = timeline_df[timeline_df['temporal_type'] == 'C'].sort_values('years_to_major_surrender')

    # Clean column order for display
    timeline_cols = [
        'TCPUID', 'muni_name', 'CSD_TYPE', 'POP_TOT_1921',
        'muni_effective_founded', 'muni_incorporated', 'railway_arrival',
        'UNIQUE_ID_base', 'reserve_name',
        'first_surrender_year', 'last_surrender_year',
        'major_surrender_year', 'major_surrender_acres',
        'orig_acres', 'total_surrendered_1933',
        'dist_m', 'surrender_notes',
        'years_to_first_surrender', 'years_to_major_surrender',
        'temporal_type', 'data_certainty',
    ]
    timeline_cols = [c for c in timeline_cols if c in timeline_df.columns]

    decade_cols = [
        'UNIQUE_ID', 'reserve_name', 'orig_acres', 'total_surrendered_1933',
        'first_surrender_year', 'last_surrender_year',
        'major_surrender_year', 'major_surrender_acres',
        'acres_pre_1900', 'acres_1900_1909', 'acres_1910_1919', 'acres_1920_1933',
        'cumulative_by_1899', 'cumulative_by_1909', 'cumulative_by_1919', 'cumulative_by_1933',
        'pct_surrendered_by_1899', 'pct_surrendered_by_1909',
        'pct_surrendered_by_1919', 'pct_surrendered_by_1933',
        'data_certainty',
    ]
    decade_cols = [c for c in decade_cols if c in reserve_summary_df.columns]

    intensity_display_cols = [
        'UNIQUE_ID', 'reserve_name', 'orig_acres', 'total_surrendered_1933',
        'pct_surrendered_total', 'n_munis_within_25km',
        'first_surrender_year', 'last_surrender_year', 'data_certainty',
    ]
    intensity_display_cols = [c for c in intensity_display_cols if c in intensity_df.columns]

    methodology_rows = [
        ['Parameter', 'Value'],
        ['Affected reserves (within 25 km of any urban municipality)', str(len(affected_ids))],
        ['Municipality–reserve pairs analysed', str(len(timeline_df))],
        ['Decade bands', 'pre-1900, 1900–1909, 1910–1919, 1920–1933'],
        ['Type A — Pre-emptive settlement', 'Municipality founded OR railway arrived before first surrender year on associated reserve'],
        ['Type B — Concurrent', f'Municipality founded within ±{CONCURRENT_WINDOW} years of major surrender year (most acres in single year)'],
        ['Type C — Post-surrender', 'Municipality founded after last recorded surrender year'],
        ['Indeterminate', 'Insufficient year data for classification'],
        ['Type priority', 'A > B > C > Indeterminate (A takes precedence)'],
        ['years_to_first_surrender', 'first_surrender_year − muni_effective_founded; negative = municipality predates surrender'],
        ['Railway data source', 'JJack_Urban_Sask_Knowledge_Graph_Feb_2026.xlsx (Railway_arrives field)'],
        ['Surrender acreage source', 'surrenders_long.csv (melted from Sask_Reserves_1931.xlsx)'],
        ['Caveat: surrenders_long coverage', f'{len(long_df["UNIQUE_ID"].unique())} of ~113 reserves have year-by-year data'],
        ['Caveat: dispossession intensity', 'Total surrendered / original acres — not causal, contextual only'],
    ]
    methodology_df = pd.DataFrame(methodology_rows[1:], columns=methodology_rows[0])

    out_xlsx = os.path.join(OUT_DIR, '02_temporal_results.xlsx')
    with pd.ExcelWriter(out_xlsx, engine='openpyxl') as writer:
        timeline_df[timeline_cols].to_excel(writer, sheet_name='Timeline_Table', index=False)
        type_a[timeline_cols].to_excel(writer, sheet_name='Type_A_Cases', index=False)
        type_b[timeline_cols].to_excel(writer, sheet_name='Type_B_Cases', index=False)
        type_c[timeline_cols].to_excel(writer, sheet_name='Type_C_Cases', index=False)
        reserve_summary_df[decade_cols].to_excel(writer, sheet_name='Reserve_Reduction_Summary', index=False)
        intensity_df[intensity_display_cols].to_excel(writer, sheet_name='Dispossession_Intensity', index=False)
        methodology_df.to_excel(writer, sheet_name='Methodology', index=False)

    print(f"  {out_xlsx}")
    print(f"    Timeline_Table: {len(timeline_df)} rows")
    print(f"    Type_A_Cases: {len(type_a)} | Type_B_Cases: {len(type_b)} | "
          f"Type_C_Cases: {len(type_c)}")
    print(f"    Reserve_Reduction_Summary: {len(reserve_summary_df)} reserves")
    print(f"    Dispossession_Intensity: {len(intensity_df)} reserves")

    print("\n" + "=" * 55)
    print("Phase 2 complete.")
    print("=" * 55)


if __name__ == '__main__':
    main()
