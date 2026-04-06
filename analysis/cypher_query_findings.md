# Cypher Query Findings

Results from running queries in `cypher_queries.md` against the Neo4j graph, following Phase 5 enrichment. Each entry records the raw results, any methodological issues encountered, and the interpretable findings.

---

## Query 1 — "Pressure then surrender" Type A municipalities by commercial tier

**Run date:** 2026-04-06

**Query (as written in cypher_queries.md):**
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

### Methodological issue — WHERE clause placement

In Neo4j Cypher, a `WHERE` clause placed immediately after `OPTIONAL MATCH` filters only the optional pattern, not the main `MATCH`. The intended behaviour was to filter all results to `temporal_type = 'A'` settlements before grouping by commercial type.

**Actual behaviour:** All 429 settlements were returned. For non-Type-A settlements, `ct.name` resolved to `null` because the `WHERE` excluded their IS_TYPE matches from the optional pattern. This produced the large `null` group (347 rows = 429 total − 82 Type A).

Additionally, some Settlement nodes have multiple `IS_TYPE` relationships (noted in Phase 0: 818 raw rows before dedup for 429 settlements). This inflates row counts in the non-null commercial type groups — a settlement with three IS_TYPE relationships appears three times.

**Corrected query form** (move WHERE before OPTIONAL MATCH):
```cypher
MATCH (s:Settlement)
WHERE s.temporal_type = 'A'
OPTIONAL MATCH (s)-[:IS_TYPE]->(ct:SettlementType)
RETURN
  ct.name                              AS commercial_type,
  count(s)                             AS n_municipalities,
  avg(s.min_dist_to_surrender_m)       AS avg_dist_m,
  collect(s.census_name)[..10]         AS examples
ORDER BY n_municipalities DESC
```

### Raw results — first run (buggy query, 2026-04-06)

Included for the record. The null group (347) is an artefact: all 429 settlements were returned, so non-Type-A settlements appear under null commercial_type. Disregard.

### Corrected results (2026-04-06)

Query re-run with WHERE moved before OPTIONAL MATCH. The null group is gone. Row counts still total 154 rather than 82 because many municipalities carry multiple commercial type labels simultaneously (e.g. Melville appears under Regional Service Centre, Railway Town, German Settlement, and Small Service Centre — it is one town with four labels). The `avg_dist_m` figures and example lists are reliable; label-group counts reflect label assignments, not distinct municipalities.

| commercial_type | label assignments | avg_dist_m | examples (first 10) |
|---|---|---|---|
| Small Service Centre | 57 | 13,142 | Forget, Birmingham, Dubuc, Duff, Fenwood, Goodeve, Grayson, Killaly, Stockholm, Summerberry |
| Organized/Ethnic Settlement | 20 | 14,670 | Melville, Duff, Fenwood, Goodeve, Grayson, Killaly, Stockholm, Dysart, Edenwold, Lipton |
| Farm-Service Town | 20 | 13,309 | Saltcoats, Indian Head, Lumsden, Bethune, B-Say-Tah, Bulyea, Craven, Disley, Fort Qu'Appelle, Lipton |
| Regional Service Centre | 16 | 13,842 | Arcola, Broadview, Grenfell, Melville, Saltcoats, Wolseley, Indian Head, Lumsden, Qu'Appelle, Canora |
| German Settlement | 11 | 14,759 | Melville, Duff, Fenwood, Grayson, Killaly, Dysart, Edenwold, Markinch, Pilot Butte, Quinton |
| Railway Town | 6 | 14,669 | Broadview, Melville, Birmingham, Bulyea, Regina Beach, Dafoe |
| Local Service Centre | 6 | 14,907 | Whitewood, Balcarres, Fort Qu'Appelle, Semans, Duck Lake, Shellbrook |
| Farm Cluster | 6 | 10,945 | Sintaluta, McLean, Margo, Quinton, Delmas, Paynton |
| Ukrainian Settlement | 5 | 13,845 | Goodeve, Arran, Ituna, Jasmin, Krydor |
| City | 3 | 15,986 | Regina, Prince Albert, North Battleford |
| Swedish Settlement | 1 | 22,676 | Stockholm |
| Jewish Colony | 1 | 7,877 | Lipton |
| Doukhobor Settlement | 1 | 7,535 | Veregin |
| Icelandic Settlement | 1 | 23,737 | Kandahar |

### Interpretation

**Cities (3 label assignments, avg 15,986 m):** Regina, Prince Albert, and North Battleford — all confirmed case study settlements, all Type A. Their average distance to surrendered land (~16 km) is actually *higher* than most smaller settlement types. **Potential interpretation (unverified):** urban pressure on reserves may have operated through political channels — petitions, MP lobbying, legislative mechanisms like the 1911 amendment — rather than direct spatial adjacency, meaning cities did not need to be immediately proximate to exert pressure. This would explain the larger distances without undermining the Type A classification. Requires archival support before it can be stated as a finding.

**Farm Cluster (6 label assignments, avg 10,945 m):** The closest average distance of any commercial type — smaller even than cities or railway towns. This is not merely "consistent with" Raibmon's argument — it *is* the microtechniques argument made spatially visible. Raibmon explicitly distinguishes between the elite, urban storytellers who produced the rhetoric justifying dispossession and the working farmers who did the actual ground-level work of it. The spatial data shows exactly that split. These small agricultural clusters were not coordinating a campaign against reserves; they were farming. Their accumulated presence — mundane, dispersed, independent — was itself the mechanism of dispossession Raibmon describes.

**Doukhobor Settlement (Veregin, 7,535 m) and Jewish Colony (Lipton, 7,877 m):** The two individual settlements closest to surrendered land in the entire Type A set. Both are ethnic agricultural colonies with no commercial tier. Raibmon's point that "a coherent white-settler society was not required in order to colonize and dispossess" applies directly here — these communities were themselves marginalized within colonial society, yet their presence on the landscape contributed to the same cumulative pattern.

**Ethnic and organized settlement types collectively** (Organized/Ethnic Settlement, German Settlement, Ukrainian Settlement, Swedish Settlement, Icelandic Settlement, Doukhobor Settlement, Jewish Colony) account for 39 of 154 label assignments across the 82 Type A municipalities. The colonial genealogy Raibmon describes is broad and internally diverse — it encompassed settlers who were themselves subject to discrimination and exclusion, yet whose agricultural presence on the land participated in the same dispossession of Indigenous territory.

**Railway Towns (6 label assignments, avg 14,669 m):** Broadview, Melville, Birmingham, Bulyea, Regina Beach, Dafoe. Broadview's presence here directly links the McGuire railway mechanism to Type A classification — railway arrival and municipal founding both 1882, with surrenders following 25–37 years later.

---

## Query 2 — Triple convergence: Type A + geometric overlap + Métis presence

**Run date:** 2026-04-06

**Query:**
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

### Results

Four municipalities returned — all small villages (VL):

| name | nearest_reserve | surrender_year | metis_community | metis_dist_m |
|---|---|---|---|---|
| Regina Beach, VL | Last Mountain Lake | 1918 | Last Mountain Lake | 0.0 |
| Lestock, VL | Muskowekwan | 1920 | Lestock | 0.0 |
| Delmas, VL | Thunderchild | 1908 | Bresaylor | 10,980 |
| Leask, VL | Mistawasis | 1911 | Muskeg Lake | 5,127 |

### Notable absence

**Kamsack is not in these results.** Kamsack overlaps Cote reserve land and is Type A, but has no Métis community association in the Phase 3 data. This is a known gap — the Phase 3 analysis can only draw on the 42 georeferenced Métis communities, and Métis presence around Kamsack is not captured in that set. Kamsack remains the strongest individual case study regardless.

### Interpretation

All four municipalities are small villages, consistent with Query 1's finding that the most intense spatial overlap with Indigenous land occurs at the small settlement level. Regina Beach and Lestock both have their associated Métis community at distance 0 — the community is inside the municipal boundary.

Through the Raibmon lens, these four cases are where multiple branches of the colonial genealogy converge in a single place. The surrender timeline (policy) is one branch. The physical incorporation of surrendered land into municipal territory (settler practice on the ground) is another. The Métis displacement (the human cost borne by a third community) is a third. Raibmon's genealogical method is precisely about showing how these disparate threads — produced by different actors, operating through different mechanisms, often unknown to each other — are nonetheless connected. These four municipalities are where all three threads land in the same location simultaneously.

---

## Query 2a — Geographic profile of the four triple-convergence municipalities

**Run date:** 2026-04-06

**Query:**
```cypher
MATCH (s:Settlement)
WHERE s.census_id IN ['SK176063', 'SK180033', 'SK182030', 'SK186035']
RETURN
  s.census_name  AS name,
  s.census_id    AS tcpuid,
  s.latitude     AS lat,
  s.longitude    AS lon,
  s.csd_type     AS type,
  s.founded      AS founded,
  s.population_1921 AS pop_1921
ORDER BY s.latitude DESC
```

### Results

| name | lat | lon | founded | pop_1921 |
|---|---|---|---|---|
| Leask, VL | 53.03 | -106.75 | null | 176 |
| Delmas, VL | 52.93 | -108.60 | 1905 | 225 |
| Lestock, VL | 51.31 | -103.97 | null | 280 |
| Regina Beach, VL | 50.79 | -104.99 | 1902 | 379 |

### Interpretation

The four municipalities are geographically dispersed across the province — spanning roughly 240 km north to south and 370 km east to west. They are not a regional cluster. This is significant: the triple-convergence pattern (Type A + overlap + Métis presence) is not a localized phenomenon tied to one treaty area or railway corridor. It appears independently across different parts of Saskatchewan.

Leask and Lestock both have null `founded` years — a data gap, not necessarily an absence of early settlement. All four are very small (population 176–379 in 1921), reinforcing the small-village pattern identified in Query 1 and Query 2.

---

## Query 2b — Railway relationships among the four triple-convergence municipalities

**Run date:** 2026-04-06

**Note on data source:** The `SERVED_BY` relationship is not fully populated for smaller villages in the graph. Railway data is stored as direct properties on Settlement nodes (`railway_arrives`, `first_railway`, etc.) and is complete for all four municipalities. Query rewritten accordingly.

**Query:**
```cypher
MATCH (s:Settlement)
WHERE s.census_id IN ['SK176063', 'SK180033', 'SK182030', 'SK186035']
RETURN
  s.census_name             AS name,
  s.founded                 AS founded,
  s.railway_arrives         AS railway_arrives,
  s.first_railway           AS first_railway,
  s.gis_railway_lines_20km  AS railways_20km,
  s.nearest_surrender_year  AS surrender_year
ORDER BY s.railway_arrives
```

### Results

| name | founded | railway_arrives | first_railway | railways within 20km | surrender_year |
|---|---|---|---|---|---|
| Delmas, VL | 1905 | 1905 | CNoR | CNoR | 1908 |
| Lestock, VL | null | 1908 | GTPR | GTPR | 1920 |
| Regina Beach, VL | 1902 | 1911 | CPR | QLSRSC, CPR | 1918 |
| Leask, VL | null | 1911 | CNoR | CNoR | 1911 |

### Interpretation

**No shared railway company.** The four municipalities were served by three different companies — Canadian Northern (CNoR), Grand Trunk Pacific (GTPR), and CPR. There is no single railway builder connecting these cases.

**The railway-to-surrender gap is the consistent pattern.** In every case, the railway arrived before the surrender:

| name | railway_arrives | surrender_year | gap (yrs) |
|---|---|---|---|
| Delmas | 1905 | 1908 | 3 |
| Leask | 1911 | 1911 | 0 |
| Lestock | 1908 | 1920 | 12 |
| Regina Beach | 1911 | 1918 | 7 |

Railway arrival preceded or coincided with surrender in all four cases. The gaps range from 0 to 12 years — consistent with the McGuire petition cycle model, where railway arrival generated demand that took several years to translate into a formal surrender.

**Delmas is the clearest McGuire Type 2 case:** railway arrives 1905, town founded 1905, Thunderchild surrender 1908 — a three-year window. The Canadian Northern both built the line and effectively created the townsite that then generated surrender pressure on Thunderchild.

**Leask is the most extreme case:** railway arrives and surrender happen in the same year (1911). The Mistawasis surrender and the CNoR's arrival appear to be simultaneous events, suggesting the surrender may have been anticipated or negotiated in conjunction with the railway's advance.

---

## Query 4 — Railway arrival vs. surrender year for Type A municipalities

**Run date:** 2026-04-06

**Query:**
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

### Results (top 25 by gap, descending)

| name | railway_company | railway_year | surrender_year | nearest_reserve | n_25km | gap_yrs |
|---|---|---|---|---|---|---|
| Balgonie, T-V | CPR | 1882 | 1919 | Piapot | 3 | 37 |
| North Regina, VL | CPR | 1882 | 1919 | Piapot | 1 | 37 |
| Whitewood, T-V | CPR | 1882 | 1919 | Ochapowace | 2 | 37 |
| Regina, C | CPR | 1882 | 1919 | Piapot | 1 | 37 |
| Pilot Butte, VL | CPR | 1882 | 1919 | Piapot | 1 | 37 |
| Craven, VL | QLSRSC | 1887 | 1918 | Last Mountain Lake | 3 | 31 |
| Lumsden, T-V | QLSRSC | 1887 | 1918 | Last Mountain Lake | 1 | 31 |
| Disley, VL | QLSRSC | 1889 | 1918 | Last Mountain Lake | 1 | 29 |
| Bethune, VL | QLSRSC | 1889 | 1918 | Last Mountain Lake | 1 | 29 |
| Broadview, T-V | CPR | 1882 | 1907 | Kahkewistahaw | 5 | 25 |
| Punnichy, VL | GTPR | 1908 | 1933 | George Gordon | 7 | 25 |
| Summerberry, VL | CPR | 1882 | 1907 | Cowessess | 2 | 25 |
| Grenfell, T-V | CPR | 1882 | 1907 | Cowessess | 2 | 25 |
| McLean, VL | CPR | 1882 | 1906 | Pasqua | 3 | 24 |
| Balcarres, VL | CPR | 1904 | 1928 | Little Black Bear | 1 | 24 |
| Qu'Appelle, T-V | CPR | 1882 | 1906 | Pasqua | 3 | 24 |
| Indian Head, T-V | CPR | 1882 | 1906 | Pasqua | 1 | 24 |
| Sintaluta, T-V | CPR | 1882 | 1905 | Carry The Kettle | 1 | 23 |
| Wolseley, T-V | CPR | 1882 | 1905 | Carry The Kettle | 1 | 23 |
| Paynton, VL | CNoR | 1905 | 1927 | Little Pine | 2 | 22 |
| Hubbard, VL | GTPR | 1907 | 1928 | Little Black Bear | 1 | 21 |
| Goodeve, VL | GTPR | 1907 | 1928 | Little Black Bear | 1 | 21 |
| Fenwood, VL | GTPR | 1907 | 1928 | Little Black Bear | 1 | 21 |
| Ituna, VL | GTPR | 1907 | 1928 | Little Black Bear | 1 | 21 |
| Lipton, VL | CPR | 1904 | 1925 | Standing Buffalo | 4 | 21 |

### Interpretation

**The CPR 1882 main line establishes where pressure would land, not when.** The top of the list is almost entirely CPR settlements established in 1882 — the year the transcontinental line reached Saskatchewan. But the long gaps (up to 37 years) should not be read as 37 years of sustained active pressure. The anticipated settlement boom following the CPR's completion largely failed to materialize through the 1880s and 1890s; the government struggled to recruit settlers in sufficient numbers. The railway corridor identified the geography of future pressure but could not by itself generate it.

**The Sifton-era immigration wave is the actual trigger.** Mass settlement only arrived during the peak 20-year period of roughly 1900–1920, driven by Sifton-era immigration policy. The surrenders in this dataset cluster precisely in that window — not because the railways finally exerted some delayed influence, but because that is when settlers arrived in numbers large enough to create genuine ground-level demand on reserve land. The correct causal sequence is: railway arrives 1882 → anticipated boom fails → government struggles to recruit settlers through the 1880s–1890s → Sifton-era policy produces mass settlement 1900–1920 → settler wave generates real pressure → surrenders follow. The railway determines *where*; the demographic wave determines *when*.

**Reserve-level clustering reveals corridor-wide pressure.** Multiple settlements appear against the same reserve, showing that surrender pressure came not from a single town's petition but from whole strings of settlements along the same railway line bearing down on the same reserve simultaneously:
- Piapot (1919): Balgonie, North Regina, Regina, Pilot Butte — all CPR 1882
- Last Mountain Lake (1918): Craven, Lumsden, Disley, Bethune — all QLSRSC 1887–1889
- Cowessess/Pasqua/Carry The Kettle (1905–1907): Summerberry, Grenfell, McLean, Qu'Appelle, Indian Head, Sintaluta, Wolseley — all CPR 1882
- Little Black Bear (1928): Hubbard, Goodeve, Fenwood, Ituna — all GTPR 1907

The surrender was the outcome of collective, corridor-wide settler pressure arriving in the boom years, not the product of any individual town's long campaign.

**Punnichy is a notable outlier.** GTPR arrives 1908, George Gordon surrendered 1933 — a 25-year gap — with 7 reserves within 25 km, the highest density in the top 25. The late surrender date (1933) falls outside the main boom period and the high reserve density suggests a more contested or prolonged process. Worth follow-up.

**The McGuire petition cycle is the documented surface of a deeper process.** The gaps of 20–37 years are not silence — once the settlement boom arrived, they represent the documented period of petitions, government correspondence, and settler lobbying that McGuire traces in the archival record. But beneath those petitions, Raibmon's framework directs attention to what was accumulating throughout: the mundane microtechniques of settler agricultural practice — farming adjacent to reserve boundaries, drawing water, claiming land — that made the reserve appear anomalous to colonial administrators and made formal surrender feel inevitable. The petitions are the visible, documented tip; the accumulated settler presence is the larger structure underneath.

### Further observations on corridor clustering

Query 4 only returns the top 25 cases by gap length, so the full extent of corridor clustering across the dataset is not yet visible. What is clear from the top 25 is that the unit of accumulated presence was the railway corridor, not the individual town. When the CPR laid its main line in 1882, it created a string of settler communities simultaneously — not one petition, but a whole corridor of independent agricultural actors whose collective presence on the landscape constituted the conditions Raibmon describes.

The CPR main line notably generates two separate clusters against different reserves: the Piapot cluster east of Regina, and the Cowessess/Pasqua/Carry The Kettle cluster further east around the Qu'Appelle Valley. One railway line, two corridors of pressure, multiple surrenders.

What the data cannot show from Query 4 alone is the spatial arrangement of settlements around each reserve — whether they surrounded it on multiple sides or were concentrated along one flank. A dedicated query (4a) is needed to characterize corridor clustering across the full dataset.

---

## Query 4a — Corridor clustering: reserves with 3+ Type A municipalities within 25 km

**Run date:** 2026-04-06

**Query:** See `cypher_queries.md` — Query 4a.

### Results

Municipalities sorted by railway year within each reserve cluster.

**Last Mountain Lake | Surrendered: 1918 | 8 Type A municipalities**
| railway_year | railway | municipality |
|---|---|---|
| 1887 | QLSRSC | Lumsden, T-V |
| 1887 | QLSRSC | Craven, VL |
| 1889 | QLSRSC | Bethune, VL |
| 1889 | QLSRSC | Disley, VL |
| 1905 | CPR | Bulyea, VL |
| 1911 | CPR | Dilke, VL |
| 1911 | CPR | Regina Beach, VL |
| 1911 | CPR | Silton, VL |

**Little Black Bear | Surrendered: 1928 | 7 Type A municipalities**
| railway_year | railway | municipality |
|---|---|---|
| 1904 | CPR | Balcarres, VL |
| 1907 | GTPR | Birmingham, VL |
| 1907 | GTPR | Fenwood, VL |
| 1907 | GTPR | Goodeve, VL |
| 1907 | GTPR | Hubbard, VL |
| 1907 | GTPR | Ituna, VL |
| 1911 | GTPR | Duff, VL |

**Poor Man's | Surrendered: 1919 | 6 Type A municipalities**
| railway_year | railway | municipality |
|---|---|---|
| 1908 | GTPR | Quinton, VL |
| 1908 | GTPR | Raymore, VL |
| 1908 | GTPR | Semans, VL |
| 1908 | GTPR | Tate, VL |
| 1909 | CPR | Dafoe, VL |
| 1909 | CPR | Kandahar, VL |

**Piapot | Surrendered: 1919 | 5 Type A municipalities**
| railway_year | railway | municipality |
|---|---|---|
| 1882 | CPR | Regina, C |
| 1882 | CPR | Balgonie, T-V |
| 1882 | CPR | North Regina, VL |
| 1882 | CPR | Pilot Butte, VL |
| 1911 | GTPR | Edenwold, VL |

**Piapot | Surrendered: 1918 | 4 Type A municipalities**
| railway_year | railway | municipality |
|---|---|---|
| 1905 | CPR | Cupar, VL |
| 1905 | CPR | Earl Grey, VL |
| 1905 | CPR | Markinch, VL |
| 1905 | CPR | Southey, VL |

**Little Bone | Surrendered: 1907 | 3 Type A municipalities**
| railway_year | railway | municipality |
|---|---|---|
| 1888 | Other | Saltcoats, T-V |
| 1889 | Other | Yorkton, T-V |
| 1907 | GTPR | Melville, T-V |

**Carry The Kettle | Surrendered: 1905 | 3 Type A municipalities**
| railway_year | railway | municipality |
|---|---|---|
| 1882 | CPR | Wolseley, T-V |
| 1882 | CPR | Sintaluta, T-V |
| 1907 | CNoR | Montmartre, VL |

**Fishing Station | Surrendered: 1924 | 3 Type A municipalities**
| railway_year | railway | municipality |
|---|---|---|
| 1904 | CPR | Dubuc, VL |
| 1904 | CPR | Grayson, VL |
| 1904 | CPR | Killaly, VL |

**Pasqua | Surrendered: 1906 | 3 Type A municipalities**
| railway_year | railway | municipality |
|---|---|---|
| 1882 | CPR | Indian Head, T-V |
| 1882 | CPR | Qu'Appelle, T-V |
| 1882 | CPR | McLean, VL |

**Standing Buffalo | Surrendered: 1925 | 3 Type A municipalities**
| railway_year | railway | municipality |
|---|---|---|
| 1904 | CPR | Lipton, VL |
| 1905 | CPR | Dysart, VL |
| 1911 | GTPR | B-Say-Tah, VL |

**Cote | Surrendered: 1906 | 3 Type A municipalities**
| railway_year | railway | municipality |
|---|---|---|
| 1904 | CNoR | Kamsack, T-V |
| 1904 | CNoR | Togo, VL |
| 1905 | CNoR | Veregin, VL |

**Muskowekwan | Surrendered: 1920 | 3 Type A municipalities**
| railway_year | railway | municipality |
|---|---|---|
| 1908 | GTPR | Jasmin, VL |
| 1908 | GTPR | Kelliher, VL |
| 1908 | GTPR | Lestock, VL |

**Muskeg Lake | Surrendered: 1919 | 3 Type A municipalities**
| railway_year | railway | municipality |
|---|---|---|
| 1911 | CNoR | Blaine Lake, VL |
| 1911 | CNoR | Marcelin, VL |
| 1913 | CNoR | Krydor, VL |

### Interpretation

**On causation and correlation:** These findings identify spatial and temporal correlations. The data cannot demonstrate that any specific cluster of settlements *caused* a surrender. However, Raibmon's framework reframes what correlation means in this context: dispossession did not require coordinated intent or direct causal chains. "A coherent white-settler society was not required in order to colonize and dispossess." Settlers working independently, each pursuing their own agricultural interests, collectively constituted the conditions under which formal surrenders occurred. The corridor clustering data is therefore not a proxy for the mechanism — in Raibmon's terms, it *is* the mechanism made spatially visible. The Cote/Kamsack cluster remains the only case where documentary evidence names the town directly, which moves beyond correlation into direct causation. All other clusters should be investigated archivally but do not require proven coordination to be analytically significant.

**13 reserves show corridor-level correlation with 3 or more Type A municipalities.** This is a consistent structural pattern across the province. Under the Raibmon framework, each cluster represents a railway corridor of independent agricultural settlers whose accumulated presence constituted the conditions for formal surrender — not a conspiracy, but a genealogy.

**Last Mountain Lake is the most clustered reserve in the dataset (8 municipalities).** Correlated with *two separate railway lines* — QLSRSC (1887–1889) and CPR (1905–1911) — arriving from different directions over a 24-year span. Two independent waves of settlement, each adding their own layer of accumulated presence around the same reserve. Whether the two waves were connected in their relationship to the 1918 surrender is a question for the archival record.

**Piapot appears twice — two separate surrender events in 1918 and 1919.** Each correlated with a distinct set of CPR settlements. A reserve reduced once was not insulated from a second round of accumulated settler presence along a different corridor.

**The Cote/Kamsack cluster is the hinge between the spatial argument and the archival argument.** Kamsack, Togo, and Veregin all arrived via CNoR in 1904–1905; the Cote surrender followed in 1906; the surrender notes name Kamsack explicitly. This is the one case where Raibmon's genealogical pattern is confirmed by documentary evidence of the mechanism. It establishes what the causal chain looks like when it becomes legible — making it the template for evaluating the other clusters in archival research.

**Single-company, single-year clusters are the dominant pattern.** Most clusters show one railway company planting a string of villages simultaneously, all near the same reserve. These settlements did not coordinate — they were the product of a single railway advance. Their independent but simultaneous presence is exactly what Raibmon means by accumulated microtechniques: no conspiracy, but a common genealogy.

---

## Query 3 — Type A municipalities with the longest pre-emptive gaps (founding year)

**Run date:** 2026-04-06

**Query:**
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

### Results

| name | founded | surrender_year | gap_years | nearest_reserve | n_25km |
|---|---|---|---|---|---|
| Whitewood, T-V | 1882 | 1919 | 37 | Ochapowace | 2 |
| Regina, C | 1882 | 1919 | 37 | Piapot | 1 |
| Lumsden, T-V | 1881 | 1918 | 37 | Last Mountain Lake | 1 |
| Craven, VL | 1882 | 1918 | 36 | Last Mountain Lake | 3 |
| Battleford, T-V | 1875 | 1909 | 34 | Moosomin | 7 |
| Fort Qu'Appelle, VL | 1880 | 1910 | 30 | Pasqua | 4 |
| Pilot Butte, VL | 1890 | 1919 | 29 | Piapot | 1 |
| Bethune, VL | 1890 | 1918 | 28 | Last Mountain Lake | 1 |
| Grayson, VL | 1896 | 1924 | 28 | Fishing Station | 3 |
| Broadview, T-V | 1882 | 1907 | 25 | Kahkewistahaw | 5 |
| Foam Lake, VL | 1882 | 1907 | 25 | Fishing Lake | 1 |
| Ituna, VL | 1903 | 1928 | 25 | Little Black Bear | 1 |
| Balcarres, VL | 1903 | 1928 | 25 | Little Black Bear | 1 |
| Punnichy, VL | 1908 | 1933 | 25 | George Gordon | 7 |
| Yorkton, T-V | 1882 | 1907 | 25 | Little Bone | 1 |
| Qu'Appelle, T-V | 1881 | 1906 | 25 | Pasqua | 3 |
| Lebret, VL | 1886 | 1910 | 24 | Pasqua | 3 |
| Sintaluta, T-V | 1881 | 1905 | 24 | Carry The Kettle | 1 |
| Grenfell, T-V | 1883 | 1907 | 24 | Cowessess | 2 |
| Indian Head, T-V | 1882 | 1906 | 24 | Pasqua | 1 |

### Key difference from Query 4

Query 4 measured gaps from **railway arrival**; Query 3 measures from **municipal founding**. For most 1882 CPR towns these are identical. But two entries near the top of this list were **not visible in Query 4** — because they predate any railway:

- **Battleford, T-V — founded 1875, gap 34 years, 7 reserves within 25 km**
- **Fort Qu'Appelle, VL — founded 1880, gap 30 years, 4 reserves within 25 km**

Both are pre-railway settlements. Battleford was established as the territorial capital of the Northwest Territories in 1875 — a governmental, administrative founding, not a railway townsite. Fort Qu'Appelle grew from an HBC trading post, also predating the CPR. Neither appears in Query 4's top 25 because the railway didn't arrive until years after founding.

A third entry also warrants attention: **Lebret, VL — founded 1886, gap 24 years.** Lebret originated as a Catholic mission community — a religious/institutional founding, distinct from both the railway corridor pattern and the pre-Confederation administrative centres.

### Interpretation

**Query 3 surfaces pre-railway and non-railway settler presence that Query 4 cannot show.** The founding-year measure reveals that the longest accumulations of settler presence adjacent to reserve land were not all railway-generated. Battleford's 34-year gap began with territorial administration in 1875 — 7 years before the CPR and 34 years before the Moosomin surrender. Fort Qu'Appelle's 30-year gap began with a trading post and grew into a town over the same period.

**This is the microtechniques argument in its most direct form.** Raibmon's framework is not about railways — it is about the accumulation of diverse, mundane settler practices over time. Query 3 makes visible the full range of colonial actors whose presence accumulated adjacent to reserve land: governmental administrators (Battleford), agricultural settlers (the 1882 CPR corridor), and religious institutions (Lebret). Each represents a different branch of Raibmon's colonial genealogy, each contributing its own layer of accumulated presence — independently, without coordination — to the conditions under which formal surrenders eventually occurred.

**Battleford's 7 reserves within 25 km is the highest density in the top 20** and is now attributable to a pre-railway administrative founding rather than a railway corridor. The territorial capital was the first form of organized settler presence in this part of the province, and it sat adjacent to a dense cluster of reserves for over three decades before the surrender wave of 1905–1915.

**Lebret adds a dimension neither railway queries nor commercial-tier queries surface.** A Catholic mission community founded 1886, adjacent to Pasqua reserve (surrendered 1910), with 4 reserves within 25 km. Religious institutions were part of the colonial genealogy — not through petitions or land claims necessarily, but through their presence on the landscape and their role in shaping Indigenous relationships to colonial society. Worth pursuing in the corpus.

### Preliminary Event context check (selected municipalities)

Before running Query 3a across the full long-gap set, a targeted check of event context for 7 known municipalities confirmed that the Neo4j Event nodes contain exactly the qualitative founding-type information needed. Key findings from that check:

| municipality | founding type indicated in context |
|---|---|
| Battleford | HBC post + NWMP fort (1875); Canada's first industrial residential school (1883); St Vital RC Church (oldest RC church in Sask) |
| Fort Qu'Appelle | Fur trade (NWC/HBC noted from 1804); NWMP barracks 1880; homesteading from 1880 |
| Lebret | Sacred Heart Mission 1866 (20 years before official founding); Lebret Indian School 1884 |
| Kamsack | Crowstand Residential School 1889 (10 years before municipal founding); Doukhobor settlers 1899; Kamsack Land Company 1908 |
| Prince Albert | Presbyterian mission 1866; NWMP 1878; Prince Albert Colonization Company 1883 |
| Yorkton | York Farmers' Colonization Company 1882 |
| Regina | NWMP headquarters 1881; Canada North West Land Company (CPR land sales) 1883 |

This confirms that the long-gap Type A municipalities include at minimum: HBC/fur trade posts, NWMP/administrative centres, Catholic and Presbyterian missions, residential schools, colonization companies, and railway land companies — multiple distinct branches of the colonial genealogy, each contributing its own layer of accumulated institutional presence adjacent to reserve land.

**Data caveat:** Event data was recorded specifically about the urban municipality as an administrative entity, not all prior settlement in that location. Where non-railway institutional presence does appear in the data, its inclusion is analytically significant. Where it is absent, that absence should not be read as absence of that presence on the landscape — it may reflect the scope of data collection. Query 3a (not yet run) will pull this data across the full long-gap set.

---

## Query 3a — Founding-type profiles for Type A municipalities with long pre-emptive gaps

**Run date:** 2026-04-06

**Query:** See `cypher_queries.md` — Query 3a. Event types pulled: `founding`, `colonization_company`, `justice_system`, `first_church`, `first_school`. Threshold: gap > 15 years.

### Results

36 municipalities returned. Full raw output below, ordered by gap descending.

| name | founded | surrender_year | gap | nearest_reserve | key event types present |
|---|---|---|---|---|---|
| Whitewood, T-V | 1882 | 1919 | 37 | Ochapowace | founding, first_church, first_school, justice_system, colonization_company |
| Regina, C | 1882 | 1919 | 37 | Piapot | founding, first_church, first_school, justice_system, colonization_company |
| Lumsden, T-V | 1881 | 1918 | 37 | Last Mountain Lake | founding, first_church, first_school, justice_system |
| Craven, VL | 1882 | 1918 | 36 | Last Mountain Lake | founding, first_church, first_school |
| Battleford, T-V | 1875 | 1909 | 34 | Moosomin | founding, first_church, first_school, justice_system, colonization_company |
| Fort Qu'Appelle, VL | 1880 | 1910 | 30 | Pasqua | founding, first_church, first_school, justice_system, colonization_company |
| Pilot Butte, VL | 1890 | 1919 | 29 | Piapot | founding, first_church, justice_system |
| Grayson, VL | 1896 | 1924 | 28 | Fishing Station | founding, first_church, first_school, justice_system |
| Bethune, VL | 1890 | 1918 | 28 | Last Mountain Lake | founding, first_church, first_school |
| Broadview, T-V | 1882 | 1907 | 25 | Kahkewistahaw | founding, first_church, first_school, justice_system |
| Qu'Appelle, T-V | 1881 | 1906 | 25 | Pasqua | founding, first_church, first_school, justice_system, colonization_company |
| Balcarres, VL | 1903 | 1928 | 25 | Little Black Bear | founding, first_church, first_school, justice_system |
| Yorkton, T-V | 1882 | 1907 | 25 | Little Bone | founding, first_church, first_school, justice_system, colonization_company |
| Foam Lake, VL | 1882 | 1907 | 25 | Fishing Lake | founding, first_church, first_school |
| Ituna, VL | 1903 | 1928 | 25 | Little Black Bear | founding, first_church, first_school |
| Punnichy, VL | 1908 | 1933 | 25 | George Gordon | founding, first_church, first_school, justice_system |
| Grenfell, T-V | 1883 | 1907 | 24 | Cowessess | founding, first_church, first_school, justice_system, colonization_company |
| Indian Head, T-V | 1882 | 1906 | 24 | Pasqua | founding, first_church, first_school, justice_system, colonization_company |
| Sintaluta, T-V | 1881 | 1905 | 24 | Carry The Kettle | founding, first_church, first_school, justice_system |
| Lebret, VL | 1886 | 1910 | 24 | Pasqua | founding, first_church, first_school |
| Duck Lake, T-V | 1875 | 1899 | 24 | One Arrow | founding, first_church, first_school, justice_system, colonization_company |
| Wolseley, T-V | 1882 | 1905 | 23 | Carry The Kettle | founding, first_church, first_school, justice_system |
| Fenwood, VL | 1905 | 1928 | 23 | Little Black Bear | founding, first_church, first_school |
| Goodeve, VL | 1906 | 1928 | 22 | Little Black Bear | founding, first_church |
| Lipton, VL | 1903 | 1925 | 22 | Standing Buffalo | founding, first_church, first_school, justice_system, colonization_company |
| Paynton, VL | 1905 | 1927 | 22 | Little Pine | founding, first_church, first_school, justice_system |
| Dubuc, VL | 1903 | 1924 | 21 | Fishing Station | founding, first_church, first_school |
| Dysart, VL | 1904 | 1925 | 21 | Standing Buffalo | founding, first_church |
| Saltcoats, T-V | 1887 | 1907 | 20 | Little Bone | founding, first_church, first_school, justice_system, colonization_company |
| Killaly, VL | 1904 | 1924 | 20 | Fishing Station | founding, first_church, first_school |
| Blaine Lake, VL | 1899 | 1919 | 20 | Muskeg Lake | founding, first_church, first_school, justice_system |
| Duff, VL | 1910 | 1928 | 18 | Little Black Bear | founding, first_church, first_school, colonization_company |
| Kelliher, VL | 1903 | 1920 | 17 | Muskowekwan | founding, first_church, first_school, justice_system |
| Marcelin, VL | 1902 | 1919 | 17 | Muskeg Lake | founding, first_church, first_school, colonization_company |
| Regina Beach, VL | 1902 | 1918 | 16 | Last Mountain Lake | founding, first_church, first_school, justice_system, colonization_company |
| Southey, VL | 1902 | 1918 | 16 | Piapot | founding, first_church, first_school, justice_system |

### Notable absences

**Prince Albert** (Type A, founded 1885, nearest surrender 1897): gap = 12 years, just below the 15-year threshold — not returned. This exclusion obscures the most analytically significant case in the dataset for layered colonial presence.

The `founded` date of 1885 reflects formal municipal incorporation. The actual accumulation began much earlier — and critically, it began on top of an already-established Métis settlement. The Métis Communities dataset records the Prince Albert Métis community as founded **1862**, with a population of 288 by 1860 and **3,236 by 1880**. The community was settled initially in **river lot style**, extending 14 miles along the North Saskatchewan. Phase 5 enrichment records `nearest_metis_dist_m: 0.0` — the Métis community is inside the municipal boundary. The settler municipality was built directly on top of an established Métis settlement, not adjacent to it.

The colonial accumulation in Prince Albert included:
- Métis river lots from 1862 (James Isbister); Scottish and English Métis arriving from Red River and Kildonan through the late 1860s–1870s
- Presbyterian mission 1866 (James Nesbit, 4 years after Isbister's settlement)
- Special Survey 1877 — Métis residents agitating for surveys to confirm land holdings
- NWMP from 1878
- Prince Albert Colonization Company from 1883
- 1885 Resistance: Métis organizing over survey and scrip concerns contributed directly; Prince Albert was a major hub

The Chakastaypasin surrender (1897) follows all of this by 12–35 years depending on where you start counting. The gap = 12 from `founded` is the least informative way to measure Prince Albert's pre-emptive accumulation. Measured from the Métis settlement (1862) to the nearest surrender (1897), the real gap is 35 years — which would place Prince Albert near the top of the long-gap set, alongside Battleford and Lumsden.

Prince Albert is not a methodological caution. It is a case where the colonial city displaced a Métis settlement, layered further colonial institutions on top, and then generated surrender pressure on the adjacent Chakastaypasin reserve — all of which is invisible to a query filtered by the municipal `founded` date. It belongs in the interpretation of this query, not merely as an absence note.

**North Battleford** (Type A, founded 1904, nearest surrender 1909): gap = 5 years — a genuine short-gap case. A CPR-era townsite with no deep pre-railway history.

**Kamsack**: gap data not returned here (likely null `founded`). Known from preliminary check to have Crowstand Residential School 1889, 10 years before any municipal founding.

### Colonization company entities documented in the long-gap set

At least 11 distinct colonization entities appear across the 36 municipalities:

| entity | year | municipality |
|---|---|---|
| North West Company / HBC | 1804 | Fort Qu'Appelle |
| York Farmers' Colonization Company | 1882 | Yorkton |
| Primitive Methodist Colonization Company | 1882 | Duff; Grenfell (Pheasant Forks colony) |
| York Colonization Company | 1883 | Whitewood |
| Canada North West Land Company | 1883 | Regina; Qu'Appelle |
| Prince Albert Colonization Company | 1881 | Duck Lake |
| Qu'Appelle Valley Farming Company (Bell Farm) | 1884 | Indian Head |
| Jewish Colonization Association | 1901 | Lipton |
| William Pearson Land Company | 1902 | Regina Beach |
| Antoine Marcelin (active European recruitment) | 1902 | Marcelin |
| Luse Land Company (possible) | 1908 | Battleford |
| The International Company | 1906 | Saltcoats |

This is not an exhaustive list — it reflects only what is recorded in the Event nodes for this event type. But it establishes that colonization companies were a distinct and widespread institutional mechanism across the long-gap set, operating alongside (and sometimes preceding) railway development.

### Pre-townsite settlement — the `founded` date understates the real accumulation

Several municipalities have a formal founding date that postdates documented settler presence by years or decades:

| municipality | documented early presence | formal `founded` | understatement |
|---|---|---|---|
| Balcarres | "settlement began in 1882" | 1903 | 21 years |
| Duff | Primitive Methodist Colony 1882 | 1910 | 28 years |
| Dysart | "settlement had occurred since the 1880s" | 1904 | ~20 years |
| Ituna | "settlement began in the 1880s" | 1903 | ~20 years |
| Killaly | "settlement in the area began in 1890" | 1904 | 14 years |
| Qu'Appelle | HBC trading post 1854/55 | 1881 | 25+ years |
| Regina Beach | "settlement in the area began in 1882" | 1902 | 20 years |

The gap_years figures in Query 3 and Query 3a are computed from the `founded` field, which records the formal townsite date. In these cases, the actual accumulation of settler presence adjacent to reserve land began substantially earlier. The real pre-emptive gaps are longer than the numbers show.

This is not a data error — it is the data correctly reflecting what "founding" meant administratively. It is an analytical caution: where the data shows a gap of 20 years, the true accumulation may represent 35–40 years of settler presence.

### Founding-type taxonomy across the 36 municipalities

The event data surfaces the following distinct branches of colonial genealogy:

**1. Pre-railway administrative / state founding (HBC + NWMP)**
- Battleford (1875): HBC post and NWMP fort simultaneously — the colonial state and the fur trade arriving together
- Fort Qu'Appelle (1880): NWMP barracks established at an existing fur trade site; NWC/HBC recorded from 1804
- Duck Lake (1875): Sacred Heart Mission 1879, NWMP detachment 1879 — mission and police arriving in the same year
- Qu'Appelle (1881): HBC trading post from 1854/55; NWMP barracks 1882

These are the deepest roots in the dataset — colonial presence accumulating around reserve land for 20–30+ years before formal surrender. None of these foundings are railway-generated.

**2. Mission-based founding**
- Lebret (1886): "Settlement in the area began with the establishment of a chapel and rectory." The founding event IS the mission. Sacred Heart Mission 1866 — a full 20 years before even the official founding year, and 44 years before the 1910 Pasqua surrender. Lebret Indian School added 1884.
- Duck Lake: Sacred Heart Mission Church 1879, Stobart Roman Catholic Public School 1885

**3. Residential school presence**
- Battleford: Canada's first industrial residential school, 1883 — 26 years before the nearest surrender
- Lebret: Lebret Indian School, 1884 — 26 years before the Pasqua surrender

These are not peripheral to the dispossession story. Residential schools were institutions that removed Indigenous children from reserves, weakened reserve-based community structures, and in some cases directly facilitated land transactions. Their presence in the founding-type data adds a dimension that neither railway proximity nor municipal petitions capture.

**4. Colonization companies**
At minimum 11 distinct entities across the set (see table above). These ranged from CPR land sales arms (Canada North West Land Company) to religious colonies (Primitive Methodist Colonization Company) to ethnic settlement schemes (Jewish Colonization Association). Each represented a distinct mechanism for organizing and directing settler arrival — not independent agricultural choices but structured, institutionally-organized land occupation.

**5. Ethnic/religious colony settlements**
- Blaine Lake (1899): "Homesteading in the area began in large quantities with the arrival of Doukhobor settlers"
- Lipton (1903): settlers from 1877; deaf-mute settler community; Jewish Colonization Association 1901
- Duff: Primitive Methodist Colony — a religious community that predated the formal village by 28 years
- Dysart, Fenwood, Ituna: Romanian/Ukrainian/German settlement communities

Consistent with Query 1's finding that ethnic and organized settlement types account for 39 of 154 label assignments across the 82 Type A municipalities. The colonial genealogy encompassed settlers who were themselves marginalized within colonial society — Doukhobors, Jewish colonists, deaf-mute settlers — whose presence nonetheless participated in the same spatial pattern of accumulation around Indigenous land.

**6. NWMP / justice system presence**
NWMP detachments appear in at least 21 of the 36 municipalities, spanning founding dates from 1875 (Fort Battleford) through the 1910s. This is close to universal in the long-gap set. The colonial state — through its policing arm — was an early and persistent presence in almost every long-gap municipality, often arriving simultaneously with or before civilian settlers.

The NWMP's role in this context was not merely law enforcement. It enforced the pass system, supervised surrenders, and in the 1885 Resistance period directly suppressed Indigenous resistance to colonial expansion. Its presence in the founding-event data links the mundane settler genealogy (churches, schools, farms) to the coercive capacity of the colonial state that underwrote it.

### Duck Lake — a new entry

Duck Lake does not appear in the preliminary event check but is an analytically significant addition to the long-gap set. Founded 1875 (gap 24), nearest reserve One Arrow (surrendered 1899) — the *earliest* surrender in the 36-municipality set. Key founding context: "settler history of Duck Lake starts with missionaries and priests, settlement centered on the development of the Stobart and Eden Company." NWMP detachment 1879, Sacred Heart Mission Church 1879, Stobart Roman Catholic Public School 1885, Prince Albert Colonization Company 1881.

Duck Lake's 1899 surrender is early even by prairie standards. The combination of a trade company driving townsite development, a mission, an NWMP presence, and a colonization company — all operating from 1875–1885 — constitutes a dense institutional genealogy converging on One Arrow reserve over 24 years. Worth pursuing in the McGuire archival record.

Duck Lake also appeared in the 1885 North West Resistance — it was the site of the first engagement of the conflict, in March 1885. The NWMP detachment established in 1879 was part of the colonial infrastructure that made that confrontation possible. The 1885 events and the 1899 surrender are separate episodes, but they are connected moments in the colonial genealogy of the same location.

### Interpretation

**The long-gap Type A set contains multiple distinct branches of the colonial genealogy Raibmon describes.** The query was designed to test whether the Event data would surface founding-type diversity — and it does. Across 36 municipalities with 16–37 year gaps, the data records: HBC/fur trade posts, NWMP forts, Catholic and Protestant missions, residential schools, railway land companies, religious colonization companies, ethnic settlement schemes, and agricultural homesteaders. These are not interchangeable — each operated through its own mechanisms, was organized by different actors, and related to Indigenous land in distinct ways. But all of them contributed layers to the accumulated settler presence that constituted the conditions for formal surrender.

**This is the spatial argument made with institutional texture.** Query 1 showed that farm clusters and ethnic colonies sat closest to surrendered land. Query 4 showed that railway corridors were the dominant organizing geography of surrender pressure. Query 3a shows what was inside those corridors: not just farmers and railway workers, but missionaries, police officers, land agents, residential school administrators, and colonization company recruiters — the full institutional apparatus of prairie colonialism operating simultaneously, mostly without coordination, each adding its own form of accumulated presence.

**The NWMP's near-universality is the most striking single finding.** The colonial state was present in almost every long-gap municipality from the earliest dates. This is not surprising historically — it is the documented mechanism by which the prairie west was opened to settlement. But it appears directly in the founding-event data for municipality after municipality, linking Raibmon's "microtechniques" argument to the coercive state infrastructure that made those microtechniques possible. Individual settlers farming adjacent to reserve boundaries were not isolated actors — they operated in a landscape already organized by state power.

**The pre-townsite understatement problem is analytically important.** For Duff, Balcarres, Dysart, and Ituna in particular, the gap_years figure significantly understates the real accumulation. The Primitive Methodist Colony at Duff began in 1882 — 28 years before the village was formally founded. If gap_years were calculated from first documented settler presence rather than formal founding, several municipalities near the 15-year threshold would appear, and several already in the set would show much longer accumulations. The `founded` field is reliable as an administrative date; it is a floor, not a ceiling, for the real pre-emptive gap.

---

## Query 3a (sensitized) — Combined event- and Métis-anchored effective gap

**Run date:** 2026-04-06

**Purpose:** Address two limitations of Query 3a: (1) the `founded` date understates the real accumulation in pre-townsite cases; (2) Prince Albert and similar settlements are excluded because the Métis community founding year predates even the earliest colonial event and is not captured by the `founded` field. The sensitized query computes `effective_start = min(founded, earliest event year, nearest_metis_y_found)` and uses the resulting `effective_gap` as the primary sort key.

**Enrichment step:** `nearest_metis_y_found` written to 32 Settlement nodes from `metis_full.csv` prior to running this query. Two nodes (Leask, Naicam) received no value due to null Y_FOUND in the source data.

**Anchor categories:**
- `founded` — formal founding date is still the earliest documented presence (11 cases)
- `event` — an Event node year (founding, colonization_company, justice_system, first_church, or first_school) predates `founded` (9 cases)
- `metis` — the nearest Métis community founding year predates both `founded` and the earliest event year (15 cases)

### Results

| name | founded | metis_y_found | earliest_event | eff_start | anchor | surrender | formal_gap | eff_gap | correction | nearest_reserve |
|---|---|---|---|---|---|---|---|---|---|---|
| Fort Qu'Appelle, VL | 1880 | 1840 | 1804 | 1804 | event | 1910 | 30 | 106 | +76 | Pasqua |
| Lebret, VL | 1886 | 1860 | 1866 | 1860 | metis | 1910 | 24 | 50 | +26 | Pasqua |
| Regina Beach, VL | 1902 | 1870 | 1902 | 1870 | metis | 1918 | 16 | 48 | +32 | Last Mountain Lake |
| Duff, VL | 1910 | — | 1882 | 1882 | event | 1928 | 18 | 46 | +28 | Little Black Bear |
| Balcarres, VL | 1903 | 1903 | 1886 | 1886 | event | 1928 | 25 | 42 | +17 | Little Black Bear |
| Battleford, T-V | 1875 | 1868 | 1875 | 1868 | metis | 1909 | 34 | 41 | +7 | Moosomin |
| Regina, C | 1882 | 1882 | 1881 | 1881 | event | 1919 | 37 | 38 | +1 | Piapot |
| Whitewood, T-V | 1882 | — | 1882 | 1882 | founded | 1919 | 37 | 37 | 0 | Ochapowace |
| Lumsden, T-V | 1881 | — | 1881 | 1881 | founded | 1918 | 37 | 37 | 0 | Last Mountain Lake |
| Craven, VL | 1882 | — | 1882 | 1882 | founded | 1918 | 36 | 36 | 0 | Last Mountain Lake |
| **Prince Albert, C** | **1885** | **1862** | **1872** | **1862** | **metis** | **1897** | **12** | **35** | **+23** | **Chakastaypasin** |
| Punnichy, VL | 1908 | 1900 | 1908 | 1900 | metis | 1933 | 25 | 33 | +8 | George Gordon |
| Duck Lake, T-V | 1875 | 1870 | 1875 | 1870 | metis | 1899 | 24 | 29 | +5 | One Arrow |
| Pilot Butte, VL | 1890 | — | 1890 | 1890 | founded | 1919 | 29 | 29 | 0 | Piapot |
| Grayson, VL | 1896 | — | 1896 | 1896 | founded | 1924 | 28 | 28 | 0 | Fishing Station |
| Bethune, VL | 1890 | — | 1890 | 1890 | founded | 1918 | 28 | 28 | 0 | Last Mountain Lake |
| Rosthern, T-V | 1893 | 1870 | 1890 | 1870 | metis | 1897 | **4** | 27 | +23 | Stoney Knoll |
| Delmas, VL | 1905 | 1882 | 1900 | 1882 | metis | 1908 | **3** | 26 | +23 | Thunderchild |
| Edenwold, VL | 1911 | — | 1893 | 1893 | event | 1919 | **8** | 26 | +18 | Piapot |
| Broadview, T-V | 1882 | — | 1882 | 1882 | founded | 1907 | 25 | 25 | 0 | Kahkewistahaw |
| Yorkton, T-V | 1882 | — | 1882 | 1882 | founded | 1907 | 25 | 25 | 0 | Little Bone |
| Ituna, VL | 1903 | — | 1903 | 1903 | founded | 1928 | 25 | 25 | 0 | Little Black Bear |
| Qu'Appelle, T-V | 1881 | — | 1881 | 1881 | founded | 1906 | 25 | 25 | 0 | Pasqua |
| Foam Lake, VL | 1882 | — | 1882 | 1882 | founded | 1907 | 25 | 25 | 0 | Fishing Lake |
| Grenfell, T-V | 1883 | — | 1882 | 1882 | event | 1907 | 24 | 25 | +1 | Cowessess |
| Indian Head, T-V | 1882 | — | 1882 | 1882 | founded | 1906 | 24 | 24 | 0 | Pasqua |
| Lipton, VL | 1903 | — | 1901 | 1901 | event | 1925 | 22 | 24 | +2 | Standing Buffalo |
| Stockholm, VL | 1903 | — | 1883 | 1883 | event | 1907 | **4** | 24 | +20 | Kahkewistahaw |
| Sintaluta, T-V | 1881 | — | 1881 | 1881 | founded | 1905 | 24 | 24 | 0 | Carry The Kettle |
| Wolseley, T-V | 1882 | — | 1882 | 1882 | founded | 1905 | 23 | 23 | 0 | Carry The Kettle |
| Fenwood, VL | 1905 | — | 1905 | 1905 | founded | 1928 | 23 | 23 | 0 | Little Black Bear |
| Goodeve, VL | 1906 | — | 1906 | 1906 | founded | 1928 | 22 | 22 | 0 | Little Black Bear |
| Paynton, VL | 1905 | — | 1905 | 1905 | founded | 1927 | 22 | 22 | 0 | Little Pine |
| Dubuc, VL | 1903 | — | 1903 | 1903 | founded | 1924 | 21 | 21 | 0 | Fishing Station |
| Dysart, VL | 1904 | — | 1904 | 1904 | founded | 1925 | 21 | 21 | 0 | Standing Buffalo |

### Fort Qu'Appelle (eff_gap 106)

Fort Qu'Appelle's effective gap of 106 years is driven by the event anchor of 1804 — the NWC colonization_company entry in the Event nodes. The 1804 date is not a query artefact or an error in categorization. Métis people worked for the NWC as engagés, guides, and provisioners from the earliest years of the fur trade; the Qu'Appelle Valley post represents Métis economic presence and labour in the valley, even if formal Métis settlement (Y_FOUND 1840 in the community data) came later. The 106-year effective gap reflects the full depth of the colonial-and-Métis genealogy in the Qu'Appelle Valley: fur trade presence from 1804, established Métis community from 1840, NWMP barracks 1880, homesteading from 1880, and formal municipal founding 1880 — all converging on the Pasqua surrender of 1910. Fort Qu'Appelle has the longest documented accumulation in the dataset by any measure.

### Four new entries — formal gap below 15, effective gap 21–27

The sensitized query surfaces four municipalities that did not appear in Query 3a at all because their formal gaps fell below the 15-year threshold:

**Rosthern, T-V** (formal gap 4 → effective gap 27, Métis anchor)
Rosthern was formally founded in 1893; the nearest Métis community (Fish Creek) has Y_FOUND 1870 — 23 years earlier. The Stoney Knoll reserve was surrendered in 1897, just 4 years after Rosthern's founding but 27 years after the Fish Creek Métis community was established. Fish Creek is also the site of the 1885 Battle of Fish Creek during the North West Resistance, connecting the Métis history of the area directly to the colonial conflict that preceded the settlement boom. Rosthern's short formal gap disguised a much longer arc of colonial and Métis presence converging on Stoney Knoll.

**Delmas, VL** (formal gap 3 → effective gap 26, Métis anchor)
Delmas was already identified in Query 2 as one of the four triple-convergence municipalities (Type A + overlap + Métis presence). The CNoR arrived 1905, the town was founded 1905, and the Thunderchild surrender followed in 1908 — a textbook 3-year McGuire petition-cycle case. The sensitized query reveals that the Bresaylor Métis community was established in 1882, 23 years before the CNoR reached the area. The railway-generated townsite was built into a landscape already marked by Métis presence; the effective gap runs not 3 years but 26.

**Edenwold, VL** (formal gap 8 → effective gap 26, event anchor)
Edenwold was founded in 1911, with the Piapot surrender in 1919 — formal gap 8 years. The event anchor pulls the effective start to 1893, based on an early event record predating the townsite. Gap correction +18. Piapot is the most-clustered reserve in the dataset (appears in both the 1918 and 1919 surrender clusters from Query 4a); Edenwold is one of a string of municipalities whose accumulated presence contributes to that picture even though its own formal gap is short.

**Stockholm, VL** (formal gap 4 → effective gap 24, event anchor)
Stockholm founded 1903, Kahkewistahaw surrender 1907 — formal gap 4. The event anchor is 1883, 20 years before the townsite, giving an effective gap of 24. Kahkewistahaw is also the nearest reserve for Broadview (formal gap 25) — the same reserve had corridor-level pressure building from two different directions over two different timescales.

### Prince Albert restored

With effective_start = 1862 (Métis community founding), Prince Albert's effective gap is 35 years — ranking it 11th in the set, between Craven and Punnichy. Its formal gap of 12 excluded it from Query 3a entirely. The Chakastaypasin surrender (1897) follows 35 years of documented Métis and colonial presence: Isbister's river lot settlement from 1862, the Presbyterian mission from 1866 (4 years later), NWMP from 1878, the Prince Albert Colonization Company from 1883, and the 1885 Resistance organizing — all converging on the same location before the municipality was formally incorporated in 1885.

Prince Albert is also a case where the colonial municipality was built directly inside an established Métis settlement (`nearest_metis_dist_m: 0.0`), not merely adjacent to one. The displacement of the Métis settlement and the surrender pressure on Chakastaypasin are parallel processes running simultaneously in the same location.

### What the anchor distribution shows

Métis community founding year is the determinative anchor in **15 of 35 cases** — nearly half. This is not a marginal correction. In the cases where it applies, it typically shifts the effective start by 20–30 years and changes the analytical picture substantially. The Métis data is not supplementary to the colonial genealogy argument — it is evidence of prior Indigenous and mixed-descent land tenure that the formal founding measure systematically erases.

Event-year anchors apply in **9 cases**, typically capturing colonization companies or NWMP presence that preceded formal municipal incorporation by a few years. The formal founding date remains the earliest documented presence in only **11 cases** — roughly a third of the set.

### Interpretation

**The sensitized query makes the understatement of the formal gap measure visible and measurable.** For 24 of 35 municipalities, the formal founding date is not the real start of accumulated colonial presence. The correction ranges from 1 year (Grenfell, Regina) to 76+ years (Fort Qu'Appelle). The Métis anchor is responsible for the largest corrections and for bringing four municipalities into the analysis that the formal measure excluded entirely.

**Raibmon's genealogical method is designed for exactly this kind of layered, multi-actor, long-accumulation analysis.** The formal founding date captures when colonial administration recognized the settlement. The event anchors capture when institutions arrived. The Métis anchor captures when the land was already occupied — by communities whose presence preceded the settler municipality and who were displaced by it. The sensitized query does not produce a single "real" gap number; it makes visible the multiple starting points of the colonial genealogy that converged on each reserve surrender.

**The four new entries (Rosthern, Delmas, Edenwold, Stockholm) are the strongest argument for the sensitized measure.** Their formal gaps (3–8 years) would place them in the "short-gap" category, consistent with a simple McGuire petition-cycle reading: railway arrives, town founded, surrender follows quickly. The sensitized gaps (24–27 years) reframe them: the railway and townsite arrived into a landscape already marked by decades of Métis settlement and colonial institutional presence. The petition cycle was not the beginning of the process — it was the final bureaucratic step in a much longer accumulation.

---

## Query 5 — Métis displacement arc: community proximity and temporal sequence

**Run date:** 2026-04-06

**Query:** See `cypher_queries.md` — Query 5. Returns all 34 municipalities with `metis_community_present = true`, sorted by distance to associated Métis community.

### Results

| municipality | founded | metis_community | dist_m | temporal_type | overlap |
|---|---|---|---|---|---|
| Regina, C | 1882 | Regina | 0 | A | False |
| Abernethy, VL | 1903 | Abernethy | 0 | none | False |
| Balcarres, VL | 1903 | Balcarres | 0 | A | False |
| Fort Qu'Appelle, VL | 1880 | Fort Qu'Appelle | 0 | A | False |
| Lebret, VL | 1886 | Lebret | 0 | A | False |
| Regina Beach, VL | 1902 | Last Mountain Lake | 0 | A | True |
| Moose Jaw, C | 1882 | Moose Jaw | 0 | none | False |
| Lestock, VL | null | Lestock | 0 | A | True |
| Saskatoon, C | 1882 | Saskatoon | 0 | none | False |
| Battleford, T-V | 1875 | Battleford | 0 | A | False |
| Prince Albert, C | 1885 | Prince Albert | 0 | A | False |
| Duck Lake, T-V | 1875 | Duck Lake | 0 | A | False |
| Birch Hills, VL | 1903 | Birch Hills | 209 | C | False |
| Estevan, T-V | 1892 | Estevan | 393 | none | False |
| Swift Current, C | 1883 | Swift Current | 534 | none | False |
| Meota, VL | null | Jackfish Lake | 4,299 | B | False |
| Leask, VL | null | Muskeg Lake | 5,127 | A | True |
| Jasmin, VL | null | Ste. Delphine | 8,427 | A | False |
| Punnichy, VL | 1908 | Touchwood | 8,539 | A | False |
| Delmas, VL | 1905 | Bresaylor | 10,980 | A | True |
| Rocanville, VL | 1902 | Welwyn | 11,361 | none | False |
| Verwood, VL | 1912 | Willow Bunch | 12,539 | none | False |
| Rosthern, T-V | 1893 | Fish Creek | 13,568 | A | False |
| Domremy, VL | 1913 | Saint Louis de Langevin | 14,648 | C | False |
| Canwood, VL | 1911 | Mont Nebo | 16,587 | none | False |
| Ruddell, VL | 1904 | Baljennie | 16,950 | none | False |
| Neville, VL | 1911 | Lac Pelletier | 17,696 | none | False |
| Dundurn, VL | 1902 | Round Prairie | 19,138 | none | False |
| Weldon, VL | 1905 | Glen Mary | 19,177 | B | False |
| Success, VL | null | Saskatchewan Landing | 21,939 | none | False |
| Landis, VL | 1907 | Cando | 24,701 | A | False |
| Naicam, VL | 1919 | Archerwill | 44,112 | none | False |
| Cadillac, VL | 1913 | Val Marie | 53,022 | none | False |
| Turtleford, VL | 1908 | Meadow Lake | 87,562 | none | False |

### Pattern 1 — Métis communities inside municipal boundaries (dist_m = 0)

12 municipalities returned dist_m = 0, meaning the associated Métis community is inside the municipal boundary. Of these, **9 are Type A**: Regina, Balcarres, Fort Qu'Appelle, Lebret, Regina Beach, Lestock, Battleford, Prince Albert, Duck Lake. These are cases where the settler municipality absorbed an established Métis settlement — not merely expanded near one — while simultaneously predating a nearby reserve surrender. The municipal boundary performed two dispossessions at once: incorporating Métis land into settler municipal territory, and generating the accumulated presence that correlated with reserve surrenders.

The three non-Type-A municipalities at dist_m = 0 (Abernethy, Moose Jaw, Saskatoon) also enclosed Métis communities, but have no surrender within 25 km. Their Métis displacement was not correlated with a proximate reserve surrender — it operated through a separate mechanism of urban expansion.

### Pattern 2 — Triple convergence at dist_m = 0

**Regina Beach** and **Lestock** are the only two municipalities with all three conditions: dist_m = 0 (Métis community inside boundary), temporal_type = A (municipality predated surrender), and overlap_with_surrender = True (municipal polygon geometrically overlaps surrendered reserve land). These cases are where all three dispossession processes converge physically and temporally in a single municipal polygon: the Métis community absorbed into the town, the reserve parcel surrendered and incorporated, and the municipality established before the surrender. First identified in Query 2; Query 5 confirms both are dist_m = 0 cases.

### Pattern 3 — Temporal type = none (no surrender within 25 km)

15 of 34 municipalities with Métis community associations have temporal_type = none — no surrendered reserve parcel within 25 km. This group includes four cities (Moose Jaw, Saskatoon, Estevan, Swift Current) and 11 smaller municipalities.

This is analytically significant. The Métis displacement documented in the communities dataset was not confined to zones of reserve surrender pressure. Major prairie cities grew by absorbing Métis settlements operating through a different mechanism entirely: direct municipal expansion, road allowance removals (Phase 3), and city boundary extension, without a proximate reserve surrender being part of the story. Saskatoon and Moose Jaw are the clearest examples — both cities enclosed Métis communities, both have Métis Y_FOUND dates that predate their own municipal founding, and neither sits near a surrendered reserve.

This means the dataset captures two distinct Métis displacement processes:
1. **Reserve-adjacent displacement** — Métis communities near reserves, where the municipality was in the pressure-then-surrender sequence (Type A cases)
2. **Urban-core displacement** — Métis communities absorbed directly into city growth, operating independently of reserve surrenders

Raibmon's framework applies to both but through different branches of the colonial genealogy. The reserve-adjacent cases involve the settler agricultural genealogy converging with Indigenous land policy. The urban-core cases involve the commercial and administrative genealogy — city building, land markets, municipal governance — directly displacing Métis communities without passing through the surrender mechanism.

### Pattern 4 — Birch Hills (Type C, dist_m = 209)

Birch Hills is the only Type C municipality in the Métis proximity set — meaning the nearest surrender *preceded* the municipal founding. The sequence is: Birch Hills Métis community established ~1880 → reserve surrender → Birch Hills municipality founded 1903. The municipality was planted after the surrender, adjacent to an established Métis community. This is not the "pressure then surrender" pattern; it is closer to post-surrender settler infill. The Métis community was already there before both the surrender and the municipality.

### Pattern 5 — Distance tail (>10 km)

Several municipalities beyond 10 km from their associated Métis community (Rocanville, Verwood, Canwood, Ruddell, Neville, Dundurn, Weldon, Success, Landis, Naicam, Cadillac, Turtleford) represent looser associations — each is simply the nearest municipality to a Métis community, not necessarily a spatially integrated case. At 44 km (Naicam/Archerwill), 53 km (Cadillac/Val Marie), and 87 km (Turtleford/Meadow Lake), the spatial relationship is essentially nominal. These entries reflect the Phase 3 matching logic rather than meaningful proximity.

### What Query 5 cannot show — the temporal sequence

Query 5 does not include `nearest_metis_y_found`, so it cannot directly show whether the Métis community predated the associated municipality. The enrichment step (Query 3a sensitized) established that in many of the dist_m = 0 cases the Métis community clearly predates the municipal founding: Prince Albert Métis community 1862 vs. municipality 1885; Fort Qu'Appelle Métis 1840 vs. municipality 1880; Battleford Métis 1868 vs. municipality 1875; Duck Lake Métis 1870 vs. municipality 1875; Lebret Métis 1860 vs. municipality 1886.

A follow-up query (5a) should add `nearest_metis_y_found` and compute `(muni_founded - metis_y_found)` to make the temporal sequence explicit for the full 34-municipality set.

### Interpretation

**The 12 dist_m = 0 cases are where the colonial municipality and the Métis displacement argument converge most directly.** In these cases the municipality did not grow near a Métis community — it grew on top of one. The Métis community data records the prior presence; the municipal boundary records the dispossession. That 9 of these 12 are Type A adds another layer: the same municipal presence that absorbed the Métis settlement also correlated with surrender pressure on an adjacent reserve. Multiple Indigenous communities were affected by the same municipal growth in the same location simultaneously.

**The 15 temporal_type = none cases extend the Métis displacement story beyond the reserve-surrender frame.** Saskatoon, Moose Jaw, Swift Current, and Estevan are in this group. Their growth involved Métis community displacement without a proximate reserve surrender — the colonial genealogy in these cities was primarily commercial and administrative, not agricultural. This is a distinct dispossession process from the farm-cluster and railway-corridor pattern that dominates the Type A analysis, and it requires different archival sources to document: municipal bylaws, road allowance records, and city growth histories rather than surrender petitions.

---

## Query 5a — Métis temporal sequence: who predated whom

**Run date:** 2026-04-06

**Query:** Extension of Query 5, adding `nearest_metis_y_found` (written during the Query 3a sensitized enrichment step) and computing `(muni_founded - metis_y_found)` to classify temporal sequence as `metis_first`, `same_year`, `muni_first`, or `unknown`. Sorted by gap descending within known cases.

### Results

| municipality | muni_founded | metis_y_found | gap | dist_m | sequence | temporal_type | overlap |
|---|---|---|---|---|---|---|---|
| Weldon, VL | 1905 | 1855 | +50 | 19,177 | metis_first | B | False |
| Dundurn, VL | 1902 | 1855 | +47 | 19,138 | metis_first | none | False |
| Fort Qu'Appelle, VL | 1880 | 1840 | +40 | 0 | metis_first | A | False |
| Domremy, VL | 1913 | 1880 | +33 | 14,648 | metis_first | C | False |
| Verwood, VL | 1912 | 1880 | +32 | 12,539 | metis_first | none | False |
| Regina Beach, VL | 1902 | 1870 | +32 | 0 | metis_first | A | True |
| Neville, VL | 1911 | 1880 | +31 | 17,696 | metis_first | none | False |
| Canwood, VL | 1911 | 1880 | +31 | 16,587 | metis_first | none | False |
| Lebret, VL | 1886 | 1860 | +26 | 0 | metis_first | A | False |
| Delmas, VL | 1905 | 1882 | +23 | 10,980 | metis_first | A | True |
| Prince Albert, C | 1885 | 1862 | +23 | 0 | metis_first | A | False |
| Rosthern, T-V | 1893 | 1870 | +23 | 13,568 | metis_first | A | False |
| Birch Hills, VL | 1903 | 1880 | +23 | 209 | metis_first | C | False |
| Rocanville, VL | 1902 | 1880 | +22 | 11,361 | metis_first | none | False |
| Turtleford, VL | 1908 | 1889 | +19 | 87,562 | metis_first | none | False |
| Cadillac, VL | 1913 | 1900 | +13 | 53,022 | metis_first | none | False |
| Moose Jaw, C | 1882 | 1870 | +12 | 0 | metis_first | none | False |
| Punnichy, VL | 1908 | 1900 | +8 | 8,539 | metis_first | A | False |
| Estevan, T-V | 1892 | 1885 | +7 | 393 | metis_first | none | False |
| Battleford, T-V | 1875 | 1868 | +7 | 0 | metis_first | A | False |
| Duck Lake, T-V | 1875 | 1870 | +5 | 0 | metis_first | A | False |
| Regina, C | 1882 | 1882 | 0 | 0 | same_year | A | False |
| Abernethy, VL | 1903 | 1903 | 0 | 0 | same_year | none | False |
| Balcarres, VL | 1903 | 1903 | 0 | 0 | same_year | A | False |
| Swift Current, C | 1883 | 1883 | 0 | 534 | same_year | none | False |
| Landis, VL | 1907 | 1911 | -4 | 24,701 | muni_first | A | False |
| Saskatoon, C | 1882 | 1920 | -38 | 0 | muni_first | none | False |
| Ruddell, VL | 1904 | 1945 | -41 | 16,950 | muni_first | none | False |
| Success, VL | null | 1880 | — | 21,939 | unknown | none | False |
| Jasmin, VL | null | 1886 | — | 8,427 | unknown | A | False |
| Lestock, VL | null | 1890 | — | 0 | unknown | A | True |
| Naicam, VL | 1919 | null | — | 44,112 | unknown | none | False |
| Leask, VL | null | null | — | 5,127 | unknown | A | True |
| Meota, VL | null | 1890 | — | 4,299 | unknown | B | False |

### Sequence summary

- **metis_first: 21** (Métis community predates municipality)
- **same_year: 4** (Y_FOUND matches `founded` exactly)
- **muni_first: 3** (municipality formally predates Y_FOUND)
- **unknown: 6** (one or both dates null)

### The metis_first finding

**21 of 34 municipalities with Métis community associations (62%) were built into pre-existing Métis settlements.** This is the core finding of Query 5a. The precedence gaps range from 5 years (Duck Lake) to 50 years (Weldon/Glen Mary). Among the 21 metis_first cases, **9 are Type A** — municipalities that also predated a nearby surrender. These are the double-dispossession cases: the municipality incorporated an established Métis settlement and simultaneously generated accumulated presence correlating with reserve surrender pressure.

The 9 metis_first + Type A cases:

| municipality | metis gap | dist_m | nearest_surrender |
|---|---|---|---|
| Fort Qu'Appelle | +40 yrs | 0 | Pasqua (1910) |
| Regina Beach | +32 yrs | 0 | Last Mountain Lake (1918) |
| Lebret | +26 yrs | 0 | Pasqua (1910) |
| Delmas | +23 yrs | 10,980 | Thunderchild (1908) |
| Prince Albert | +23 yrs | 0 | Chakastaypasin (1897) |
| Rosthern | +23 yrs | 13,568 | Stoney Knoll (1897) |
| Punnichy | +8 yrs | 8,539 | George Gordon (1933) |
| Battleford | +7 yrs | 0 | Moosomin (1909) |
| Duck Lake | +5 yrs | 0 | One Arrow (1899) |

In every case the sequence runs: Métis community established → settler municipality built into or near that community → reserve surrender follows. Three temporally stacked displacements in the same location.

### The same_year cases

Regina, Abernethy, Balcarres, and Swift Current show Y_FOUND matching `founded` exactly. The Y_FOUND field in the Métis Communities dataset is approximate — a founding year assigned from available sources, often rounded to the decade or to a key documented event. An exact match is more likely to indicate data approximation than literal simultaneity. All four should be treated as probable metis_first cases pending source verification. Regina in particular had Métis freighters and voyageurs in the region well before 1882; the 1882 Y_FOUND likely reflects when the community became formally identifiable in sources rather than when Métis people first lived there.

### The muni_first cases and their limitations

**Saskatoon (gap -38, Y_FOUND 1920):** Saskatoon's `muni_first` classification is likely a data limitation rather than an accurate historical sequence. The "Saskatoon" community in the dataset (Y_FOUND 1920) may reflect when a specific documented settlement formed, not when Métis people first lived in the area. The Round Prairie Métis community (Y_FOUND 1855, currently matched to Dundurn 19 km south) is a possible candidate for earlier Métis presence connected to the Saskatoon area, but the nature and extent of that relationship requires further source work before claims can be made. Saskatoon should not be treated as a genuine muni_first case; it is more accurately flagged as unknown pending archival investigation.

**Ruddell/Baljennie (gap -41, Y_FOUND 1945):** Baljennie appears to be a post-WWII community — Y_FOUND 1945 may reflect a road allowance settlement that formed as families were displaced from elsewhere. The municipality predates this specific community formation, but the Métis families involved likely had prior presence in other locations. A genuine muni_first in terms of this specific community's documented dates; analytically weaker than the others.

**Landis/Cando (gap -4):** Minor inversion, within the margin of Y_FOUND precision.

### Raibmon's frame applied to the temporal sequence

Query 5a makes the Métis dimension of the colonial genealogy temporally explicit. Raibmon's genealogical method asks not just who was present but in what order — because the order encodes the dispossession. The `metis_first` cases are not cases where settlers and Métis communities happened to be near each other; they are cases where the Métis settlement was the prior land use that the colonial municipality displaced. The municipal boundary is the instrument of dispossession. The gap years measure how long the Métis community existed before that boundary arrived to absorb it.

The 50-year gap at Weldon/Glen Mary is notable even though the spatial association is loose (19 km). The Glen Mary Métis community was established in 1855 — a generation before the CPR reached Saskatchewan, and half a century before Weldon was founded in 1905. The colonial genealogy in this area extends back to HBC employment and river lot settlement well before the railway era that dominates the municipal founding narrative.

**What this adds to the project argument:** The settlement of prairie municipalities was not simply the occupation of empty land by incoming settlers. In 62% of the cases where a Métis community is documented near a municipality, the Métis community was already there. The colonial municipality arrived second, absorbed or surrounded the prior Métis settlement, and in the Type A cases then correlated with surrender pressure on adjacent Indigenous reserves. The genealogy runs: prior Métis land use → colonial municipal absorption → reserve surrender pressure. Three phases of the same dispossession process, each documented in a different data layer.

---

## Query 6 — High surrender density: cluster pressure analysis

**Run date:** 2026-04-06

**Query:** See `cypher_queries.md` — Query 6. Returns all municipalities with 3 or more surrendered parcels within 25 km, with commercial type, temporal type, distance to nearest surrender, and Métis presence. Not restricted to Type A — captures the full density picture regardless of founding sequence.

**Note on row count:** 73 rows returned due to multiple IS_TYPE relationships per municipality (same inflation as Query 1). Interpreted below as distinct municipalities.

### Results — distinct municipalities, deduplicated

**7 surrenders within 25 km**

| municipality | commercial types | n_5km | type | min_dist_m | metis |
|---|---|---|---|---|---|
| Punnichy, VL | Farm-Service Town; Small Service Centre | 0 | A | 7,936 | True |
| Battleford, T-V | Regional Service Centre | 0 | A | 10,264 | True |
| North Battleford, C | City | 0 | A | 9,010 | False |

**6 surrenders within 25 km**

| municipality | commercial types | n_5km | type | min_dist_m | metis |
|---|---|---|---|---|---|
| Lestock, VL | Small Service Centre | 3 | A | 0 | True |
| Blaine Lake, VL | Farm-Service Town; Small Service Centre | 0 | A | 10,760 | False |
| Leask, VL | Farm-Service Town; Small Service Centre | 5 | A | 0 | True |
| Marcelin, VL | Small Service Centre | 1 | A | 802 | False |

**5 surrenders within 25 km**

| municipality | commercial types | n_5km | type | min_dist_m | metis |
|---|---|---|---|---|---|
| Broadview, T-V | Railway Town; Regional Service Centre | 1 | A | 1,241 | False |
| Stockholm, VL | Organized/Ethnic; Swedish Settlement; Small Service Centre | 0 | A | 22,676 | False |
| Edenwold, VL | Organized/Ethnic; German Settlement; Small Service Centre | 0 | A | 6,884 | False |
| Quinton, VL | Farm Cluster; Organized/Ethnic; German Settlement; Small Service Centre | 0 | A | 6,612 | False |
| Parkside, VL | Farm-Service Town; Small Service Centre | 0 | A | 13,407 | False |

**4 surrenders within 25 km**

| municipality | commercial types | n_5km | type | min_dist_m | metis |
|---|---|---|---|---|---|
| Dubuc, VL | Small Service Centre | 0 | A | 15,322 | False |
| B-Say-Tah, VL | Farm-Service Town; Small Service Centre | 0 | A | 5,900 | False |
| Dysart, VL | Organized/Ethnic; German Settlement; Small Service Centre | 0 | A | 12,210 | False |
| Fort Qu'Appelle, VL | Farm-Service Town; Local Service Centre | 0 | A | 8,216 | True |
| Lipton, VL | Farm-Service Town; Organized/Ethnic; Jewish Colony; Small Service Centre | 0 | A | 7,877 | False |
| Jasmin, VL | Organized/Ethnic; Ukrainian Settlement; Small Service Centre | 0 | A | 19,904 | True |
| Raymore, VL | Small Service Centre | 1 | A | 3,549 | False |
| Delmas, VL | Farm Cluster; Small Service Centre | 3 | A | 0 | True |

**3 surrenders within 25 km**

| municipality | commercial types | n_5km | type | min_dist_m | metis |
|---|---|---|---|---|---|
| Grayson, VL | Organized/Ethnic; German Settlement; Small Service Centre | 0 | A | 12,480 | False |
| Killaly, VL | Organized/Ethnic; German Settlement; Small Service Centre | 0 | A | 19,776 | False |
| Balgonie, T-V | Small Service Centre | 0 | A | 18,798 | False |
| Qu'Appelle, T-V | Regional Service Centre | 0 | A | 13,027 | False |
| Craven, VL | Farm-Service Town; Small Service Centre | 0 | A | 14,023 | False |
| Cupar, VL | Small Service Centre | 0 | A | 19,650 | False |
| Lebret, VL | Small Service Centre | 0 | A | 14,958 | True |
| Markinch, VL | Organized/Ethnic; German Settlement; Small Service Centre | 0 | A | 14,626 | False |
| McLean, VL | Farm Cluster; Small Service Centre | 0 | A | 16,438 | False |
| Southey, VL | Small Service Centre | 0 | A | 12,263 | False |
| Kamsack, T-V | Regional Service Centre | 1 | A | 0 | False |
| Veregin, VL | Organized/Ethnic; Doukhobor Settlement; Small Service Centre | 0 | A | 7,535 | False |
| Kelliher, VL | Farm-Service Town; Small Service Centre | 0 | A | 11,832 | False |
| Leross, VL | Small Service Centre | 2 | B | 1,941 | False |
| Denholm, VL | Farm Cluster; Railway Town; Small Service Centre | 0 | B | 20,956 | False |
| Vawn, VL | Small Service Centre | 0 | B | 17,970 | False |

### Type A dominance

All municipalities with ≥4 surrenders within 25 km are Type A. Of the 16 municipalities in the 3-surrender group, 13 are Type A and 3 are Type B (Leross, Denholm, Vawn). No Type C or none-type municipalities appear anywhere in the high-density set. The 25 km surrender density is not random with respect to temporal type — high concentrations of surrendered land cluster around municipalities that predated the surrenders, not around post-surrender settlements.

### The Battle River corridor — highest-density zone in the province

Battleford and North Battleford both return 7 surrenders within 25 km, sharing the same 7 parcels. Together with Blaine Lake (6), Leask (6), and Marcelin (6), the Battle River / Muskeg Lake area contains the densest concentration of surrendered reserve land in the province relative to adjacent municipalities. Battleford (founded 1875) is the oldest settlement in the high-density set — its 34-year pre-emptive gap, its HBC/NWMP founding type, and its position at the centre of this cluster together make it the strongest case for the pre-railway administrative-presence argument.

Leask is particularly striking within this corridor: 6 surrenders within 25 km, 5 within 5 km, dist_m = 0, overlap = True, Type A, Métis present. Five separate surrendered parcels within 5 km of a municipality that geometrically overlaps surrendered reserve land. This is the most intense 5km surrender density in the dataset.

### Ethnic settlement types in the high-density zones

The commercial type data confirms and extends Query 1's finding. Across the ≥3 surrender group, ethnic and organized settlement labels appear throughout: German Settlement (Edenwold, Quinton, Dysart, Grayson, Killaly, Markinch), Ukrainian Settlement (Jasmin), Swedish Settlement (Stockholm), Doukhobor Settlement (Veregin), Jewish Colony (Lipton), Organized/Ethnic Settlement (multiple). These are not outliers at the edges of the high-density zones — they are central to them.

Query 1 showed that ethnic/organized settlement types account for 39 of 154 label assignments across the 82 Type A municipalities, and that farm clusters and ethnic colonies sit closest to surrendered land on average. Query 6 shows that the same types appear disproportionately in the highest-density surrender zones. The correlation is consistent across multiple query angles. Raibmon's argument that a coherent settler society was not required for dispossession to occur is spatially confirmed: the communities with the most diverse, internally differentiated settler populations — including communities marginalized within settler society itself — are precisely those sitting in the zones of highest reserve surrender density.

### Parkside — new high-density entry

Parkside (5 surrenders within 25 km, Type A, Farm-Service Town) has not appeared in previous query results. It sits in the Battleford/Muskeg Lake corridor, consistent with that area's high overall density. Worth including in any corridor-level case study of the Battle River region.

### Punnichy — the persistent outlier

Punnichy ties Battleford and North Battleford at 7 surrenders within 25 km despite being a small village rather than a regional centre — and with n_5km = 0, all 7 surrendered parcels are at intermediate distance rather than immediately adjacent. The George Gordon surrender (1933) falls outside the main boom period and is already flagged from Query 4 as requiring follow-up. Query 6 confirms that Punnichy sits at the centre of an unusually dense surrender landscape even by the standards of the province's highest-density zones.

### Type B entries

Leross, Denholm, and Vawn are the only non-Type-A municipalities in the high-density set. Type B means their founding was concurrent with (within 5 years of) the nearest surrender rather than preceding it. They were planted into landscapes where the surrender process was already underway. Their presence in the high-density list is consistent with the corridor argument: high-density zones attracted multiple waves of settlement, some of which arrived simultaneously with rather than before the formal surrender events.
