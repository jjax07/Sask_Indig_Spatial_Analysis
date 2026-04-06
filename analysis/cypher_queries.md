# Cypher Queries — Phase 5 Enrichment

Queries against the Neo4j graph following Phase 5 enrichment. All queries use properties written to `Settlement` nodes in Phase 5, combined with existing graph relationships.

## Schema reference

- `Settlement` properties (Phase 5): `min_dist_to_surrender_m`, `nearest_surrender_reserve`, `nearest_surrender_year`, `n_surrenders_5km`, `n_surrenders_25km`, `overlap_with_surrender`, `temporal_type`, `metis_community_present`, `nearest_metis_community`, `nearest_metis_dist_m`
- `Settlement` properties (existing): `census_id`, `census_name`, `csd_type`, `founded`, `incorporated`, `population_1921`, `latitude`, `longitude`
- `(s:Settlement)-[:IS_TYPE]->(ct:SettlementType)` — `ct.name` is the commercial type
- `(s:Settlement)-[:HAD_EVENT]->(e:Event)` — `e.type`, `e.year`, `e.context`
- `(s:Settlement)-[:SERVED_BY]->(r:RailwayLine)` — `r.builder_name`, `r.year_constructed`

---

## 1. "Pressure then surrender" core argument — Type A municipalities by commercial tier

```cypher
MATCH (s:Settlement)
OPTIONAL MATCH (s)-[:IS_TYPE]->(ct:SettlementType)
WHERE s.temporal_type = 'A'
RETURN
  ct.name                              AS commercial_type,
  count(s)                             AS n_municipalities,
  avg(s.min_dist_to_surrender_m)       AS avg_dist_m,
  collect(s.census_name)[..10]         AS examples
ORDER BY n_municipalities DESC
```

---

## 2. Triple convergence — Type A + geometric overlap + Métis presence

The highest-intensity dispossession cases: municipalities that predated a nearby surrender, overlap geometrically with surrendered land, and have an associated Métis community. Most useful for case study selection.

```cypher
MATCH (s:Settlement)
WHERE s.temporal_type = 'A'
  AND s.overlap_with_surrender = true
  AND s.metis_community_present = true
RETURN
  s.census_name             AS name,
  s.census_id               AS tcpuid,
  s.min_dist_to_surrender_m AS dist_m,
  s.nearest_surrender_reserve AS nearest_reserve,
  s.nearest_surrender_year  AS surrender_year,
  s.nearest_metis_community AS metis_community,
  s.nearest_metis_dist_m    AS metis_dist_m
ORDER BY s.min_dist_to_surrender_m ASC
```

---

## 3. Type A municipalities with the longest pre-emptive gaps

Tests the McGuire "petition cycle" argument: a long gap between municipal founding and formal surrender is not absence of pressure — it is the pressure. `founded` is a direct Settlement property.

```cypher
MATCH (s:Settlement)
WHERE s.temporal_type = 'A'
  AND s.nearest_surrender_year IS NOT NULL
  AND s.founded IS NOT NULL
RETURN
  s.census_name             AS name,
  s.founded                 AS founded_year,
  s.nearest_surrender_year  AS surrender_year,
  (s.nearest_surrender_year - s.founded) AS gap_years,
  s.nearest_surrender_reserve AS nearest_reserve,
  s.n_surrenders_25km       AS n_reserves_25km
ORDER BY gap_years DESC
LIMIT 20
```

---

## 4. Railway arrival + Type A — McGuire three-mechanism test

Tests whether railway arrival preceded formal surrender (McGuire's mechanisms 2 and 3: railway as driver of townsite demand and land market speculation).

**Note:** Railway data is stored as direct properties on Settlement nodes, not reliably via `SERVED_BY` relationships. Use `s.railway_arrives` and `s.first_railway`.

```cypher
MATCH (s:Settlement)
WHERE s.temporal_type = 'A'
  AND s.nearest_surrender_year IS NOT NULL
  AND s.railway_arrives IS NOT NULL
RETURN
  s.census_name               AS name,
  s.first_railway             AS railway_company,
  s.railway_arrives           AS railway_year,
  s.nearest_surrender_year    AS surrender_year,
  s.nearest_surrender_reserve AS nearest_reserve,
  s.n_surrenders_25km         AS n_reserves_25km,
  (s.nearest_surrender_year - s.railway_arrives) AS rail_before_surrender_yrs
ORDER BY rail_before_surrender_yrs DESC
LIMIT 25
```

---

## 4a. Corridor clustering — reserves with multiple Type A municipalities within 25 km

Identifies all surrendered reserves that had three or more Type A municipalities within 25 km, giving the full picture of corridor-wide pressure across the dataset. For each such reserve, lists the municipalities, their railway companies, and railway arrival years to reveal whether the pressure came from a single line or multiple converging corridors.

Note: `n_surrenders_25km` is a property on Settlement nodes (count of surrendered parcels near that municipality), not a count of municipalities near a reserve. This query works from the municipality side, grouping by nearest reserve to reconstruct the reserve-level picture.

```cypher
MATCH (s:Settlement)
WHERE s.temporal_type = 'A'
  AND s.nearest_surrender_reserve IS NOT NULL
  AND s.railway_arrives IS NOT NULL
WITH
  s.nearest_surrender_reserve  AS reserve,
  s.nearest_surrender_year     AS surrender_year,
  collect(s.census_name)       AS municipalities,
  collect(s.first_railway)     AS railways,
  collect(s.railway_arrives)   AS railway_years,
  count(s)                     AS n_type_a_munis
WHERE n_type_a_munis >= 3
RETURN
  reserve,
  surrender_year,
  n_type_a_munis,
  municipalities,
  railways,
  railway_years
ORDER BY n_type_a_munis DESC
```

---

## 3a. Founding-type profiles for Type A municipalities with long pre-emptive gaps

Pulls founding event context and key institutional event types for all Type A municipalities with a founding-to-surrender gap greater than 15 years. Purpose: to surface the diversity of colonial founding types (administrative, fur trade, religious/mission, colonization company, residential school, railway townsite, agricultural colony) across the long-gap set, going beyond the railway corridor pattern identified in Query 4.

**Data caveat:** Event data was recorded specifically about the urban municipality as an administrative entity, not about all prior settlement in that location. Pre-municipal institutional presence (missions, HBC posts) may appear only as passing references in founding context notes, or not at all. Absences should not be read as absence of that presence — they may reflect the scope of data collection. Where non-railway institutional types do appear, their inclusion is analytically significant.

```cypher
MATCH (s:Settlement)
WHERE s.temporal_type = 'A'
  AND s.nearest_surrender_year IS NOT NULL
  AND s.founded IS NOT NULL
  AND (s.nearest_surrender_year - s.founded) > 15
WITH s, (s.nearest_surrender_year - s.founded) AS gap_years
OPTIONAL MATCH (s)-[:HAD_EVENT]->(e:Event)
WHERE e.type IN ['founding', 'colonization_company', 'justice_system', 'first_church', 'first_school']
RETURN
  s.census_name             AS name,
  s.founded                 AS founded,
  s.nearest_surrender_year  AS surrender_year,
  gap_years,
  s.nearest_surrender_reserve AS nearest_reserve,
  collect({type: e.type, year: e.year, context: e.context}) AS key_events
ORDER BY gap_years DESC
```

---

## 4b. Reserves with multiple surrender events in the Type A set

Checks whether any reserves appear more than once across Type A municipalities — indicating multiple separate surrenders on the same reserve, each correlated with a different wave of settlement. Piapot appeared twice in Query 4a; this query tests whether that pattern occurs elsewhere.

```cypher
MATCH (s:Settlement)
WHERE s.temporal_type = 'A'
  AND s.nearest_surrender_reserve IS NOT NULL
WITH
  s.nearest_surrender_reserve AS reserve,
  s.nearest_surrender_year    AS surrender_year,
  count(s)                    AS n_type_a_munis
WITH
  reserve,
  collect({year: surrender_year, n: n_type_a_munis}) AS surrender_events,
  count(DISTINCT surrender_year)                      AS n_distinct_surrenders
WHERE n_distinct_surrenders > 1
RETURN
  reserve,
  n_distinct_surrenders,
  surrender_events
ORDER BY n_distinct_surrenders DESC
```

---

## 4c. Full railway-to-surrender gap distribution for all Type A municipalities

Query 4 showed only the top 25 by gap length. This query returns the full distribution across all Type A municipalities, grouped into gap bands, to test whether gaps cluster in the 1900–1920 settlement boom window.

```cypher
MATCH (s:Settlement)
WHERE s.temporal_type = 'A'
  AND s.nearest_surrender_year IS NOT NULL
  AND s.railway_arrives IS NOT NULL
WITH
  s.census_name                                    AS name,
  s.railway_arrives                                AS railway_year,
  s.nearest_surrender_year                         AS surrender_year,
  s.nearest_surrender_reserve                      AS reserve,
  (s.nearest_surrender_year - s.railway_arrives)   AS gap_yrs
RETURN
  CASE
    WHEN gap_yrs < 0  THEN 'Surrender before railway'
    WHEN gap_yrs = 0  THEN '0 years'
    WHEN gap_yrs <= 5 THEN '1–5 years'
    WHEN gap_yrs <= 10 THEN '6–10 years'
    WHEN gap_yrs <= 20 THEN '11–20 years'
    WHEN gap_yrs <= 30 THEN '21–30 years'
    ELSE '31+ years'
  END                  AS gap_band,
  count(s)             AS n_municipalities,
  min(gap_yrs)         AS min_gap,
  max(gap_yrs)         AS max_gap,
  round(avg(gap_yrs))  AS avg_gap
ORDER BY min_gap
```

---

## 4d. Railway company frequency across Type A corridor clusters

Counts how many Type A municipalities and how many distinct reserves each railway company is associated with, to establish which companies drove corridor pressure most broadly across the province.

```cypher
MATCH (s:Settlement)
WHERE s.temporal_type = 'A'
  AND s.first_railway IS NOT NULL
  AND s.nearest_surrender_reserve IS NOT NULL
RETURN
  s.first_railway                           AS railway_company,
  count(s)                                  AS n_type_a_munis,
  count(DISTINCT s.nearest_surrender_reserve) AS n_distinct_reserves,
  collect(DISTINCT s.nearest_surrender_reserve)[..10] AS reserves_sample
ORDER BY n_type_a_munis DESC
```

---

## 4e. The Punnichy / George Gordon outlier cluster

Pulls the full profile of the George Gordon cluster — the late-surrendering (1933), high-density outlier identified in Query 4. Includes all Type A municipalities within 25 km, their railway context, and the gap to surrender, to characterize what made this case distinct from the boom-era corridor pattern.

```cypher
MATCH (s:Settlement)
WHERE s.temporal_type = 'A'
  AND s.nearest_surrender_reserve = 'George Gordon'
RETURN
  s.census_name               AS name,
  s.founded                   AS founded,
  s.first_railway             AS railway_company,
  s.railway_arrives           AS railway_year,
  s.nearest_surrender_year    AS surrender_year,
  s.n_surrenders_25km         AS n_reserves_25km,
  (s.nearest_surrender_year - s.railway_arrives) AS gap_yrs,
  s.metis_community_present   AS metis_present,
  s.population_1921           AS pop_1921
ORDER BY s.railway_arrives
```

---

## 5. Métis displacement arc — community proximity and temporal sequence

For all municipalities with an associated Métis community, surfaces the founding year and surrender temporal type. Cross-reference `muni_founded` against the Métis community's `Y_FOUND` (in `Métis_Communities.xlsx`) to identify cases where the Métis community predated the municipality.

```cypher
MATCH (s:Settlement)
WHERE s.metis_community_present = true
RETURN
  s.census_name              AS municipality,
  s.founded                  AS muni_founded,
  s.nearest_metis_community  AS metis_community,
  s.nearest_metis_dist_m     AS metis_dist_m,
  s.temporal_type            AS surrender_temporal_type,
  s.overlap_with_surrender   AS overlap
ORDER BY metis_dist_m ASC
```

---

## 6. High surrender density — cluster pressure analysis

Municipalities with three or more surrendered parcels within 25 km. These are the regions of most concentrated reserve reduction, likely corresponding to railway corridors where multiple reserves were targeted.

```cypher
MATCH (s:Settlement)
WHERE s.n_surrenders_25km >= 3
OPTIONAL MATCH (s)-[:IS_TYPE]->(ct:SettlementType)
RETURN
  s.census_name             AS name,
  ct.name                   AS commercial_type,
  s.n_surrenders_25km       AS n_25km,
  s.n_surrenders_5km        AS n_5km,
  s.temporal_type           AS temporal_type,
  s.min_dist_to_surrender_m AS min_dist_m,
  s.metis_community_present AS metis_present
ORDER BY s.n_surrenders_25km DESC
```

---

## 7. The 6 geometric overlap cases — full profile

Full event and railway context for municipalities whose 1921 polygon geometry overlaps with surrendered reserve land. These are the strongest spatial cases: surrendered land was directly incorporated into municipal territory.

```cypher
MATCH (s:Settlement)
WHERE s.overlap_with_surrender = true
OPTIONAL MATCH (s)-[:IS_TYPE]->(ct:SettlementType)
OPTIONAL MATCH (s)-[:HAD_EVENT]->(e:Event)
OPTIONAL MATCH (s)-[:SERVED_BY]->(r:RailwayLine)
RETURN
  s.census_name             AS name,
  ct.name                   AS commercial_type,
  s.nearest_surrender_reserve AS reserve,
  s.nearest_surrender_year  AS surrender_year,
  s.temporal_type           AS temporal_type,
  s.metis_community_present AS metis_present,
  collect(DISTINCT toString(e.year) + ': ' + e.context)[..5] AS events,
  collect(DISTINCT r.builder_name) AS railways
```

---

## 8. Type A cities and towns only — organized settler pressure frame

Filters to higher-tier settlements (RSC/LSC commercial types) where settler pressure would have been most organized and commercially motivated. Villages are excluded.

```cypher
MATCH (s:Settlement)-[:IS_TYPE]->(ct:SettlementType)
WHERE s.temporal_type = 'A'
  AND ct.name IN ['RSC', 'LSC']
RETURN
  s.census_name             AS name,
  ct.name                   AS commercial_type,
  s.nearest_surrender_reserve AS nearest_reserve,
  s.nearest_surrender_year  AS surrender_year,
  s.n_surrenders_25km       AS n_reserves_25km,
  s.min_dist_to_surrender_m AS dist_m,
  s.metis_community_present AS metis_present
ORDER BY s.n_surrenders_25km DESC, s.min_dist_to_surrender_m ASC
```

---

## 9. Summary statistics — aggregate view of all temporal types

Overview table for reporting: counts, average distances, and co-occurrence rates for overlap and Métis presence across all temporal type categories.

```cypher
MATCH (s:Settlement)
RETURN
  s.temporal_type                        AS type,
  count(s)                               AS n,
  round(avg(s.min_dist_to_surrender_m))  AS avg_min_dist_m,
  sum(CASE WHEN s.overlap_with_surrender THEN 1 ELSE 0 END) AS n_overlap,
  sum(CASE WHEN s.metis_community_present THEN 1 ELSE 0 END) AS n_metis,
  sum(CASE WHEN s.n_surrenders_5km > 0 THEN 1 ELSE 0 END)   AS n_within_5km
ORDER BY type
```

---

## 10. Frank Oliver's 1911 amendment — large municipalities near surrenders

The 1911 *Indian Act* amendment permitted expropriation without consent where a reserve was near a town exceeding 8,000 population. Surfaces Type A and B municipalities that met or approached that threshold by 1921.

```cypher
MATCH (s:Settlement)
WHERE s.population_1921 >= 8000
  AND s.temporal_type IN ['A', 'B']
OPTIONAL MATCH (s)-[:IS_TYPE]->(ct:SettlementType)
RETURN
  s.census_name             AS name,
  s.population_1921         AS pop_1921,
  ct.name                   AS commercial_type,
  s.nearest_surrender_reserve AS nearest_reserve,
  s.nearest_surrender_year  AS surrender_year,
  s.min_dist_to_surrender_m AS dist_m,
  s.metis_community_present AS metis_present
ORDER BY s.population_1921 DESC
```
