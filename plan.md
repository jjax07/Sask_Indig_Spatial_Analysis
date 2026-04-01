# plan.md — Saskatchewan Indigenous Spatial Analysis: Implementation Plan

## Implementation Log

### Phase 0 — completed 2026-04-01
Script: `analysis/00_prepare_data.py`. All outputs written to `analysis/data/`.

**Issues resolved during implementation:**
- `Sask_1921_Urban_Muni_Full.geojson` has duplicate column names after stripping both field prefixes (`L0Sask1921Full.*` and `UrbanSaskHist - Final.csv.*`). Fixed by keeping only the `L0Sask1921Full.*` spatial columns and dropping the CSV columns entirely before writing to GPKG.
- `NAME` is a reserved field name in OGR/GPKG format. The Métis community GeoJSON `Name` field was renamed to `community_name` on load.
- Neo4j query returns 818 records (not 429) due to multiple IS_TYPE relationships per Settlement. **Deduplicate on `census_id` at the start of Phase 1.**
- 194 of 818 Settlement records (after dedup: some fraction of 429) are missing a `founded` year. Phase 1 must fall back to `incorporated` year where `founded` is null, and flag residual nulls.
- All 54 surrender parcels have clean year data after sentinel handling — no nulls.
- All 42 surrender UNIQUE_IDs match the master table.

---

## Project Context and Interpretive Frame

This plan operationalizes the spatial and temporal analysis described in `Indigenous_Spatial_Analysis.md`. The driving argument — that urban municipalities grew on or adjacent to Indigenous spaces systematically reduced through surrender, coercion, and encroachment — requires that the analysis be structured to surface temporal sequencing, not just proximity. Statistical proximity without the chronological relationship between municipal founding and surrender year produces description, not argument. Every output must therefore carry both dimensions.

Theoretical debts to Raibmon (bottom-up settler pressure preceding formal surrender) and Waiser (mechanics of surrender 1896–1911) shape what counts as a positive finding: a municipality founded before a nearby surrender is not merely spatially close — it is a candidate for the "pressure then surrender" sequence the research is arguing for.

---

## Data Reality Check Before Starting

Several field-level issues discovered during scoping must be resolved before any spatial work begins:

**1. Field name prefix in the Urban Muni layer.** All property names in `Sask_1921_Urban_Muni_Full.geojson` carry the prefix `L0Sask1921Full.` (e.g., `L0Sask1921Full.TCPUID_CSD_1921`, `L0Sask1921Full.CSD_TYPE`). This is an ArcGIS export artefact. Every script must reference these prefixed names directly or strip the prefix on load.

**2. CSD_TYPE filtering.** The 429 urban municipalities are recoverable from CSD_TYPE values `C` (Cities), `T` (Towns), `VL` (Villages), and `T_PT`. Filtering by CSD_TYPE alone may not yield exactly 429; the preferred approach is a join against the 429 TCPUIDs confirmed in Neo4j. The TCPUID join is authoritative.

**3. YEAR_SURR sentinel value.** One record (`PRF116`) has `YEAR_SURR = -99` while `YR_SUR = 1927`. Use `YR_SUR` as primary surrender year and fall back to `YEAR_SURR` for null handling. All analyses must treat -99 as null.

**4. Métis xlsx vs geojson coverage gap.** 113 communities in `Métis_Communities.xlsx` but only 42 georeferenced in `Metis_Community.geojson`. 71 communities have no coordinates. Spatial analysis can only use the 42 georeferenced points. The 71 unlocated communities must be handled in a separate non-spatial table. Do not misrepresent the 42 as a complete picture.

**5. Reserves_Initial_Survey join key.** The initial survey polygons use `UniqueD_1902` (not `UNIQUE_ID`) as the reserve identifier field. The surrender layer uses `UNIQUE_ID`. This naming discrepancy must be handled explicitly in all joins.

**6. hasZ flag in Métis geojson.** `Metis_Community.geojson` has 3D coordinates (hasZ=true). GeoPandas handles this transparently but the Z coordinate must be dropped before distance calculations.

**7. Surrender UNIQUE_ID sub-parcel suffixes.** Some surrender parcels have sub-IDs like `PRQA86-3` — extract the base ID using regex `^([A-Z]+\d+[A-Z]?)` for joins to the master table.

**8. Neo4j commercial tier.** The `commercial_tier` values (RSC/LSC/SSC) are `SettlementType` nodes connected via `:IS_TYPE` relationships, not a direct Settlement property. Queries retrieving commercial tier must use `OPTIONAL MATCH (s)-[:IS_TYPE]->(ct:SettlementType)`.

---

## Technical Decisions

### Coordinate Reference System
All input layers are in WGS84 (EPSG:4326) and must be reprojected before any distance measurement.

**Decision: Use EPSG:3347 (NAD83 / Statistics Canada Lambert) for all projected operations.** This minimises area distortion across the full province. Outputs stored with geometry in EPSG:4326 for display compatibility.

### Distance Thresholds
Three nested buffers:
- **Overlap / contiguous (0 m):** surrender parcel geometry intersects or touches municipality polygon
- **Immediate proximity (5 km):** visually adjacent; within one small township length
- **Near-urban influence (25 km):** order of magnitude for pre-automobile daily movement and farming range

All outputs report the actual measured distance, not just which threshold band it falls into, so researchers can apply different cutoffs without re-running.

### Join Keys

| Join | Left key | Right key | Notes |
|------|----------|-----------|-------|
| Urban muni ↔ Neo4j | `L0Sask1921Full.TCPUID_CSD_1921` | `census_id` | Authoritative filter for 429 |
| Surrender ↔ Initial survey | `UNIQUE_ID` (base ID, strip sub-parcel suffix) | `UniqueD_1902` | Rename on load for consistency |
| Surrender ↔ Reserves master table | `UNIQUE_ID` | `UNIQUE_ID` | Direct match |
| Métis geojson ↔ xlsx | `UNIQUE_ID` | `UNIQUE_ID` | Direct match |

### Output Formats
- **Primary analysis outputs:** Excel workbooks (.xlsx) with multiple sheets — consistent with existing KnowledgeGraph analysis pattern
- **Case study profiles:** Markdown files (one per priority municipality) in `analysis/case_studies/`
- **Visualization-ready data:** GeoJSON files with analysis attributes attached, EPSG:4326
- **Neo4j enrichment:** Dispossession proximity data written back as Settlement node properties

---

## Phase Structure

### Phase 0 — Data Preparation (`analysis/00_prepare_data.py`)

Runs first. Produces clean, analysis-ready versions of all layers. No analysis happens here — only loading, validation, filtering, and joining. All subsequent scripts import from these outputs.

**Steps:**

1. Load `Sask_1921_Urban_Muni_Full.geojson`. Strip the `L0Sask1921Full.` prefix from all column names. Filter to 429 urban municipalities by joining against the Neo4j-sourced TCPUID list (retrieved via `MATCH (s:Settlement) RETURN s.census_id, s.name, s.founded, s.csd_type`). Reproject to EPSG:3347.

2. Load `SK_ReserveSurrenders_1933.geojson`. Drop Z coordinates if present. Create `year_surr_clean` preferring `YR_SUR` over `YEAR_SURR`, replacing -99 sentinels with None. Extract `UNIQUE_ID_BASE` (strip trailing sub-parcel suffix). Reproject to EPSG:3347.

3. Load `Reserves_Initial_Survey.geojson`. Rename `UniqueD_1902` to `UNIQUE_ID` for consistency. Reproject to EPSG:3347.

4. Load `Sask_Reserves_1931.xlsx`, Sheet1. Parse all `SURR_YYYY` columns; melt into a long-format table `(UNIQUE_ID, year, acres_surrendered)` with null/zero rows dropped. This is the backbone of Phase 2 temporal analysis.

5. Load `Metis_Community.geojson`. Drop Z coordinate. Reproject to EPSG:3347.

6. Load `Métis_Communities.xlsx`, Sheet1. Clean `Y_FOUND` and `Y_DEPART` — approximate dates; flag uncertainty. Join to geojson on `UNIQUE_ID`. The 71 unjoined records become a separate `metis_unlocated_df` saved as a supplementary table.

7. Load `Reserve_Boundary_Changes.geojson` and `Reserves_CD_1921.geojson` as reference layers.

8. Write outputs to `analysis/data/`:
   - `urban_429.gpkg` — filtered 429 municipalities, EPSG:3347
   - `surrenders_clean.gpkg` — surrender parcels with cleaned fields, EPSG:3347
   - `reserves_initial.gpkg` — initial survey polygons, EPSG:3347
   - `reserves_master.csv` — full xlsx master table
   - `surrenders_long.csv` — melted year-by-year surrender acreage
   - `metis_located.gpkg` — 42 located Métis community points, EPSG:3347
   - `metis_full.csv` — all 113 communities with temporal data
   - `neo4j_settlements.csv` — Neo4j Settlement properties for 429 municipalities

9. Print a validation report: feature counts, null counts for key fields, CRS confirmation, any UNIQUE_ID in surrenders that does not match the master table.

---

### Phase 1 — Spatial Proximity Analysis (`analysis/01_spatial_proximity.py`)

**Purpose:** For each of the 429 urban municipalities, determine which surrendered reserve parcels fall within defined distance bands, and compute the minimum distance to any surrendered land.

**Steps:**

1. Load `urban_429.gpkg` and `surrenders_clean.gpkg` from Phase 0.

2. Compute a distance matrix using geopandas `.distance()` between each urban municipality and each surrender parcel. Both layers are in EPSG:3347 so distances are in metres. With 429 municipalities × 54 parcels = 23,166 rows — computationally trivial.

3. For each municipality, find:
   - `min_dist_m`: minimum distance to any surrender parcel
   - `nearest_surrender_uid`: UNIQUE_ID of nearest parcel
   - `nearest_surrender_reserve`: reserve name of nearest parcel
   - `nearest_surrender_year`: `year_surr_clean` of nearest parcel
   - `n_surrenders_5km`: count of parcels within 5,000 m
   - `n_surrenders_25km`: count of parcels within 25,000 m
   - `overlap_flag`: boolean, any surrender parcel intersects the municipality polygon
   - `all_nearby_surrenders`: JSON list of all parcels within 25 km with distances and years

4. Retrieve from Neo4j for each municipality: `founded` year, `population_1921`, commercial type (via IS_TYPE join).

5. Compute temporal gap columns:
   - `founding_before_surrender`: municipal founding year < nearest surrender year (the "pressure then surrender" signal)
   - `surrender_before_founding`: nearest surrender year < municipal founding year
   - `years_gap`: `year_surr_clean` − `founded` (negative = municipality predates surrender)

6. Produce a ranked output table sorted by `min_dist_m` ascending.

7. Save to `analysis/01_proximity_results.xlsx` with sheets:
   - `Ranked_All` — all 429 municipalities ranked by proximity
   - `Within_5km` — municipalities within 5 km of surrendered land
   - `Overlapping` — municipalities with direct geometric overlap
   - `Pressure_Then_Surrender` — municipalities where `founding_before_surrender = True`
   - `Surrender_Then_Muni` — municipalities where `surrender_before_founding = True`
   - `Methodology` — distance thresholds, CRS used, data caveats

8. Save `analysis/01_proximity_map.geojson` of the 429 municipalities with proximity fields attached, EPSG:4326.

**Technical note on overlap detection:** Surrender parcel boundaries were drawn at the time of surrender and may not precisely match current urban polygon boundaries. Direct overlap should be interpreted as "the surrendered land became incorporated municipal land." The Notes field on surrender records often states this explicitly (e.g., the Cote reserve note: "Surrendered for sale and settlement of Kamsack").

---

### Phase 2 — Temporal Sequencing Analysis (`analysis/02_temporal_sequencing.py`)

**Purpose:** Use the year-by-year surrender acreage data from `Sask_Reserves_1931.xlsx` to reconstruct the progressive reduction of each reserve, and correlate that timeline with the growth trajectory of nearby municipalities.

**Steps:**

1. Load `surrenders_long.csv` and `01_proximity_results.xlsx` from Phase 0/1.

2. Filter to reserves that have at least one municipality within 25 km — the "affected reserves" set.

3. For each affected reserve:
   - Compute cumulative acres surrendered by decade (pre-1900, 1900–1909, 1910–1919, 1920–1933)
   - Compute percentage of original acreage surrendered by each decade endpoint
   - Note the decade of first surrender and the decade of greatest single-year surrender

4. For each municipality within 25 km of an affected reserve, retrieve from Neo4j:
   - `founded` year, `incorporated` year (from Event nodes)
   - Railway arrival year (from SERVED_BY relationship)

5. Build a combined timeline table: `UNIQUE_ID`, `reserve_name`, `muni_name`, `muni_founded`, `muni_incorporated`, `railway_arrival`, `surr_[year]` for each year in the surrender column set. This is the key evidence table for the dispossession argument.

6. Classify each reserve-municipality pair into three temporal types:
   - **Type A — Pre-emptive settlement:** Municipality founded and/or railway arrived before any surrender on the associated reserve. Strongest candidate for Raibmon/Waiser "pressure then surrender" argument.
   - **Type B — Concurrent:** Municipality founded within 5 years of major surrender.
   - **Type C — Post-surrender settlement:** Municipality founded after surrender complete. Consistent with conventional "opened land was then settled" narrative; does not exclude earlier informal pressure.

7. Compute a "dispossession intensity index" for context (not causal): total acres surrendered within 25 km of any municipality as a percentage of original acreage.

8. Save to `analysis/02_temporal_results.xlsx` with sheets:
   - `Timeline_Table` — full combined timeline per reserve-municipality pair
   - `Type_A_Cases` — pre-emptive settlement cases
   - `Type_B_Cases` — concurrent cases
   - `Type_C_Cases` — post-surrender cases
   - `Reserve_Reduction_Summary` — decade-by-decade acreage reduction per reserve
   - `Methodology`

---

### Phase 3 — Métis Overlap Analysis (`analysis/03_metis_overlap.py`)

**Purpose:** Identify spatial co-location and temporal overlap between Métis communities and urban municipalities, and document road allowance communities as evidence of displacement into marginal Crown land.

**Steps:**

1. Load `metis_located.gpkg` (42 georeferenced communities) and `urban_429.gpkg`.

2. For each Métis community point, compute distance to nearest urban municipality boundary (boundary distance, not centroid-to-centroid). Also flag whether the point falls within a municipality polygon.

3. Join Métis temporal data from `metis_full.csv` on `UNIQUE_ID`. Key fields: `Y_FOUND`, `Y_DEPART`, `TYPE`, population at 1860/1880/1900/1921/1940.

4. Identify overlapping cases: communities where the Métis community name matches or closely corresponds to a municipality name (Regina, Prince Albert, Saskatoon, Battleford, Moose Jaw, Estevan all appear in both datasets). For these, construct a side-by-side timeline: Métis `Y_FOUND`, municipal `founded`, Métis `Y_DEPART`. The pattern of Métis community departure coinciding with or following municipal founding/growth is the displacement signal.

5. Handle the 71 unlocated Métis communities separately. Produce a table with known `LOCATION` text and `TYPE` field for manual georeferencing notes. Flag road allowance communities explicitly — their marginal spatial position is itself evidence of displacement.

6. For located road allowance communities, compute distance to nearest municipal boundary and nearest railway line. Road allowance communities by definition formed in the gaps of the survey grid; their distance from municipalities and railways reflects intentional marginalisation.

7. Save to `analysis/03_metis_results.xlsx` with sheets:
   - `Displacement_Cases` — communities with both Métis presence and municipal overlap, with comparative timeline
   - `Road_Allowance_Profile` — road allowance communities with spatial context
   - `Unlocated_Communities` — 71 unlocated communities for future georeferencing
   - `All_Located_Proximity` — full proximity table for 42 located communities
   - `Methodology`

---

### Phase 4 — Case Study Builder (`analysis/04_case_studies.py`)

**Purpose:** Produce structured profiles for priority municipalities using all data assembled in Phases 1–3, formatted for qualitative follow-up and potential StoryMap integration.

**Priority cases:** Kamsack, Regina, North Battleford, Prince Albert, Broadview.

**Data already confirmed for Kamsack:** Three surrender records within or adjacent to the municipality — Cote (PRQA64, 16,240 acres, 1906, "Surrendered for sale and settlement of Kamsack"), Keeseekoose (PRQA66, 7,600 acres, 1909), and The Key (PRQA65, 11,500 acres, 1909). The Cote surrender note explicitly names Kamsack as the driver — this is the clearest documented case in the dataset.

**Steps:**

1. For each priority municipality, query all analysis outputs from Phases 1–3:
   - Municipality metadata: TCPUID, type, population 1921, founded, incorporated, railway arrival, commercial type
   - All surrender parcels within 50 km with full attributes including the `Notes` field
   - All Métis communities within 50 km with temporal data
   - Temporal sequence summary and Type A/B/C classification
   - Reserve population trajectory from `TPOP_*` fields in the surrender geojson

2. Query Neo4j for contextual graph data:
   ```cypher
   MATCH (s:Settlement {census_id: $tcpuid})
   OPTIONAL MATCH (s)-[:HAD_EVENT]->(e:Event)
   OPTIONAL MATCH (s)-[:SERVED_BY]->(r:RailwayLine)
   RETURN s, collect(e), collect(r)
   ```

3. Output: one Markdown file per case at `analysis/case_studies/[name].md` with sections:
   - Settlement overview
   - Surrendered reserve land in proximity (table)
   - Métis community presence (table)
   - Temporal sequence narrative (auto-generated from data, with Type classification)
   - Reserve population trajectory (table)
   - Verbatim surrender notes (`Notes` and `NOTES_1` fields)
   - Gaps and questions for qualitative follow-up (archival sources, newspapers, graphrag corpus)

4. Save `analysis/04_case_study_data.xlsx` with one sheet per case study.

---

### Phase 5 — Neo4j Enrichment (`analysis/05_neo4j_enrichment.py`)

**Purpose:** Write spatial analysis findings back into the Neo4j graph as properties on Settlement nodes, making dispossession proximity data queryable alongside all existing graph data.

**New properties to add to Settlement nodes:**

| Property | Type | Source |
|---|---|---|
| `min_dist_to_surrender_m` | float | Phase 1 |
| `nearest_surrender_reserve` | string | Phase 1 |
| `nearest_surrender_year` | int | Phase 1 |
| `n_surrenders_5km` | int | Phase 1 |
| `n_surrenders_25km` | int | Phase 1 |
| `overlap_with_surrender` | boolean | Phase 1 |
| `temporal_type` | string (A/B/C/none) | Phase 2 |
| `metis_community_present` | boolean | Phase 3 |
| `nearest_metis_community` | string | Phase 3 |
| `nearest_metis_dist_m` | float | Phase 3 |

This enables future graph queries combining commercial tier, founding timeline, and dispossession proximity in a single Cypher traversal.

---

## Script Execution Order and Dependencies

```
00_prepare_data.py              (no dependencies — runs first)
        |
        ├── 01_spatial_proximity.py     (depends on: 00 outputs + Neo4j)
        |
        ├── 02_temporal_sequencing.py   (depends on: 00 outputs + 01 outputs + Neo4j)
        |
        ├── 03_metis_overlap.py         (depends on: 00 outputs)
        |
        ├── 04_case_studies.py          (depends on: 01, 02, 03 outputs + Neo4j)
        |
        └── 05_neo4j_enrichment.py      (depends on: 01, 02, 03 outputs)
```

Phases 1, 2, and 3 can be run in parallel after Phase 0 completes.

---

## Directory Structure

```
Reserves_Urban_Spaces/
├── analysis/
│   ├── 00_prepare_data.py
│   ├── 01_spatial_proximity.py
│   ├── 02_temporal_sequencing.py
│   ├── 03_metis_overlap.py
│   ├── 04_case_studies.py
│   ├── 05_neo4j_enrichment.py
│   ├── data/                           # Phase 0 intermediate outputs
│   │   ├── urban_429.gpkg
│   │   ├── surrenders_clean.gpkg
│   │   ├── reserves_initial.gpkg
│   │   ├── reserves_master.csv
│   │   ├── surrenders_long.csv
│   │   ├── metis_located.gpkg
│   │   ├── metis_full.csv
│   │   └── neo4j_settlements.csv
│   ├── case_studies/                   # Phase 4 markdown outputs
│   │   ├── kamsack.md
│   │   ├── regina.md
│   │   ├── north_battleford.md
│   │   ├── prince_albert.md
│   │   └── broadview.md
│   ├── 01_proximity_results.xlsx
│   ├── 01_proximity_map.geojson
│   ├── 02_temporal_results.xlsx
│   ├── 03_metis_results.xlsx
│   └── 04_case_study_data.xlsx
```

---

## Python Dependencies

```
geopandas>=0.14
pandas>=2.0
fiona>=1.9
shapely>=2.0
openpyxl>=3.1
neo4j>=5.0
pyproj>=3.6
numpy>=1.26
```

EPSG:3347 requires pyproj with the PROJ datum grid for Canada. Confirm with:
`python -c "from pyproj import CRS; CRS.from_epsg(3347)"`

---

## Priority Case Study Quick-Reference

| Municipality | TCPUID | Type | Pop 1921 | Key Reserves in Proximity | Notes |
|---|---|---|---|---|---|
| Kamsack | SK179019 | Town | 2,002 | Cote (1906, 16,240 ac), Keeseekoose (1909, 7,600 ac), The Key (1909, 11,500 ac) | Cote surrender note explicitly names Kamsack |
| Regina | SK176022 | City | 34,432 | TBD from Phase 1 | Métis community present |
| North Battleford | SK186026 | City | 4,108 | TBD from Phase 1 | Métis: Battleford, Bresaylor, Jackfish Lake |
| Prince Albert | SK185026 | City | 7,558 | TBD from Phase 1 | Métis community present |
| Broadview | SK175021 | Town | 839 | TBD from Phase 1 | — |

---

## Limitations and Interpretive Caveats

**1. The 54 surrender parcels are not exhaustive.** `SK_ReserveSurrenders_1933.geojson` captures formal documented surrenders to 1933. Informal encroachments, road allowance alienations, and boundary adjustments in `Reserve_Boundary_Changes.geojson` represent additional reductions not counted in surrender acreage. Several boundary change notes explicitly describe survey "corrections" that reduced reserve size.

**2. Municipal polygon geometry is 1921 extent, not founding-year extent.** Municipalities grew between founding and 1921. A surrender parcel overlapping the 1921 polygon may not have overlapped the founding-year footprint. Overlap findings should be stated as "surrendered land later incorporated into the municipality" — establishing directionality requires the Notes field, as in the Kamsack case.

**3. Distance is boundary-to-boundary, not centroid-to-centroid.** This is correct for the argument — the edge of municipal land constituted settler pressure on reserve borders, not the town centre. But large municipalities (Regina, Prince Albert) will show smaller distances to everything, inflating their apparent dispossession proximity.

**4. 71 Métis communities lack coordinates.** The 42 georeferenced points are a partial picture skewed toward communities with surviving physical markers or clear place-name continuity. Road allowance communities — the most marginalised — are the most underrepresented in the georeferenced set. Any conclusion about Métis displacement must acknowledge this gap.

**5. `founded` in Neo4j ≠ formal incorporation.** It tracks first permanent settler occupation or first institutional presence. Formal `incorporated` year comes later. Both matter: `founded` better indicates when settler pressure began; `incorporated` marks administrative formalisation of territorial claim.

**6. Reserve population data (`TPOP_*` fields) is for the whole reserve, not just the surrendered portion.** Population decline following surrender cannot be read directly as surrender-caused without controlling for other variables. Figures are indicative, not conclusive.

**7. The analysis cannot identify pre-surrender settler encroachment from geospatial data alone.** This is the core Raibmon/Waiser argument — settlers farming reserve land before formal surrender — but it requires archival sources to document. The spatial and temporal analysis identifies *candidates* for this pattern; the corpus evidence (local histories and newspapers via graphrag) must do the argumentative work.

**8. The `Data_Certainty` field in the master table must be surfaced.** Several records have noted data quality flags. Aggregate claims should be filtered or weighted by this field — low-certainty records should not silently inflate acreage totals.

---

## Visualization Notes for StoryMap Integration

The Phase 1 GeoJSON output (`01_proximity_map.geojson`) is designed to be loaded directly into ArcGIS StoryMap or QGIS as an enriched municipality layer. Key display fields:
- `min_dist_band`: categorical (Overlap / Within 5km / Within 25km / Beyond 25km) for choropleth
- `temporal_type`: A/B/C/None for symbol differentiation
- `nearest_surrender_reserve`: tooltip text
- `founding_before_surrender`: boolean for filtering to "pressure then surrender" cases

The surrender parcel layer (`SK_ReserveSurrenders_1933.geojson`) can be styled by `YR_SUR` for temporal animation. The initial survey layer (`Reserves_Initial_Survey.geojson`) as a semi-transparent underlay shows original extent versus what remained.
