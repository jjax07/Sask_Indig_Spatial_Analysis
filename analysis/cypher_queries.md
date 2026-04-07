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

## 3a (sensitized). Combined event- and Métis-anchored effective gap

**Requires:** `nearest_metis_y_found` property on Settlement nodes (written by inline enrichment script, 2026-04-06 — 32 nodes updated from `analysis/data/metis_full.csv`).

Computes `effective_start = min(founded, earliest institutional event year, nearest_metis_y_found)` and flags which anchor was determinative (`founded` / `event` / `metis`). Returns all Type A municipalities with `effective_gap > 15`, showing both the formal gap and the corrected gap side by side.

```cypher
MATCH (s:Settlement)
WHERE s.temporal_type = 'A'
  AND s.nearest_surrender_year IS NOT NULL
  AND s.founded IS NOT NULL
OPTIONAL MATCH (s)-[:HAD_EVENT]->(e:Event)
WHERE e.type IN ['founding', 'colonization_company', 'justice_system', 'first_church', 'first_school']
  AND e.year IS NOT NULL
WITH s,
  s.founded                AS formal_founded,
  s.nearest_surrender_year AS surrender_year,
  s.nearest_metis_y_found  AS metis_y_found,
  min(e.year)              AS earliest_event_year
WITH s, formal_founded, surrender_year, metis_y_found, earliest_event_year,
  reduce(m = formal_founded, x IN [earliest_event_year, metis_y_found] |
    CASE WHEN x IS NOT NULL AND x < m THEN x ELSE m END
  ) AS effective_start,
  CASE
    WHEN metis_y_found IS NOT NULL AND
         (earliest_event_year IS NULL OR metis_y_found <= earliest_event_year) AND
         metis_y_found < formal_founded
    THEN 'metis'
    WHEN earliest_event_year IS NOT NULL AND earliest_event_year < formal_founded
    THEN 'event'
    ELSE 'founded'
  END AS anchor
WITH s, formal_founded, surrender_year, metis_y_found, earliest_event_year,
     effective_start, anchor,
  (surrender_year - formal_founded) AS formal_gap,
  (surrender_year - effective_start) AS effective_gap
WHERE effective_gap > 15
RETURN
  s.census_name               AS name,
  formal_founded              AS founded,
  metis_y_found,
  earliest_event_year,
  effective_start,
  anchor,
  surrender_year,
  s.nearest_surrender_reserve AS nearest_reserve,
  formal_gap,
  effective_gap,
  (effective_gap - formal_gap) AS gap_correction
ORDER BY effective_gap DESC
LIMIT 35
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

## 5a. Métis temporal sequence — who predated whom

**Requires:** `nearest_metis_y_found` property on Settlement nodes (written during Query 3a sensitized enrichment, 2026-04-06).

Extends Query 5 by adding `nearest_metis_y_found` and computing the gap between Métis community founding and municipal founding. Classifies each case as `metis_first`, `same_year`, `muni_first`, or `unknown`. Sorted by gap descending so the deepest precedence cases appear first.

```cypher
MATCH (s:Settlement)
WHERE s.metis_community_present = true
RETURN
  s.census_name              AS municipality,
  s.founded                  AS muni_founded,
  s.nearest_metis_community  AS metis_community,
  s.nearest_metis_y_found    AS metis_y_found,
  s.nearest_metis_dist_m     AS metis_dist_m,
  s.temporal_type            AS temporal_type,
  s.overlap_with_surrender   AS overlap,
  CASE
    WHEN s.nearest_metis_y_found IS NULL OR s.founded IS NULL THEN 'unknown'
    WHEN s.nearest_metis_y_found < s.founded THEN 'metis_first'
    WHEN s.nearest_metis_y_found = s.founded THEN 'same_year'
    ELSE 'muni_first'
  END AS sequence
ORDER BY
  CASE WHEN s.nearest_metis_y_found IS NULL OR s.founded IS NULL THEN 1 ELSE 0 END,
  s.founded - s.nearest_metis_y_found DESC
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

**Note:** Railway data is stored as direct properties on Settlement nodes, not reliably via `SERVED_BY` relationships. Use `s.first_railway` and `s.railway_arrives`.

```cypher
MATCH (s:Settlement)
WHERE s.overlap_with_surrender = true
OPTIONAL MATCH (s)-[:IS_TYPE]->(ct:SettlementType)
OPTIONAL MATCH (s)-[:HAD_EVENT]->(e:Event)
WITH s, ct, e
WITH s,
  collect(DISTINCT ct.name)                                        AS commercial_types,
  collect(DISTINCT toString(e.year) + ': ' + e.context)[..5]      AS events
RETURN
  s.census_name               AS name,
  commercial_types,
  s.nearest_surrender_reserve AS reserve,
  s.nearest_surrender_year    AS surrender_year,
  s.temporal_type             AS temporal_type,
  s.metis_community_present   AS metis_present,
  s.first_railway             AS railway,
  s.railway_arrives           AS rail_year,
  events
```

---

## 7a. Overlap cases — cross-query synthesis profile

Pulls together all analytically relevant properties for the 6 geometric overlap municipalities in a single row per settlement: effective presence (corrected for institutional events and Métis founding), formal and effective gaps, railway gap, and surrender density. Purpose: to enable side-by-side comparison of the mechanisms operating across the overlap set and support the unified dispossession argument.

**Note:** `effective_start` uses `min(founded, earliest institutional event year, nearest_metis_y_found)`. Leask has null `founded` and null `nearest_metis_y_found`; its effective_start is anchored to the earliest event year (1912), which postdates its surrender (1911) — a data gap, not an analytical finding. Leask's Type A classification was assigned in Phase 2 from criteria not fully captured in the `founded` property.

```cypher
MATCH (s:Settlement)
WHERE s.overlap_with_surrender = true
OPTIONAL MATCH (s)-[:HAD_EVENT]->(e:Event)
WHERE e.type IN ['founding', 'colonization_company', 'justice_system', 'first_church', 'first_school']
  AND e.year IS NOT NULL
WITH s, min(e.year) AS earliest_event_year
WITH s, earliest_event_year,
  [x IN [s.founded, earliest_event_year, s.nearest_metis_y_found] WHERE x IS NOT NULL] AS anchors
WITH s, earliest_event_year,
  CASE WHEN size(anchors) > 0
    THEN reduce(m = anchors[0], x IN anchors | CASE WHEN x < m THEN x ELSE m END)
    ELSE null END AS effective_start
RETURN
  s.census_name               AS name,
  s.temporal_type             AS temporal_type,
  s.founded                   AS founded,
  s.nearest_metis_y_found     AS metis_y_found,
  earliest_event_year,
  effective_start,
  s.nearest_surrender_year    AS surrender_year,
  (s.nearest_surrender_year - s.founded)        AS formal_gap,
  (s.nearest_surrender_year - effective_start)  AS effective_gap,
  s.first_railway             AS railway,
  s.railway_arrives           AS rail_year,
  (s.nearest_surrender_year - s.railway_arrives) AS rail_gap,
  s.nearest_surrender_reserve AS reserve,
  s.n_surrenders_5km          AS n_5km,
  s.n_surrenders_25km         AS n_25km,
  s.metis_community_present   AS metis_present,
  s.nearest_metis_community   AS metis_community,
  s.nearest_metis_dist_m      AS metis_dist_m
ORDER BY s.nearest_surrender_year ASC
```

---

## 8. Type A cities and towns only — organized settler pressure frame

Filters to higher-tier settlements (RSC/LSC commercial types) where settler pressure would have been most organized and commercially motivated. Villages are excluded.

```cypher
MATCH (s:Settlement)-[:IS_TYPE]->(ct:SettlementType)
WHERE s.temporal_type = 'A'
  AND ct.name IN ['Regional Service Centre', 'Local Service Centre', 'City']
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

## 8a. Indirect benefit — geographic hinterland density around RSC/LSC settlements

Tests the indirect benefit chain geographically: rather than measuring an RSC's own distance to surrendered land, counts the Type A farm clusters and small villages within 50km whose presence near surrendered land generated the agricultural hinterland from which larger centres drew commercial benefit. A high hinterland count indicates the RSC sat at the hub of a dispossession frontier, even if it did not sit on surrendered land itself.

**Note:** This query approximates hinterland proximity using the Haversine formula on latitude/longitude properties. It does not use graph relationships between settlements — it computes point-to-point distance between all RSC/LSC nodes and all Type A small-settlement nodes.

```cypher
MATCH (hub:Settlement)-[:IS_TYPE]->(hub_ct:SettlementType)
WHERE hub.temporal_type = 'A'
  AND hub_ct.name IN ['Regional Service Centre', 'Local Service Centre', 'City']
MATCH (sat:Settlement)-[:IS_TYPE]->(sat_ct:SettlementType)
WHERE sat.temporal_type = 'A'
  AND sat_ct.name IN ['Farm Cluster', 'Farm-Service Town', 'Small Service Centre',
                      'Railway Town', 'Organized/Ethnic Settlement']
  AND sat.census_name <> hub.census_name
WITH hub, sat,
  point.distance(
    point({latitude: hub.latitude, longitude: hub.longitude}),
    point({latitude: sat.latitude, longitude: sat.longitude})
  ) AS dist_m
WHERE dist_m <= 50000
WITH hub,
  count(sat)                    AS n_type_a_satellites,
  round(avg(sat.min_dist_to_surrender_m)) AS avg_satellite_dist_to_surrender_m,
  collect(sat.census_name)[..8] AS satellite_sample
RETURN
  hub.census_name               AS hub,
  hub.min_dist_to_surrender_m   AS hub_dist_to_surrender_m,
  n_type_a_satellites,
  avg_satellite_dist_to_surrender_m,
  satellite_sample
ORDER BY n_type_a_satellites DESC
```

---

## 8b. Indirect benefit — railway-mediated hinterland around RSC/LSC settlements

Tests the same indirect benefit chain through the railway network rather than raw geography. Identifies RSC/LSC settlements that share a railway line (via `first_railway` property) with Type A farm clusters and small settlements near surrendered land. The railway is the mechanism through which agricultural surplus, commercial traffic, and population growth were transferred from the dispossession frontier to the larger service centres.

**Note:** Uses `first_railway` as a proxy for shared corridor — settlements served by the same company on the same general line. This is an approximation; settlements served by the same company but on different branch lines may be grouped together.

```cypher
MATCH (hub:Settlement)-[:IS_TYPE]->(hub_ct:SettlementType)
WHERE hub.temporal_type = 'A'
  AND hub_ct.name IN ['Regional Service Centre', 'Local Service Centre', 'City']
  AND hub.first_railway IS NOT NULL
MATCH (sat:Settlement)-[:IS_TYPE]->(sat_ct:SettlementType)
WHERE sat.temporal_type = 'A'
  AND sat_ct.name IN ['Farm Cluster', 'Farm-Service Town', 'Small Service Centre',
                      'Railway Town', 'Organized/Ethnic Settlement']
  AND sat.first_railway = hub.first_railway
  AND sat.census_name <> hub.census_name
  AND sat.min_dist_to_surrender_m IS NOT NULL
RETURN
  hub.census_name               AS hub,
  hub.first_railway             AS railway,
  hub.min_dist_to_surrender_m   AS hub_dist_to_surrender_m,
  count(sat)                    AS n_railway_satellites,
  round(avg(sat.min_dist_to_surrender_m)) AS avg_satellite_dist_to_surrender_m,
  min(sat.min_dist_to_surrender_m)        AS min_satellite_dist_m,
  collect(sat.census_name)[..8] AS satellite_sample
ORDER BY n_railway_satellites DESC
```

---

## 8c. Commercial type gradient — average distance to surrendered land by type

Formal confirmation of the distance gradient across all commercial types. Returns average and median distance to the nearest surrendered parcel for every commercial type in the dataset, making the two-tier mechanism argument — farm clusters needed direct land access, larger centres benefited indirectly — visible in a single table.

```cypher
MATCH (s:Settlement)-[:IS_TYPE]->(ct:SettlementType)
WHERE s.min_dist_to_surrender_m IS NOT NULL
WITH ct.name AS commercial_type,
  count(s)                              AS n,
  round(avg(s.min_dist_to_surrender_m)) AS avg_dist_m,
  round(percentileCont(s.min_dist_to_surrender_m, 0.5)) AS median_dist_m,
  min(s.min_dist_to_surrender_m)        AS min_dist_m,
  max(s.min_dist_to_surrender_m)        AS max_dist_m,
  sum(CASE WHEN s.temporal_type = 'A' THEN 1 ELSE 0 END) AS n_type_a,
  sum(CASE WHEN s.overlap_with_surrender THEN 1 ELSE 0 END) AS n_overlap
RETURN commercial_type, n, avg_dist_m, median_dist_m, min_dist_m, max_dist_m, n_type_a, n_overlap
ORDER BY avg_dist_m ASC
```

---

## 8d. RSC/LSC settlements with highest farm-cluster hinterland density

Identifies which RSC/LSC/City settlements have the greatest concentration of Type A small settlements within 50km, regardless of how close those satellites sit to surrendered land. Where 8a asks "how close to surrendered land were the satellites?", this asks "which RSCs commanded the densest agricultural hinterlands?" — directly testing the "RSC as service hub for the dispossession frontier" framing. Battleford is the expected leader given Query 6 findings, but this query surfaces the full ranking.

```cypher
MATCH (hub:Settlement)-[:IS_TYPE]->(hub_ct:SettlementType)
WHERE hub_ct.name IN ['Regional Service Centre', 'Local Service Centre', 'City']
  AND hub.latitude IS NOT NULL
MATCH (sat:Settlement)-[:IS_TYPE]->(sat_ct:SettlementType)
WHERE sat.temporal_type = 'A'
  AND sat_ct.name IN ['Farm Cluster', 'Farm-Service Town', 'Small Service Centre',
                      'Railway Town', 'Organized/Ethnic Settlement']
  AND sat.census_name <> hub.census_name
  AND sat.latitude IS NOT NULL
WITH hub, sat,
  point.distance(
    point({latitude: hub.latitude, longitude: hub.longitude}),
    point({latitude: sat.latitude, longitude: sat.longitude})
  ) AS dist_m
WHERE dist_m <= 50000
WITH hub,
  count(sat)                    AS n_type_a_satellites,
  collect(sat.census_name)[..8] AS satellite_sample
RETURN
  hub.census_name               AS hub,
  hub.temporal_type             AS hub_temporal_type,
  hub.min_dist_to_surrender_m   AS hub_dist_to_surrender_m,
  n_type_a_satellites,
  satellite_sample
ORDER BY n_type_a_satellites DESC
LIMIT 20
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

---

## 11a. Type B municipalities — compressed pressure or anticipated surrender?

For each Type B municipality, surfaces the gaps between railway arrival, founding, and surrender to distinguish two sub-patterns: (1) compressed Type A — railway arrives, town founded, surrender follows rapidly; (2) anticipated surrender — town and surrender arrive simultaneously, suggesting the surrender was pre-arranged to accommodate incoming settlement. Ordered by rail-to-surrender gap ascending to surface the most simultaneous cases first.

```cypher
MATCH (s:Settlement)
WHERE s.temporal_type = 'B'
  AND s.nearest_surrender_year IS NOT NULL
OPTIONAL MATCH (s)-[:IS_TYPE]->(ct:SettlementType)
RETURN
  s.census_name                                         AS name,
  s.founded                                             AS founded,
  s.railway_arrives                                     AS railway_year,
  s.first_railway                                       AS railway,
  s.nearest_surrender_year                              AS surrender_year,
  s.nearest_surrender_reserve                           AS reserve,
  s.n_surrenders_25km                                   AS n_25km,
  s.min_dist_to_surrender_m                             AS dist_m,
  s.metis_community_present                             AS metis_present,
  (s.nearest_surrender_year - s.founded)                AS found_to_surrender_yrs,
  (s.nearest_surrender_year - s.railway_arrives)        AS rail_to_surrender_yrs,
  collect(DISTINCT ct.name)                             AS commercial_types
ORDER BY rail_to_surrender_yrs ASC
```

---

## 11b. Type C municipalities — post-surrender absorption profile

Full profile of all Type C municipalities: how long after the surrender each was founded, whether Métis communities were present (testing the three-layer sequence: surrender → Métis displacement → municipal founding), and what institutional events appear in the record. Ordered by years-after-surrender ascending to show the most rapid post-surrender settlements first.

```cypher
MATCH (s:Settlement)
WHERE s.temporal_type = 'C'
  AND s.nearest_surrender_year IS NOT NULL
OPTIONAL MATCH (s)-[:IS_TYPE]->(ct:SettlementType)
OPTIONAL MATCH (s)-[:HAD_EVENT]->(e:Event)
WHERE e.type IN ['founding', 'colonization_company', 'first_church', 'first_school']
  AND e.year IS NOT NULL
RETURN
  s.census_name                                         AS name,
  s.nearest_surrender_year                              AS surrender_year,
  s.founded                                             AS founded,
  (s.founded - s.nearest_surrender_year)                AS years_after_surrender,
  s.nearest_surrender_reserve                           AS reserve,
  s.min_dist_to_surrender_m                             AS dist_m,
  s.metis_community_present                             AS metis_present,
  s.nearest_metis_y_found                               AS metis_y_found,
  s.first_railway                                       AS railway,
  s.railway_arrives                                     AS railway_year,
  collect(DISTINCT ct.name)                             AS commercial_types,
  collect(DISTINCT toString(e.year) + ': ' + e.context)[..3] AS key_events
ORDER BY years_after_surrender ASC
```

---

## 11c. Cross-type — A, B, and C municipalities nearest the same reserve

Identifies reserves that attracted municipalities of more than one temporal type — showing all three benefit mechanisms (pressure, simultaneity, absorption) operating on the same piece of land at different moments. Ordered by number of distinct types present, then by total municipality count.

```cypher
MATCH (s:Settlement)
WHERE s.temporal_type IN ['A', 'B', 'C']
  AND s.nearest_surrender_reserve IS NOT NULL
WITH s.nearest_surrender_reserve  AS reserve,
     s.nearest_surrender_year     AS surrender_year,
     collect({
       name:         s.census_name,
       type:         s.temporal_type,
       founded:      s.founded,
       dist_m:       s.min_dist_to_surrender_m,
       railway:      s.first_railway,
       railway_year: s.railway_arrives,
       metis:        s.metis_community_present
     })                           AS municipalities,
     collect(DISTINCT s.temporal_type) AS types_present,
     count(s)                     AS n_municipalities
WHERE size(types_present) >= 2
RETURN
  reserve,
  surrender_year,
  types_present,
  n_municipalities,
  municipalities
ORDER BY size(types_present) DESC, n_municipalities DESC
```
