#!/usr/bin/env python3
"""
Phase 5b: Métis founding year enrichment (supplemental)

Writes `nearest_metis_y_found` to Settlement nodes that already have
`nearest_metis_community` set (from Phase 5 main enrichment).

Deduplication rule: where multiple records in metis_full.csv share a NAME,
take the minimum non-null Y_FOUND. This captures the earliest documented
presence for that community location, regardless of record type (Community,
Road Allowance, Métis Farm, Wintering Site, Post).

Source:  analysis/data/metis_full.csv
Depends: nearest_metis_community already set on Settlement nodes (Phase 5)
Writes:  nearest_metis_y_found (int) on Settlement nodes
"""

import os
import pandas as pd
from neo4j import GraphDatabase

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'analysis', 'data')

NEO4J_URI = 'bolt://localhost:7687'
NEO4J_PASSWORD = '11069173'


def build_year_lookup(csv_path):
    """Build name → minimum non-null Y_FOUND from metis_full.csv."""
    df = pd.read_csv(csv_path)
    df['NAME'] = df['NAME'].str.strip()
    df['Y_FOUND'] = pd.to_numeric(df['Y_FOUND'], errors='coerce')

    # For each name, take the minimum non-null Y_FOUND across all record types
    lookup = (
        df.dropna(subset=['Y_FOUND'])
        .groupby('NAME')['Y_FOUND']
        .min()
        .astype(int)
        .to_dict()
    )

    # Report any names with multiple records and which value was selected
    dupes = df[df['NAME'].duplicated(keep=False)].sort_values('NAME')
    if not dupes.empty:
        print("  Duplicate NAME entries — value selected (minimum non-null Y_FOUND):")
        for name, grp in dupes.groupby('NAME'):
            years = grp['Y_FOUND'].dropna().astype(int).tolist()
            selected = lookup.get(name, None)
            print(f"    {name}: {years} → {selected}")

    return lookup


def fetch_nearest_communities(driver):
    """Return all Settlement nodes that have nearest_metis_community set."""
    cypher = """
    MATCH (s:Settlement)
    WHERE s.nearest_metis_community IS NOT NULL
    RETURN s.census_id AS tcpuid, s.census_name AS name,
           s.nearest_metis_community AS community
    """
    with driver.session() as session:
        return [dict(r) for r in session.run(cypher)]


def write_year(driver, updates):
    """Write nearest_metis_y_found for a list of {tcpuid, year} dicts."""
    cypher = """
    UNWIND $rows AS row
    MATCH (s:Settlement {census_id: row.tcpuid})
    SET s.nearest_metis_y_found = row.year
    RETURN count(s) AS updated
    """
    with driver.session() as session:
        result = session.run(cypher, rows=updates)
        return result.single()['updated']


def main():
    print("=" * 60)
    print("Phase 5b — Métis founding year enrichment")
    print("=" * 60)

    csv_path = os.path.join(DATA_DIR, 'metis_full.csv')
    print(f"\n[1] Building year lookup from {csv_path}...")
    lookup = build_year_lookup(csv_path)
    print(f"  {len(lookup)} communities with non-null Y_FOUND")

    driver = GraphDatabase.driver(NEO4J_URI, auth=('neo4j', NEO4J_PASSWORD))

    print("\n[2] Fetching Settlement nodes with nearest_metis_community...")
    nodes = fetch_nearest_communities(driver)
    print(f"  {len(nodes)} nodes found")

    updates = []
    skipped = []
    for node in nodes:
        community = node['community']
        year = lookup.get(community)
        if year is not None:
            updates.append({'tcpuid': node['tcpuid'], 'year': year})
        else:
            skipped.append(node)

    print(f"\n[3] Writing nearest_metis_y_found to {len(updates)} nodes...")
    if updates:
        n = write_year(driver, updates)
        print(f"  Updated: {n}")

    if skipped:
        print(f"\n  Skipped (null Y_FOUND in source or name not matched): {len(skipped)}")
        for s in skipped:
            print(f"    {s['name']} — community: {s['community']}")

    driver.close()
    print("\nPhase 5b complete.")


if __name__ == '__main__':
    main()
