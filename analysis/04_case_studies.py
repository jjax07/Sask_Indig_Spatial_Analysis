#!/usr/bin/env python3
"""
Phase 4: Case Study Builder
Produces structured profiles for 7 priority municipalities drawing on all
Phase 1–3 outputs plus Neo4j event data.

Outputs:
  analysis/case_studies/[name].md  — one markdown profile per case
  analysis/04_case_study_data.xlsx — one sheet per case
"""

import json
import os
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from neo4j import GraphDatabase

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'analysis', 'data')
OUT_DIR = os.path.join(BASE_DIR, 'analysis')
CASE_DIR = os.path.join(OUT_DIR, 'case_studies')
METIS_DIR = os.path.join(BASE_DIR, 'SK_Metis_Communities')
KG_WORKBOOK = os.path.join(BASE_DIR, '..', 'KnowledgeGraph',
                           'JJack_Urban_Sask_Knowledge_Graph_Feb_2026.xlsx')

NEO4J_URI = 'bolt://localhost:7687'
NEO4J_PASSWORD = '11069173'

CASE_RADIUS_M = 50_000  # 50 km for case study profiles

PRIORITY_CASES = [
    {'name': 'Kamsack',          'tcpuid': 'SK179019', 'slug': 'kamsack'},
    {'name': 'Broadview',        'tcpuid': 'SK175021', 'slug': 'broadview'},
    {'name': 'North Battleford', 'tcpuid': 'SK186026', 'slug': 'north_battleford'},
    {'name': 'Prince Albert',    'tcpuid': 'SK185026', 'slug': 'prince_albert'},
    {'name': 'Regina',           'tcpuid': 'SK176022', 'slug': 'regina'},
    {'name': 'Duck Lake',        'tcpuid': 'SK185027', 'slug': 'duck_lake'},
    {'name': 'Fort Qu\'Appelle', 'tcpuid': 'SK176048', 'slug': 'fort_quappelle'},
]

TPOP_COLS = ['TPOP_1881', 'TPOP_1885', 'TPOP_1889', 'TPOP_1893', 'TPOP_1897',
             'TPOP_1901', 'TPOP_1905', 'TPOP_1909', 'TPOP_1911', 'TPOP_1921', 'TPOP_1931']


# =============================================================================
# Data loaders
# =============================================================================

def load_all_data():
    urban = gpd.read_file(os.path.join(DATA_DIR, 'urban_429.gpkg'))
    surrenders = gpd.read_file(os.path.join(DATA_DIR, 'surrenders_clean.gpkg'))
    metis = gpd.read_file(os.path.join(DATA_DIR, 'metis_located.gpkg'))

    # Road allowance communities
    ra = gpd.read_file(os.path.join(METIS_DIR, 'Metis_RoadAllowance.geojson'))
    ra['geometry'] = ra['geometry'].apply(
        lambda g: shapely.force_2d(g) if g is not None else g)
    ra = ra.to_crs('EPSG:3347')

    metis_full = pd.read_csv(os.path.join(DATA_DIR, 'metis_full.csv'))

    p1 = pd.read_excel(os.path.join(OUT_DIR, '01_proximity_results.xlsx'),
                       sheet_name='Ranked_All')
    p2 = pd.read_excel(os.path.join(OUT_DIR, '02_temporal_results.xlsx'),
                       sheet_name='Timeline_Table')
    p3_disp = pd.read_excel(os.path.join(OUT_DIR, '03_metis_results.xlsx'),
                            sheet_name='Displacement_Cases')

    kg = pd.read_excel(KG_WORKBOOK, sheet_name='Sheet1')
    kg = kg.rename(columns={'V1T27_1921': 'TCPUID'})

    return urban, surrenders, metis, ra, metis_full, p1, p2, p3_disp, kg


def get_neo4j_case_data(tcpuid):
    """Fetch events and railway lines for a single settlement from Neo4j."""
    driver = GraphDatabase.driver(NEO4J_URI, auth=('neo4j', NEO4J_PASSWORD))
    query = """
        MATCH (s:Settlement {census_id: $tcpuid})
        OPTIONAL MATCH (s)-[:HAD_EVENT]->(e:Event)
        OPTIONAL MATCH (s)-[:SERVED_BY]->(r:RailwayLine)
        RETURN
            s.census_name     AS name,
            s.founded         AS founded,
            s.incorporated    AS incorporated,
            s.population_1921 AS pop,
            collect(distinct {type: e.type, year: e.year, context: e.context}) AS events,
            collect(distinct {builder: r.builder_name, year: r.year_constructed}) AS railways
    """
    with driver.session() as session:
        result = list(session.run(query, tcpuid=tcpuid))
    driver.close()
    if not result:
        return {}
    rec = result[0]
    return {
        'name': rec['name'],
        'founded': rec['founded'],
        'incorporated': rec['incorporated'],
        'pop': rec['pop'],
        'events': [e for e in rec['events'] if any(v is not None for v in e.values())],
        'railways': [r for r in rec['railways'] if any(v is not None for v in r.values())],
    }


# =============================================================================
# Per-case spatial queries
# =============================================================================

def get_nearby_surrenders(muni_geom, surrenders_gdf, radius_m):
    dists = shapely.distance(surrenders_gdf.geometry.values, muni_geom)
    mask = dists <= radius_m
    result = surrenders_gdf[mask].copy()
    result['dist_m'] = dists[mask]
    return result.sort_values('dist_m')


def get_nearby_metis(muni_geom, metis_gdf, ra_gdf, metis_full_df, radius_m):
    """Return located community and road allowance points within radius."""
    dists_c = shapely.distance(metis_gdf.geometry.values, muni_geom)
    comm = metis_gdf[dists_c <= radius_m].copy()
    comm['dist_m'] = dists_c[dists_c <= radius_m]
    comm['layer'] = 'Community'

    dists_r = shapely.distance(ra_gdf.geometry.values, muni_geom)
    ra_near = ra_gdf[dists_r <= radius_m].copy()
    ra_near['dist_m'] = dists_r[dists_r <= radius_m]
    ra_near['layer'] = 'Road Allowance'
    ra_near = ra_near.rename(columns={'NAME': 'community_name'})

    # Join temporal data for communities
    comm = comm.merge(
        metis_full_df[['UNIQUE_ID', 'Y_FOUND', 'Y_DEPART', 'TYPE',
                        'POP_1860', 'POP_1880', 'POP_1900', 'POP_1921_CSD']],
        on='UNIQUE_ID', how='left', suffixes=('', '_full')
    )
    ra_near = ra_near.merge(
        metis_full_df[['UNIQUE_ID', 'Y_FOUND', 'Y_DEPART',
                        'POP_1860', 'POP_1880', 'POP_1900', 'POP_1921_CSD']],
        on='UNIQUE_ID', how='left'
    )

    return comm, ra_near


def get_temporal_data(tcpuid, p2_df):
    return p2_df[p2_df['TCPUID'] == tcpuid].copy()


# =============================================================================
# Markdown generation
# =============================================================================

def fmt_year(val):
    try:
        v = int(float(val))
        return str(v)
    except (TypeError, ValueError):
        return '—'


def fmt_num(val):
    try:
        return f'{int(float(val)):,}'
    except (TypeError, ValueError):
        return '—'


def temporal_narrative(muni_row, temporal_df, neo_data):
    """Generate a plain-language temporal sequence summary."""
    lines = []
    founded = fmt_year(muni_row.get('effective_founded'))
    incorporated = fmt_year(muni_row.get('incorporated_num'))
    railway_yr = fmt_year(neo_data.get('railways')[0].get('year') if neo_data.get('railways') else None)
    railway_co = neo_data.get('railways')[0].get('builder') if neo_data.get('railways') else None

    lines.append(f'**Municipal founding:** {founded}  ')
    lines.append(f'**Formal incorporation:** {incorporated}  ')
    if railway_yr != '—':
        co_str = f' ({railway_co})' if railway_co else ''
        lines.append(f'**Railway arrival:** {railway_yr}{co_str}  ')
    lines.append('')

    if temporal_df.empty:
        lines.append('_No surrender parcels within 25 km — temporal classification not applicable._')
        return '\n'.join(lines)

    types = temporal_df['temporal_type'].value_counts()
    dominant = types.index[0]

    type_labels = {
        'A': 'Type A — Pre-emptive settlement',
        'B': 'Type B — Concurrent',
        'C': 'Type C — Post-surrender settlement',
        'Indeterminate': 'Indeterminate',
    }
    lines.append(f'**Classification:** {type_labels.get(dominant, dominant)} '
                 f'({types[dominant]} of {len(temporal_df)} reserve pairs)')
    lines.append('')

    if dominant == 'A':
        min_gap = temporal_df['years_to_first_surrender'].min()
        max_gap = temporal_df['years_to_first_surrender'].max()
        if min_gap == max_gap:
            lines.append(f'The municipality was founded {int(abs(min_gap))} year(s) before '
                         f'the first recorded surrender on the nearest reserve.')
        else:
            lines.append(f'Across associated reserves, the municipality predated first surrender '
                         f'by {int(abs(min_gap))}–{int(abs(max_gap))} years.')
        lines.append('This places it within the "pressure then surrender" sequence: settler '
                     'presence preceded and likely contributed to the formal surrender of '
                     'reserve land.')
    elif dominant == 'B':
        lines.append('The municipality was founded within five years of the major surrender '
                     'event on nearby reserves — consistent with concurrent settlement and '
                     'dispossession.')
    elif dominant == 'C':
        lines.append('The municipality was founded after the associated reserve surrenders '
                     'were recorded — consistent with the conventional "opened land was then '
                     'settled" narrative, though pre-surrender informal encroachment cannot '
                     'be excluded.')

    lines.append('')
    lines.append('| Reserve | First surrender | Muni founded | Gap (yrs) | Type | Dist (m) |')
    lines.append('|---|---|---|---|---|---|')
    shown = set()
    for _, row in temporal_df.sort_values('years_to_first_surrender').iterrows():
        key = (row['UNIQUE_ID_base'], row['TCPUID'])
        if key in shown:
            continue
        shown.add(key)
        gap = fmt_year(row.get('years_to_first_surrender'))
        lines.append(
            f"| {row.get('reserve_name', '—')} "
            f"| {fmt_year(row.get('first_surrender_year'))} "
            f"| {fmt_year(row.get('muni_effective_founded'))} "
            f"| {gap} "
            f"| {row.get('temporal_type', '—')} "
            f"| {fmt_num(row.get('dist_m'))} |"
        )

    return '\n'.join(lines)


def pop_trajectory_table(nearby_surr):
    """Build a population trajectory markdown table for nearby reserves."""
    present_cols = [c for c in TPOP_COLS if c in nearby_surr.columns
                    and nearby_surr[c].notna().any()]
    if not present_cols:
        return '_No population data available._'

    years = [c.replace('TPOP_', '') for c in present_cols]
    header = '| Reserve | Dist (m) | ' + ' | '.join(years) + ' |'
    sep = '|---|---|' + '|'.join(['---'] * len(years)) + '|'
    lines = [header, sep]
    for _, row in nearby_surr.iterrows():
        pops = [fmt_num(row.get(c)) for c in present_cols]
        lines.append(
            f"| {row.get('RSRVE_NAME', '—')} "
            f"| {fmt_num(row.get('dist_m'))} "
            f"| {'|'.join(pops)} |"
        )
    lines.append('')
    lines.append('_Note: Population figures are for the whole reserve, not the surrendered '
                 'portion. Decline following surrender cannot be attributed solely to surrender '
                 'without controlling for other variables._')
    return '\n'.join(lines)


def surrender_notes_section(nearby_surr):
    """Verbatim Notes and NOTES_1 fields for nearby surrender parcels."""
    lines = []
    for _, row in nearby_surr.iterrows():
        notes = str(row.get('Notes') or '').strip()
        notes1 = str(row.get('NOTES_1') or '').strip()
        if not notes and not notes1:
            continue
        lines.append(f"**{row.get('RSRVE_NAME', row.get('UNIQUE_ID', '?'))}** "
                     f"(UNIQUE_ID: {row.get('UNIQUE_ID', '—')}, "
                     f"surrendered: {fmt_year(row.get('year_surr_clean'))}, "
                     f"dist: {fmt_num(row.get('dist_m'))} m)")
        if notes:
            lines.append(f'> {notes}')
        if notes1 and notes1.lower() not in ('nan', notes.lower()):
            lines.append(f'> {notes1}')
        lines.append('')
    return '\n'.join(lines) if lines else '_No verbatim notes recorded for nearby parcels._'


def metis_section(comm_df, ra_df, p3_disp, tcpuid, muni_name=''):
    """Métis community presence table and displacement signal."""
    lines = []

    if comm_df.empty and ra_df.empty:
        return '_No georeferenced Métis communities within 50 km._'

    # Check if this municipality appears in displacement cases
    # Match on name_match_muni or containing_muni_name (tcpuid not saved in Excel sheet)
    muni_name_str = muni_name if isinstance(muni_name, str) else ''
    disp = p3_disp[
        p3_disp['name_match_muni'].fillna('').str.contains(muni_name_str, case=False) |
        p3_disp['containing_muni_name'].fillna('').str.contains(muni_name_str, case=False)
    ]

    if not comm_df.empty:
        lines.append('**Located communities (within 50 km):**')
        lines.append('')
        lines.append('| Community | Type | Founded | Departed | Dist (m) | Pop 1860 | Pop 1900 | Pop 1921 |')
        lines.append('|---|---|---|---|---|---|---|---|')
        for _, row in comm_df.sort_values('dist_m').iterrows():
            lines.append(
                f"| {row.get('community_name', '—')} "
                f"| {row.get('TYPE', 'Community')} "
                f"| {fmt_year(row.get('Y_FOUND'))} "
                f"| {fmt_year(row.get('Y_DEPART'))} "
                f"| {fmt_num(row.get('dist_m'))} "
                f"| {fmt_num(row.get('POP_1860'))} "
                f"| {fmt_num(row.get('POP_1900'))} "
                f"| {fmt_num(row.get('POP_1921_CSD'))} |"
            )
        lines.append('')

    if not ra_df.empty:
        lines.append('**Road allowance communities (within 50 km):**')
        lines.append('')
        lines.append('| Community | Founded | Departed | Dist (m) |')
        lines.append('|---|---|---|---|')
        for _, row in ra_df.sort_values('dist_m').iterrows():
            depart = fmt_year(row.get('Y_DEPART'))
            depart_str = depart if depart != '—' else '— _(undocumented removal)_'
            lines.append(
                f"| {row.get('community_name', '—')} "
                f"| {fmt_year(row.get('Y_FOUND'))} "
                f"| {depart_str} "
                f"| {fmt_num(row.get('dist_m'))} |"
            )
        lines.append('')
        lines.append('_Road allowance community proximity to this municipality was intentional: '
                     'residents maintained kinship ties and accessed day labour markets here. '
                     'Departure dates reflect forced removal (communities were often burned by '
                     'CCF provincial government, 1940s–1960s); undocumented removals are '
                     'recorded as blank._')
        lines.append('')

    if not disp.empty:
        lines.append('**Displacement signal:**')
        for _, row in disp.iterrows():
            preceded = row.get('metis_preceded_muni')
            depart_after = row.get('depart_after_muni_founded')
            name = row.get('community_name', '—')
            muni_yr = fmt_year(row.get('muni_effective_founded'))
            found_yr = fmt_year(row.get('Y_FOUND_clean'))
            depart_yr = fmt_year(row.get('Y_DEPART_clean'))
            if preceded:
                lines.append(
                    f'The {name} Métis community (founded {found_yr}) predated this '
                    f'municipality (founded {muni_yr}) by '
                    f'{int(float(muni_yr) - float(found_yr))} years.'
                )
            if depart_after:
                lines.append(
                    f'Community departure recorded {depart_yr} — after municipal founding, '
                    f'consistent with displacement following settler establishment.'
                )

    return '\n'.join(lines)


def gaps_section(muni_name, nearby_surr, comm_df, ra_df, temporal_df, neo_data):
    """Generate targeted follow-up questions based on data present."""
    lines = ['Suggested archival and corpus queries for qualitative follow-up:', '']

    # Surrender notes that name the municipality
    explicit = nearby_surr[
        nearby_surr['Notes'].fillna('').str.contains(muni_name, case=False) |
        nearby_surr['NOTES_1'].fillna('').str.contains(muni_name, case=False)
    ]
    if not explicit.empty:
        reserves = ', '.join(explicit['RSRVE_NAME'].tolist())
        lines.append(f'- Surrender notes explicitly mention {muni_name} for: **{reserves}**. '
                     f'Confirm in Indian Affairs records whether these surrenders were '
                     f'formally linked to municipal settlement pressure.')

    # Type A — look for pre-surrender encroachment
    type_a = temporal_df[temporal_df['temporal_type'] == 'A']
    if not type_a.empty:
        for _, row in type_a.iterrows():
            r = row.get('reserve_name', '')
            yr = fmt_year(row.get('first_surrender_year'))
            gap = row.get('years_to_first_surrender')
            if pd.notna(gap) and gap > 0:
                lines.append(
                    f'- {muni_name} predated the {r} surrender ({yr}) by {int(gap)} years. '
                    f'Search local newspapers and histories for evidence of settlers '
                    f'farming or occupying {r} reserve land before {yr}.'
                )

    # Railway timing
    if neo_data.get('railways'):
        for rail in neo_data['railways']:
            ry = rail.get('year')
            rb = rail.get('builder', '')
            if ry:
                lines.append(
                    f'- Railway arrived {ry} ({rb}). Examine how railway promotion '
                    f'intersected with reserve surrender in local booster literature '
                    f'and land company records.'
                )

    # Founding event context
    found_events = [e for e in neo_data.get('events', []) if e.get('type') == 'founding']
    if found_events and found_events[0].get('context'):
        lines.append(f'- Founding context in KG: "{found_events[0]["context"]}". '
                     f'Verify against local histories and newspaper accounts in graphrag corpus.')

    # Residential school
    school_events = [e for e in neo_data.get('events', []) if e.get('type') == 'first_school']
    resid = [e for e in neo_data.get('events', []) if 'residential' in str(e.get('context', '')).lower()
             or 'residential' in str(e.get('type', '')).lower()]
    if school_events and school_events[0].get('context') and 'residential' in school_events[0]['context'].lower():
        lines.append(f'- Residential school noted in founding events. Examine relationship '
                     f'between school location, reserve proximity, and land alienation.')

    # Métis community
    if not comm_df.empty or not ra_df.empty:
        names = list(comm_df.get('community_name', pd.Series()).dropna()) + \
                list(ra_df.get('community_name', pd.Series()).dropna())
        lines.append(
            f'- Métis communities documented near {muni_name}: '
            f'{", ".join(str(n) for n in names[:5])}. '
            f'Query Métis_Communities_Research.docx and graphrag corpus for '
            f'settler accounts of Métis presence and displacement.'
        )

    # Colonization company
    col_events = [e for e in neo_data.get('events', [])
                  if e.get('type') == 'colonization_company' and e.get('context')]
    if col_events:
        lines.append(f'- Colonization company active: "{col_events[0]["context"]}". '
                     f'Examine company land holdings relative to nearby reserve boundaries.')

    lines.append('- Search graphrag corpus for settler-perspective accounts of land use '
                 f'and encroachment in the {muni_name} area in the decade before each '
                 f'recorded surrender.')

    return '\n'.join(lines)


# =============================================================================
# Markdown assembly
# =============================================================================

def build_markdown(case, muni_row, neo_data, nearby_surr, comm_df, ra_df,
                   temporal_df, p3_disp, kg_row):
    name = case['name']
    tcpuid = case['tcpuid']

    # KG fields
    kg = kg_row.iloc[0] if not kg_row.empty else pd.Series()

    sections = []

    # Header
    sections.append(f'# Case Study: {name}')
    sections.append(f'_Generated 2026-04-02 from Phase 1–3 spatial analysis outputs._')
    sections.append('')

    # Settlement overview
    sections.append('## Settlement Overview')
    sections.append('')
    sections.append('| Field | Value |')
    sections.append('|---|---|')
    sections.append(f'| TCPUID | {tcpuid} |')
    sections.append(f'| Type | {muni_row.get("CSD_TYPE", "—")} |')
    sections.append(f'| Population (1921) | {fmt_num(muni_row.get("POP_TOT_1921"))} |')
    sections.append(f'| Founded | {fmt_year(muni_row.get("effective_founded"))} |')
    sections.append(f'| Incorporated | {fmt_year(muni_row.get("incorporated_num"))} |')
    sections.append(f'| Commercial type | {muni_row.get("commercial_type", "—")} |')
    if neo_data.get('railways'):
        for r in neo_data['railways']:
            sections.append(
                f'| Railway arrival | {fmt_year(r.get("year"))} ({r.get("builder", "—")}) |'
            )
    sections.append('')

    # Key events from Neo4j
    if neo_data.get('events'):
        sections.append('**Key events (from Knowledge Graph):**')
        sections.append('')
        events_sorted = sorted(
            [e for e in neo_data['events'] if e.get('year') is not None],
            key=lambda e: e.get('year', 9999)
        )
        for e in events_sorted:
            ctx = e.get('context', '').strip() if e.get('context') else ''
            label = e.get('type', '').replace('_', ' ').title()
            if ctx:
                sections.append(f'- **{fmt_year(e["year"])}** ({label}): {ctx}')
            else:
                sections.append(f'- **{fmt_year(e["year"])}** ({label})')
        sections.append('')

    # Surrendered reserve land
    sections.append(f'## Surrendered Reserve Land Within 50 km')
    sections.append('')
    if nearby_surr.empty:
        sections.append('_No surrendered parcels within 50 km._')
    else:
        sections.append(
            f'| Reserve | UNIQUE_ID | Surrendered | Acres | '
            f'Orig acres | Dist (m) | Treaty |'
        )
        sections.append('|---|---|---|---|---|---|---|')
        for _, row in nearby_surr.iterrows():
            sections.append(
                f"| {row.get('RSRVE_NAME', '—')} "
                f"| {row.get('UNIQUE_ID', '—')} "
                f"| {fmt_year(row.get('year_surr_clean'))} "
                f"| {fmt_num(row.get('ACRES_SURR'))} "
                f"| {fmt_num(row.get('ORIG_ACRE'))} "
                f"| {fmt_num(row.get('dist_m'))} "
                f"| {row.get('TREATY_No_', '—')} |"
            )
    sections.append('')

    # Temporal sequence
    sections.append('## Temporal Sequence')
    sections.append('')
    sections.append(temporal_narrative(muni_row, temporal_df, neo_data))
    sections.append('')

    # Population trajectory
    sections.append('## Reserve Population Trajectory')
    sections.append('')
    sections.append(pop_trajectory_table(nearby_surr))
    sections.append('')

    # Métis presence
    sections.append('## Métis Community Presence')
    sections.append('')
    sections.append(metis_section(comm_df, ra_df, p3_disp, tcpuid, muni_name=name))
    sections.append('')

    # Verbatim surrender notes
    sections.append('## Verbatim Surrender Notes')
    sections.append('')
    sections.append(surrender_notes_section(nearby_surr))

    # Gaps and questions
    sections.append('## Gaps and Questions for Follow-up')
    sections.append('')
    sections.append(gaps_section(name, nearby_surr, comm_df, ra_df, temporal_df, neo_data))
    sections.append('')

    return '\n'.join(sections)


# =============================================================================
# Main
# =============================================================================

def main():
    print('=' * 55)
    print('Phase 4: Case Study Builder')
    print('=' * 55)

    os.makedirs(CASE_DIR, exist_ok=True)

    print('\n[1/3] Loading data')
    urban, surrenders, metis, ra, metis_full, p1, p2, p3_disp, kg = load_all_data()

    # Build lookup for Phase 1 municipality rows (need effective_founded etc.)
    p1_lookup = p1.set_index('TCPUID_CSD_1921')

    print('\n[2/3] Building case studies')
    excel_sheets = {}

    for case in PRIORITY_CASES:
        tcpuid = case['tcpuid']
        name = case['name']
        print(f'  {name} ({tcpuid})')

        # Municipality geometry
        muni_row_geo = urban[urban['TCPUID_CSD_1921'] == tcpuid]
        if muni_row_geo.empty:
            print(f'    WARNING: {tcpuid} not found in urban_429.gpkg — skipping')
            continue
        muni_geom = muni_row_geo.geometry.iloc[0]

        # Phase 1 proximity row
        muni_p1 = p1_lookup.loc[tcpuid] if tcpuid in p1_lookup.index else pd.Series()

        # Neo4j
        neo_data = get_neo4j_case_data(tcpuid)

        # Spatial queries
        nearby_surr = get_nearby_surrenders(muni_geom, surrenders, CASE_RADIUS_M)
        comm_df, ra_df = get_nearby_metis(muni_geom, metis, ra, metis_full, CASE_RADIUS_M)

        # Phase 2 temporal data
        temporal_df = get_temporal_data(tcpuid, p2)

        # KG row
        kg_row = kg[kg['TCPUID'] == tcpuid]

        # Build markdown
        md = build_markdown(case, muni_p1, neo_data, nearby_surr,
                            comm_df, ra_df, temporal_df, p3_disp, kg_row)

        md_path = os.path.join(CASE_DIR, f'{case["slug"]}.md')
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f'    -> {md_path}')

        # Excel sheet data
        surr_sheet = nearby_surr[[
            c for c in ['UNIQUE_ID', 'RSRVE_NAME', 'year_surr_clean', 'ACRES_SURR',
                        'ORIG_ACRE', 'TREATY_No_', 'dist_m', 'Notes', 'NOTES_1',
                        'Data_Certa'] + TPOP_COLS
            if c in nearby_surr.columns
        ]].copy()
        surr_sheet.insert(0, 'muni_name', name)
        surr_sheet.insert(1, 'muni_tcpuid', tcpuid)
        excel_sheets[name] = surr_sheet

    print('\n[3/3] Writing Excel workbook')
    out_xlsx = os.path.join(OUT_DIR, '04_case_study_data.xlsx')
    with pd.ExcelWriter(out_xlsx, engine='openpyxl') as writer:
        for sheet_name, df in excel_sheets.items():
            safe_name = sheet_name[:31]
            df.to_excel(writer, sheet_name=safe_name, index=False)
    print(f'  {out_xlsx} ({len(excel_sheets)} sheets)')

    print('\n' + '=' * 55)
    print('Phase 4 complete.')
    print('=' * 55)


if __name__ == '__main__':
    main()
