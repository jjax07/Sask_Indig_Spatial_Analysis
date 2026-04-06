#!/usr/bin/env python3
"""
Phase 5: Neo4j Enrichment
Writes spatial analysis findings from Phases 1–3 back into the Neo4j graph
as properties on Settlement nodes, enabling combined Cypher queries across
commercial tier, founding timeline, and dispossession proximity.

Depends on:
  analysis/01_proximity_results.xlsx  (Phase 1)
  analysis/02_temporal_results.xlsx   (Phase 2)
  analysis/03_metis_results.xlsx      (Phase 3)

Outputs:
  analysis/05_enrichment_log.xlsx     — per-municipality summary of values written
  Writes directly to Neo4j Settlement nodes (bolt://localhost:7687)

New Settlement properties:
  min_dist_to_surrender_m   float   — boundary distance to nearest surrendered parcel (m)
  nearest_surrender_reserve string  — reserve name of nearest surrendered parcel
  nearest_surrender_year    int     — year of nearest surrender
  n_surrenders_5km          int     — count of surrender parcels within 5 km
  n_surrenders_25km         int     — count of surrender parcels within 25 km
  overlap_with_surrender    bool    — any surrender parcel geometrically overlaps municipality
  temporal_type             string  — A/B/C/Indeterminate/none (most pre-emptive across all pairs)
  metis_community_present   bool    — any located Métis community is nearest to this municipality
  nearest_metis_community   string  — name of closest associated Métis community
  nearest_metis_dist_m      float   — distance to that community (m)
"""

import os
import warnings

import numpy as np
import pandas as pd
from neo4j import GraphDatabase

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, 'analysis')

NEO4J_URI = 'bolt://localhost:7687'
NEO4J_PASSWORD = '11069173'

# Temporal type priority order (lower index = higher priority = more pre-emptive)
TYPE_PRIORITY = {'A': 0, 'B': 1, 'C': 2, 'Indeterminate': 3}


# =============================================================================
# Data loaders
# =============================================================================

def load_phase1():
    """Load Phase 1 proximity results — one row per municipality."""
    path = os.path.join(OUT_DIR, '01_proximity_results.xlsx')
    df = pd.read_excel(path, sheet_name='Ranked_All')
    print(f"  Phase 1: {len(df)} municipalities")

    keep = [
        'TCPUID_CSD_1921',
        'min_dist_m',
        'nearest_surrender_reserve',
        'nearest_surrender_year',
        'n_surrenders_5km',
        'n_surrenders_25km',
        'overlap_flag',
    ]
    df = df[keep].copy()
    df = df.rename(columns={'TCPUID_CSD_1921': 'tcpuid'})

    # Coerce numeric fields
    df['min_dist_m'] = pd.to_numeric(df['min_dist_m'], errors='coerce')
    df['nearest_surrender_year'] = pd.to_numeric(df['nearest_surrender_year'], errors='coerce')
    df['n_surrenders_5km'] = pd.to_numeric(df['n_surrenders_5km'], errors='coerce').astype('Int64')
    df['n_surrenders_25km'] = pd.to_numeric(df['n_surrenders_25km'], errors='coerce').astype('Int64')
    df['overlap_flag'] = df['overlap_flag'].astype(bool)

    return df


def load_phase2():
    """Load Phase 2 timeline table — one row per municipality×reserve pair.

    Reduce to one row per municipality by taking the most pre-emptive temporal
    type across all reserve pairs (priority: A > B > C > Indeterminate).
    Municipalities with no pairs in the 25 km window receive type 'none'.
    """
    path = os.path.join(OUT_DIR, '02_temporal_results.xlsx')
    df = pd.read_excel(path, sheet_name='Timeline_Table')
    print(f"  Phase 2: {len(df)} municipality×reserve pairs")

    df = df.rename(columns={'TCPUID': 'tcpuid'})

    def best_type(types):
        """Return the highest-priority temporal type from a series."""
        valid = [t for t in types if t in TYPE_PRIORITY]
        if not valid:
            return 'none'
        return min(valid, key=lambda t: TYPE_PRIORITY[t])

    type_per_muni = (
        df.groupby('tcpuid')['temporal_type']
        .apply(best_type)
        .reset_index()
        .rename(columns={'temporal_type': 'temporal_type'})
    )
    print(f"  Phase 2: {len(type_per_muni)} municipalities with proximity pairs")
    print(f"  Phase 2 type distribution:\n{type_per_muni['temporal_type'].value_counts().to_string()}")

    return type_per_muni


def load_phase3():
    """Load Phase 3 proximity table — one row per Métis community.

    For each municipality TCPUID that appears as the nearest municipality to at
    least one Métis community, record:
      - metis_community_present = True
      - nearest_metis_community = name of the closest of those communities
      - nearest_metis_dist_m = its distance

    Also check the Displacement_Cases sheet: municipalities with a name-matched
    Métis community get metis_community_present = True even if no Métis community
    lists them as 'nearest' (handles the within-boundary cases).
    """
    path = os.path.join(OUT_DIR, '03_metis_results.xlsx')

    # All located community proximity rows
    prox = pd.read_excel(path, sheet_name='All_Located_Proximity')
    print(f"  Phase 3 proximity: {len(prox)} Métis community rows")

    # Group by nearest_muni_tcpuid — find closest community per municipality
    prox_valid = prox[prox['nearest_muni_tcpuid'].notna()].copy()
    prox_valid['nearest_muni_dist_m'] = pd.to_numeric(prox_valid['nearest_muni_dist_m'], errors='coerce')

    per_muni = (
        prox_valid
        .sort_values('nearest_muni_dist_m')
        .groupby('nearest_muni_tcpuid', sort=False)
        .first()
        .reset_index()
        [['nearest_muni_tcpuid', 'community_name', 'nearest_muni_dist_m']]
        .rename(columns={
            'nearest_muni_tcpuid': 'tcpuid',
            'community_name': 'nearest_metis_community',
            'nearest_muni_dist_m': 'nearest_metis_dist_m',
        })
    )
    per_muni['metis_community_present'] = True

    # Also pull displacement cases (name-matched, may be within municipality)
    disp = pd.read_excel(path, sheet_name='Displacement_Cases')
    # Displacement cases have containing_muni_name but not always a TCPUID column.
    # Use the nearest_muni_tcpuid from the prox table via community name join.
    if 'nearest_muni_tcpuid' in disp.columns:
        disp_tcpuids = set(disp['nearest_muni_tcpuid'].dropna())
    else:
        # Fall back: match via community_name → nearest_muni_tcpuid in prox table
        disp_tcpuids = set(
            prox_valid[prox_valid['community_name'].isin(disp['community_name'])]
            ['nearest_muni_tcpuid']
        )

    # Any displacement-case municipality not already in per_muni → add with True flag only
    existing = set(per_muni['tcpuid'])
    extra_tcpuids = disp_tcpuids - existing
    if extra_tcpuids:
        extra_rows = pd.DataFrame({
            'tcpuid': list(extra_tcpuids),
            'nearest_metis_community': None,
            'nearest_metis_dist_m': None,
            'metis_community_present': True,
        })
        per_muni = pd.concat([per_muni, extra_rows], ignore_index=True)

    print(f"  Phase 3: {len(per_muni)} municipalities with associated Métis communities")
    return per_muni


# =============================================================================
# Merge
# =============================================================================

def build_enrichment_df(p1, p2, p3):
    """Merge Phase 1, 2, 3 data on TCPUID.

    All 429 municipalities appear in Phase 1. Phase 2 and 3 have subsets.
    Left-join to preserve all 429 rows.
    """
    df = p1.merge(p2, on='tcpuid', how='left')
    df = df.merge(p3, on='tcpuid', how='left')

    # Fill defaults for municipalities with no proximity pairs or Métis associations
    df['temporal_type'] = df['temporal_type'].fillna('none')
    df['metis_community_present'] = df['metis_community_present'].fillna(False).astype(bool)

    print(f"\n  Enrichment table: {len(df)} municipalities")
    print(f"  temporal_type distribution:\n{df['temporal_type'].value_counts().to_string()}")
    print(f"  metis_community_present: {df['metis_community_present'].sum()} municipalities")
    print(f"  overlap_with_surrender: {df['overlap_flag'].sum()} municipalities")

    return df


# =============================================================================
# Neo4j write
# =============================================================================

def clean_for_neo4j(val):
    """Convert pandas NA / numpy types to Python-native types for Neo4j driver."""
    if val is None:
        return None
    if isinstance(val, float) and np.isnan(val):
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return float(val)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    if pd.isna(val) if not isinstance(val, (list, dict)) else False:
        return None
    return val


def build_param_list(df):
    """Convert enrichment DataFrame to a list of dicts safe for Cypher UNWIND."""
    records = []
    for _, row in df.iterrows():
        records.append({
            'tcpuid': row['tcpuid'],
            'min_dist_to_surrender_m': clean_for_neo4j(row['min_dist_m']),
            'nearest_surrender_reserve': clean_for_neo4j(row['nearest_surrender_reserve']),
            'nearest_surrender_year': clean_for_neo4j(
                int(row['nearest_surrender_year']) if pd.notna(row['nearest_surrender_year']) else None
            ),
            'n_surrenders_5km': clean_for_neo4j(row['n_surrenders_5km']),
            'n_surrenders_25km': clean_for_neo4j(row['n_surrenders_25km']),
            'overlap_with_surrender': bool(row['overlap_flag']),
            'temporal_type': str(row['temporal_type']),
            'metis_community_present': bool(row['metis_community_present']),
            'nearest_metis_community': clean_for_neo4j(row['nearest_metis_community']),
            'nearest_metis_dist_m': clean_for_neo4j(row['nearest_metis_dist_m']),
        })
    return records


CYPHER_WRITE = """
UNWIND $rows AS row
MATCH (s:Settlement {census_id: row.tcpuid})
SET
  s.min_dist_to_surrender_m   = row.min_dist_to_surrender_m,
  s.nearest_surrender_reserve = row.nearest_surrender_reserve,
  s.nearest_surrender_year    = row.nearest_surrender_year,
  s.n_surrenders_5km          = row.n_surrenders_5km,
  s.n_surrenders_25km         = row.n_surrenders_25km,
  s.overlap_with_surrender    = row.overlap_with_surrender,
  s.temporal_type             = row.temporal_type,
  s.metis_community_present   = row.metis_community_present,
  s.nearest_metis_community   = row.nearest_metis_community,
  s.nearest_metis_dist_m      = row.nearest_metis_dist_m
RETURN count(s) AS updated
"""


def write_to_neo4j(param_list):
    """Batch-write enrichment properties to Settlement nodes."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=('neo4j', NEO4J_PASSWORD))
    # Split into batches of 100 to avoid oversized transactions
    batch_size = 100
    total_updated = 0
    with driver.session() as session:
        for i in range(0, len(param_list), batch_size):
            batch = param_list[i:i + batch_size]
            result = session.run(CYPHER_WRITE, rows=batch)
            n = result.single()['updated']
            total_updated += n
    driver.close()
    return total_updated


# =============================================================================
# Verification query
# =============================================================================

CYPHER_VERIFY = """
MATCH (s:Settlement)
WHERE s.min_dist_to_surrender_m IS NOT NULL
RETURN
  s.census_id               AS census_id,
  s.census_name             AS name,
  s.min_dist_to_surrender_m AS min_dist_m,
  s.nearest_surrender_reserve AS nearest_reserve,
  s.nearest_surrender_year  AS surrender_year,
  s.n_surrenders_5km        AS n_5km,
  s.n_surrenders_25km       AS n_25km,
  s.overlap_with_surrender  AS overlap,
  s.temporal_type           AS temporal_type,
  s.metis_community_present AS metis_present,
  s.nearest_metis_community AS nearest_metis,
  s.nearest_metis_dist_m    AS metis_dist_m
ORDER BY s.min_dist_to_surrender_m ASC
"""


def run_verification():
    """Query Neo4j to confirm enrichment was written correctly."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=('neo4j', NEO4J_PASSWORD))
    with driver.session() as session:
        records = [dict(r) for r in session.run(CYPHER_VERIFY)]
    driver.close()
    df = pd.DataFrame(records)
    print(f"\n  Verification: {len(df)} Settlement nodes have min_dist_to_surrender_m set")
    return df


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 60)
    print("Phase 5 — Neo4j Enrichment")
    print("=" * 60)

    # --- Load ---
    print("\n[1] Loading Phase 1–3 outputs...")
    p1 = load_phase1()
    p2 = load_phase2()
    p3 = load_phase3()

    # --- Merge ---
    print("\n[2] Building enrichment table...")
    enrichment = build_enrichment_df(p1, p2, p3)

    # --- Write ---
    print("\n[3] Writing to Neo4j...")
    param_list = build_param_list(enrichment)
    n_updated = write_to_neo4j(param_list)
    print(f"  Nodes updated: {n_updated}")

    if n_updated < len(enrichment):
        n_missing = len(enrichment) - n_updated
        print(f"  WARNING: {n_missing} TCPUIDs in enrichment table had no matching Settlement node.")
        print("  These may be municipalities present in the spatial data but absent from Neo4j.")

    # --- Verify ---
    print("\n[4] Verifying write...")
    verify_df = run_verification()

    # Spot-check: Kamsack should have overlap_with_surrender = True
    kamsack = verify_df[verify_df['name'].str.contains('Kamsack', case=False, na=False)]
    if not kamsack.empty:
        row = kamsack.iloc[0]
        print(f"\n  Spot check — Kamsack:")
        print(f"    overlap_with_surrender : {row['overlap']}")
        print(f"    nearest_reserve        : {row['nearest_reserve']}")
        print(f"    surrender_year         : {row['surrender_year']}")
        print(f"    temporal_type          : {row['temporal_type']}")
        print(f"    metis_present          : {row['metis_present']}")
    else:
        print("\n  WARNING: Kamsack not found in verification results.")

    # --- Save log ---
    print("\n[5] Saving enrichment log...")
    log_path = os.path.join(OUT_DIR, '05_enrichment_log.xlsx')

    # Merge enrichment with verify for the log
    log = enrichment.rename(columns={
        'overlap_flag': 'overlap_with_surrender',
        'min_dist_m': 'min_dist_to_surrender_m',
    })

    with pd.ExcelWriter(log_path, engine='openpyxl') as writer:
        log.to_excel(writer, sheet_name='Enrichment_Values', index=False)
        verify_df.to_excel(writer, sheet_name='Neo4j_Verification', index=False)

        # Summary sheet
        summary = pd.DataFrame({
            'Metric': [
                'Total municipalities',
                'Nodes updated in Neo4j',
                'With overlap_with_surrender',
                'Temporal type A',
                'Temporal type B',
                'Temporal type C',
                'Temporal type Indeterminate',
                'Temporal type none',
                'With metis_community_present',
                'Municipalities with n_surrenders_5km > 0',
                'Municipalities with n_surrenders_25km > 0',
            ],
            'Count': [
                len(enrichment),
                n_updated,
                int(enrichment['overlap_flag'].sum()),
                int((enrichment['temporal_type'] == 'A').sum()),
                int((enrichment['temporal_type'] == 'B').sum()),
                int((enrichment['temporal_type'] == 'C').sum()),
                int((enrichment['temporal_type'] == 'Indeterminate').sum()),
                int((enrichment['temporal_type'] == 'none').sum()),
                int(enrichment['metis_community_present'].sum()),
                int((enrichment['n_surrenders_5km'].fillna(0) > 0).sum()),
                int((enrichment['n_surrenders_25km'].fillna(0) > 0).sum()),
            ]
        })
        summary.to_excel(writer, sheet_name='Summary', index=False)

        # Methodology sheet
        methodology = pd.DataFrame({'Notes': [
            'Phase 5: Neo4j Enrichment — writes spatial analysis findings to Settlement nodes.',
            '',
            'Source data:',
            '  Phase 1 (01_proximity_results.xlsx, Ranked_All): proximity metrics per municipality.',
            '  Phase 2 (02_temporal_results.xlsx, Timeline_Table): temporal type per muni×reserve pair.',
            '  Phase 3 (03_metis_results.xlsx, All_Located_Proximity + Displacement_Cases).',
            '',
            'temporal_type reduction:',
            '  Each municipality may appear in multiple muni×reserve pairs in Phase 2,',
            '  each with its own temporal type. The most pre-emptive type is used:',
            '  A > B > C > Indeterminate > none.',
            '  "none" = municipality has no surrender parcels within 25 km.',
            '',
            'metis_community_present derivation:',
            '  True if any Métis community in All_Located_Proximity has this municipality',
            '  as its nearest municipality (by nearest_muni_tcpuid), OR if this municipality',
            '  appears in Displacement_Cases (name-matched Métis community).',
            '  nearest_metis_community and nearest_metis_dist_m are from the closest',
            '  community among those grouped to this municipality.',
            '',
            'Limitations:',
            '  - 71 of 113 Métis communities are unlocated; metis_community_present = False',
            '    does not mean no Métis presence, only no georeferenced presence.',
            '  - Métis community association is based on "nearest municipality" grouping,',
            '    not a full distance matrix from each municipality. Phase 3 displacement',
            '    cases use name matching and are the more reliable proximity indicators.',
            '  - overlap_with_surrender uses 1921 municipal polygon geometry. Overlap means',
            '    surrendered land was later incorporated into the municipality, not necessarily',
            '    that the municipality existed at surrender time.',
        ]})
        methodology.to_excel(writer, sheet_name='Methodology', index=False)

    print(f"  Log saved: {log_path}")
    print("\nPhase 5 complete.")


if __name__ == '__main__':
    main()
