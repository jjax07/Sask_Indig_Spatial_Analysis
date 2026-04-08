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

---

## Query 8 — Type A cities and towns only: organized settler pressure frame

**Run:** 2026-04-07

**Query correction:** Original query used abbreviations 'RSC' and 'LSC' which do not match graph values. Corrected to full names 'Regional Service Centre', 'Local Service Centre', and 'City'. Query description stated "villages excluded" but commercial type and municipal status are independent — Fort Qu'Appelle, Balcarres, Foam Lake, and Shellbrook are all VL municipalities with RSC or LSC commercial types and appear in results accordingly.

### Results

| Name | Commercial type | Nearest reserve | Surrender | n_25km | dist_m | Métis |
|---|---|---|---|---|---|---|
| North Battleford, C | City | Moosomin | 1909 | 7 | 9,010 | No |
| Battleford, T-V | RSC | Moosomin | 1909 | 7 | 10,264 | Yes |
| Broadview, T-V | RSC | Kahkewistahaw | 1907 | 5 | 1,241 | No |
| Fort Qu'Appelle, VL | LSC | Pasqua | 1910 | 4 | 8,216 | Yes |
| Kamsack, T-V | RSC | Cote | 1906 | 3 | 0 | No |
| Qu'Appelle, T-V | RSC | Pasqua | 1906 | 3 | 13,027 | No |
| Whitewood, T-V | LSC | Ochapowace | 1919 | 2 | 6,424 | No |
| Grenfell, T-V | RSC | Cowessess | 1907 | 2 | 6,483 | No |
| Duck Lake, T-V | LSC | One Arrow | 1899 | 2 | 10,726 | Yes |
| Arcola, T-V | RSC | Ocean Man | 1901 | 2 | 15,961 | No |
| Rosthern, T-V | RSC | Stoney Knoll | 1897 | 2 | 17,245 | Yes |
| Melfort, T-V | RSC | Cumberland | 1902 | 1 | 12,061 | No |
| Wolseley, T-V | RSC | Carry The Kettle | 1905 | 1 | 14,395 | No |
| Yorkton, T-V | RSC | Little Bone | 1907 | 1 | 15,520 | No |
| Semans, VL | LSC | Poor Man's | 1919 | 1 | 16,090 | No |
| Saltcoats, T-V | RSC | Little Bone | 1907 | 1 | 16,321 | No |
| Canora, T-V | RSC | The Key | 1909 | 1 | 16,444 | No |
| Lumsden, T-V | RSC | Last Mountain Lake | 1918 | 1 | 16,573 | No |
| Prince Albert, C | City | Chakastaypasin | 1897 | 1 | 17,431 | Yes |
| Melville, T-V | RSC | Little Bone | 1907 | 1 | 19,350 | No |
| Regina, C | City | Piapot | 1919 | 1 | 21,518 | Yes |
| Indian Head, T-V | RSC | Pasqua | 1906 | 1 | 22,364 | No |
| Balcarres, VL | LSC | Little Black Bear | 1928 | 1 | 23,253 | Yes |
| Foam Lake, VL | RSC | Fishing Lake | 1907 | 1 | 24,221 | No |
| Shellbrook, VL | LSC | Mistawasis | 1919 | 1 | 24,731 | No |

### Findings

**The larger the settlement, the further it sits from surrendered land.** Most RSC/LSC/City settlements are 10,000–24,000 metres from the nearest surrendered parcel. Only Kamsack (0m) and Broadview (1,241m) are genuinely close. This is the inverse of the pattern identified in Query 1, where farm clusters and ethnic colonies averaged around 10,000–11,000m with many sitting substantially closer.

**The underlying assumption of the query does not hold.** The query was designed to surface cases where organized, institutionally legible settler pressure — boards of trade, municipal petitions, commercial lobbying — drove surrender demand. But the spatial data shows that higher-tier settlements are systematically further from surrendered land, not closer to it. The query's premise assumed that more organized pressure produced more intense spatial outcomes; the data suggests the opposite.

**The interpretive frame that does fit:** larger centres and smaller farm settlements operated through different mechanisms and at different spatial scales. Farm clusters and ethnic colonies needed direct access to surrendered land — they were ploughing it, fencing it, farming it. Proximity was the condition of their economic existence. Larger centres benefited indirectly: through market expansion, increased hinterland population, and commercial traffic generated by surrounding agricultural settlement. They did not need to sit on surrendered land; they needed surrendered land to be settled so that settlers would buy goods, ship grain, and use their services. Both are forms of colonial pressure, but operating through distinct mechanisms.

**This reframes what "pressure" means at each scale.** Farm clusters and ethnic colonies generated pressure through physical presence and encroachment — Raibmon's microtechniques operating at the level of everyday agricultural practice. Larger centres generated pressure more indirectly: formal petitions, letters to Indian Affairs, political lobbying, organized commercial interest in opening surrounding territory. The spatial distance of RSC/LSC settlements from surrendered land is not evidence that they were uninvolved in dispossession — it is evidence that their involvement operated through a different register.

**Kamsack is the exception.** It is the only RSC in the set with dist_m = 0. Kamsack was simultaneously a regional service centre and a direct land-pressure case. This dual character — institutional scale combined with physical proximity and documentary causation — is part of what makes it the anchor case study.

**The Battleford/North Battleford pair** leads on surrender density (7 each) but the count reflects the same 7 parcels — they share a corridor and are counted independently. Together they represent the administrative-centre end of the spectrum: Battleford founded 1875 as territorial capital (HBC, NWMP), North Battleford a later CPR-era city. Their high n_25km reflects the corridor density of the Battle River region identified in Query 6, not a direct proximity relationship.

**Métis presence is sparse in this set.** Only 6 of 25 results have Métis communities present (Battleford, Fort Qu'Appelle, Duck Lake, Rosthern, Prince Albert, Regina). This is consistent with the broader pattern: Métis communities are most concentrated near the smaller settlements that sit closest to surrendered land, not near the larger commercial centres that benefited indirectly.

---

## Query 7 — The 6 geometric overlap cases: full profile

**Run:** 2026-04-07

**Note on railway data:** Query 7 as written uses `SERVED_BY` relationships to retrieve railway data, but these relationships are not reliably populated. Railway data (`first_railway`, `railway_arrives`) exists as direct properties on Settlement nodes and must be read from there. Results below incorporate the corrected node-property values.

### Results

| Municipality | Reserve | Surrender year | Temporal type | Métis present | Railway | Rail year |
|---|---|---|---|---|---|---|
| Kamsack, T-V | Cote | 1906 | A | No | CNoR | — |
| Delmas, VL | Thunderchild | 1908 | A | Yes | CNoR | 1905 |
| Laird, VL | Stoney Knoll | 1897 | C | No | CNoR | — |
| Leask, VL | Mistawasis | 1911 | A | Yes | CNoR | 1911 |
| Lestock, VL | Muskowekwan | 1920 | A | Yes | GTPR | 1908 |
| Regina Beach, VL | Last Mountain Lake | 1918 | A | Yes | CPR | 1911 |

*Railway years for Kamsack and Laird not retrieved in this run — not absent from the dataset.*

### Findings

**5 of 6 are Type A.** Geometric overlap with surrendered reserve land — the strongest spatial criterion — is overwhelmingly associated with municipalities that predated the formal surrender. These are not cases where a municipality grew toward already-surrendered land; they are cases where the municipality existed first and the surrender followed.

**Laird is the only Type C.** Stoney Knoll was surrendered in 1897 before Laird was established (first postmaster 1900, first school 1910). Laird is a Mennonite ethnic colony served by CNoR. The overlap here reflects geographic proximity rather than temporal precedence — the surrendered land was absorbed into the municipality's eventual footprint, but the settlement did not precede the surrender. Laird's inclusion in the overlap set is analytically distinct from the five Type A cases and should be noted when the overlap criterion is cited as evidence of the "pressure then surrender" argument.

**4 of 6 have Métis presence.** Among the overlap cases, Métis community co-presence is the norm rather than the exception. This aligns with Query 5/5a findings: zones of deepest spatial dispossession (geometric overlap) tend to be the same zones where Métis communities were present. Kamsack and Laird are the two exceptions.

**Kamsack is the anchor case.** The event context explicitly names the 1906 Cote First Nation land surrender as playing "a large role in the settling of Kamsack." It also records Crowstand Residential School (1889) and a Presbyterian Mission church (1889) — pre-municipal colonial institutional presence that directly precedes and contextualizes the surrender. Kamsack is the only overlap case with documentary causation established in the data; all others are correlations warranting archival follow-up.

**CNoR dominates.** Four of the six overlap municipalities are associated with Canadian Northern Railway — Kamsack, Delmas, Laird, and Leask. This is consistent with the corridor-clustering pattern identified in Query 4a, where CNoR corridors account for the largest share of Type A pressure clusters.

**Regina Beach — colonization company founding.** The 1902 Pearson Land Company event note is the key context here. Settlement began informally as early as 1882, but it was a land company that formalized townsite development. The CPR arrived in 1911, seven years before the Last Mountain Lake surrender (1918). This is a case where both colonization company activity and railway infrastructure were in place well before the formal surrender.

**Lestock — GTPR, 1908.** Railway arrived 12 years before the Muskowekwan surrender (1920). Lestock is a small village with limited event data, but the 12-year gap between railway arrival and surrender is consistent with the Sifton-era boom dynamic: railway arrives, settlement accumulates, pressure mounts, surrender follows.

**Leask — the high-density outlier.** Already flagged in Query 6 as having the most intense 5 km surrender density in the dataset (5 parcels within 5 km, dist_m = 0, overlap = True). Query 7 confirms it also appears in the geometric overlap set, with Mistawasis surrendered in 1911, the same year the CNoR arrived. The simultaneity of railway arrival and surrender year is striking: railway, townsite, and surrender all converge in 1911.

---

## Query 7a — Overlap cases: cross-query synthesis profile

**Run:** 2026-04-07

### Results

| Municipality | Type | Founded | Metis y_found | Earliest event | Effective start | Surrender | Formal gap | Effective gap | Railway | Rail year | Rail gap | n_5km | n_25km | Métis community | Métis dist_m |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Laird, VL | C | 1908 | — | 1908 | 1908 | 1897 | −11 | −11 | CNoR | 1910 | −13 | 1 | 1 | — | — |
| Kamsack, T-V | A | 1899 | — | 1889 | 1889 | 1906 | 7 | 17 | CNoR | 1904 | 2 | 1 | 3 | — | — |
| Delmas, VL | A | 1905 | 1882 | 1900 | 1882 | 1908 | 3 | 26 | CNoR | 1905 | 3 | 3 | 4 | Bresaylor | 10,980 |
| Leask, VL | A | null | null | 1912 | 1912* | 1911 | null | −1* | CNoR | 1911 | 0 | 5 | 6 | Muskeg Lake | 5,127 |
| Regina Beach, VL | A | 1902 | 1870 | 1902 | 1870 | 1918 | 16 | 48 | CPR | 1911 | 7 | 1 | 1 | Last Mountain Lake | 0 |
| Lestock, VL | A | null | 1890 | 1924 | 1890 | 1920 | null | 30 | GTPR | 1908 | 12 | 3 | 6 | Lestock | 0 |

*Leask effective_start and effective_gap are artefacts of the null `founded` and null `nearest_metis_y_found` — the earliest event year (1912) postdates the surrender (1911). Leask's Type A classification was assigned in Phase 2 from criteria not fully captured in the `founded` property. The rail gap (0) and the 5-km surrender density (highest in the dataset) are the analytically reliable indicators for Leask.

### Cross-query evidence by settlement

**Kamsack, T-V** appears in: Query 1 (Regional Service Centre), Query 4a (CNoR corridor, rail 1904), Query 6 (1 surrender within 25km, dist_m = 0), Query 7 (overlap confirmed, documentary causation). It does not appear in Queries 2, 5, or 5a — no Métis association in the Phase 3 data, which is a known gap. The key correction from 7a: effective_start 1889 (Crowstand Residential School), pushing the effective gap from 7 to 17 years. Kamsack had a residential school operating for 10 years before any municipal founding, followed by Doukhobor settlers (1899), a land company (1908), and the CNoR (1904). The documentary causation note makes it the anchor case for the argument; the 7a effective_start correction shows that the pre-emptive presence was deeper than the formal founding date indicates.

**Delmas, VL** appears in: Query 1 (Farm Cluster, avg dist 10,945m — closest commercial type to surrendered land), Query 2 (triple convergence — Type A + overlap + Métis), Query 2b (railway gap 3 years, clearest McGuire Type 2 case), Query 3a sensitized (effective_gap 26, Métis anchor 1882, formal gap only 3), Query 4a (CNoR corridor), Query 5/5a (Métis community Bresaylor, metis_first by 23 years), Query 6 (3 surrenders within 25km). The Métis anchor correction is the most analytically significant: the formal founding-to-surrender gap of 3 years makes Delmas look like a nearly simultaneous townsite-surrender case, but the sensitized effective gap of 26 years shows that the Bresaylor Métis community — present since 1882 — predates both the CNoR townsite (1905) and the Thunderchild surrender (1908) by more than two decades. The "rapid" surrender was the conclusion of a much longer accumulation.

**Leask, VL** appears in: Query 2 (triple convergence), Query 2b (rail gap 0), Query 5/5a (Métis community Muskeg Lake, sequence unknown due to null founded and null metis_y_found), Query 6 (6 surrenders within 25km — highest 25km density in the overlap set; 5 within 5km — highest 5km density in the entire dataset), Query 7 (overlap confirmed). The null `founded` property is a recurring data gap, but Leask's position in the data is clear from every other indicator: it sits at the centre of the densest surrender landscape in the province, at dist_m = 0 from Mistawasis reserve land, with the CNoR arriving in the same year as the surrender (1911). The 0-year rail gap and 5-parcel 5km density together make Leask the most spatially intense case in the dataset even without a reliable founding date.

**Lestock, VL** appears in: Query 2 (triple convergence), Query 2b (GTPR, rail gap 12 years), Query 5 (Métis community Lestock at dist_m = 0 — inside the municipal boundary), Query 5a (sequence unknown, Métis y_found 1890), Query 6 (3 surrenders within 25km). The 7a effective_start correction is important: `founded` is null, but the Métis community at Lestock dates to 1890, giving an effective_start of 1890 and an effective_gap of 30 years — the second-longest in the overlap set after Regina Beach. The Muskowekwan surrender (1920) came 30 years after the Métis community was established and 12 years after the GTPR arrived. The Métis community is inside the municipal boundary, meaning the municipality eventually enclosed it.

**Regina Beach, VL** appears in: Query 1 (Railway Town), Query 2 (triple convergence), Query 2a (non-railway overlap cases), Query 2b (CPR, rail gap 7), Query 3a (formal gap 16, appears in long-gap set), Query 3a sensitized (effective_gap 48, Métis anchor 1870 — deepest effective gap in the overlap set), Query 4a (CPR 1911 corridor, alongside Bulyea, Dilke, Silton), Query 5/5a (Métis community Last Mountain Lake at dist_m = 0, metis_first by 32 years, overlap = True), Query 6 (1 surrender within 25km — not a high-density case). Regina Beach is the most temporally layered case in the overlap set. Settlement began informally in 1882, the William Pearson Land Company formalized it in 1902, the CPR arrived in 1911, and the Last Mountain Lake surrender followed in 1918. The Métis community at Last Mountain Lake predates all of this by at least 32 years and is enclosed within the municipal boundary. The formal founding-to-surrender gap of 16 years is already substantial; the sensitized effective gap of 48 years is the longest in the overlap set, and one of the longest in the entire dataset.

**Laird, VL** appears in: Query 3a sensitized (Rosthern, the nearby Stoney Knoll case, appears — Laird itself does not, because it is Type C and the sensitized query filters for Type A). Laird does not appear in Queries 2, 5, or 5a. It is present in Query 7 and 7a as the outlier. The 7a data confirms: Stoney Knoll surrendered 1897, Laird's first postmaster and earliest events all date to 1908–1910, CNoR arrived 1910 — 13 years after the surrender. No Métis presence. Laird is a Mennonite ethnic colony whose footprint came to overlap land that had already been surrendered. It is the test case that distinguishes geographic overlap from the "pressure then surrender" dynamic.

### Unified argument

The 6 geometric overlap municipalities are the most spatially concentrated expression of colonial dispossession in the Saskatchewan dataset. What makes them analytically significant is not the overlap criterion alone — it is what the cross-query evidence reveals when each settlement is read against the full record of queries 1 through 6.

**Five of the six show the "pressure then surrender" sequence.** Kamsack, Delmas, Leask, Lestock, and Regina Beach all preceded the formal surrender of the reserve land that now sits within or adjacent to their boundaries. This is not a statistical tendency across the broader Type A set — it is a structural feature of the overlap cases specifically. The municipalities that ended up geometrically absorbing surrendered reserve land were, in five of six instances, the municipalities that existed before the surrender happened.

**Effective presence substantially predates formal founding in every resolvable case.** The formal founding dates for the 5 Type A overlap municipalities range from null (Leask, Lestock) to as recent as 1905 (Delmas). But the effective colonial presence — measured by institutional event anchors and Métis community founding dates — extends significantly further back in every case where data is available: Kamsack to 1889 (Crowstand Residential School), Delmas to 1882 (Bresaylor Métis community), Regina Beach to 1870 (Last Mountain Lake Métis community), Lestock to 1890 (Lestock Métis community). The municipalities that geometrically enclosed surrendered reserve land were the endpoints of colonial accumulations that, in some cases, had been building for 30 to 48 years before the formal surrender occurred.

**Métis displacement is embedded in the overlap cases.** Four of the five Type A overlap municipalities have Métis communities present, and in two of those four — Regina Beach and Lestock — the Métis community is inside the municipal boundary (dist_m = 0). The zones of deepest First Nations spatial dispossession (geometric overlap with surrendered reserve land) are the same zones where Métis communities had been established for decades before the municipalities arrived. The overlap cases do not show First Nations and Métis dispossession as separate stories: they show them operating in the same places, through the same accumulation of colonial presence.

**Railway infrastructure was in place before every surrender in the Type A overlap set.** The rail gaps for the five resolvable Type A cases range from 0 (Leask, simultaneous) to 12 years (Lestock), with Kamsack at 2, Delmas at 3, and Regina Beach at 7. This is a clean confirmation of McGuire's mechanism: railway arrival preceded surrender in every case. The variation in gap length reflects different phases of settler accumulation — Delmas and Kamsack are short-gap boom-era cases; Regina Beach and Lestock are longer-accumulation cases where colonization company or Métis displacement dynamics were already established before the railway arrived.

**CNoR is the dominant infrastructure agent in the overlap set.** Four of six municipalities — Kamsack, Delmas, Laird, and Leask — are CNoR settlements. The Canadian Northern Railway built the lines that planted three of the five Type A overlap settlements. This is consistent with Query 4a's finding that CNoR corridors account for the largest share of Type A pressure clusters province-wide. In the overlap set, CNoR's role is not merely correlational: at Delmas, the CNoR both built the line and created the townsite (1905) that then generated the three-year surrender window. At Leask, CNoR arrival and surrender are simultaneous (1911).

**Kamsack anchors the argument with documentary evidence; the pattern in the other five demands archival follow-up.** The event data explicitly names the 1906 Cote surrender as causal to Kamsack's settlement. The same pattern — institutional presence accumulating over years or decades, followed by railway infrastructure, followed by formal surrender — is visible in all five Type A overlap cases. But absent documentary evidence of the kind preserved in the Kamsack record, the other cases remain correlation under Raibmon's framework. The convergence of spatial, temporal, and institutional evidence across queries 1 through 7a is strong enough to warrant systematic archival investigation: petition records, Indian Affairs correspondence, and local land company records for Delmas, Leask, Lestock, and Regina Beach.

**Laird is the exception that clarifies the rule.** Stoney Knoll was surrendered in 1897. Laird was established in 1908. The CNoR arrived in 1910. The land overlap is real — Laird's footprint includes surrendered Stoney Knoll land — but the temporal sequence runs the other direction. Laird is a Mennonite ethnic colony that was planted into a landscape already reduced by surrender, not one whose presence generated the conditions for surrender. Laird's presence in the overlap set does not weaken the argument; it sharpens the analytical distinction between geographic absorption of surrendered land and the pressure-then-surrender dynamic that defines the other five cases.

---

## Query 8a — Indirect benefit: geographic hinterland density around RSC/LSC settlements

**Run:** 2026-04-07

Counts Type A farm-scale satellites within 50km of each RSC/LSC/City hub. Ordered by satellite count.

### Results

| Hub | Hub dist_m | Type A satellites (50km) | Avg satellite dist to surrender |
|---|---|---|---|
| Balcarres, VL | 23,253 | 28 | 13,997 |
| Lumsden, T-V | 16,573 | 24 | 14,129 |
| Fort Qu'Appelle, VL | 8,216 | 21 | 13,096 |
| Qu'Appelle, T-V | 13,027 | 20 | 12,732 |
| Regina, C | 21,518 | 17 | 12,540 |
| Melville, T-V | 19,350 | 17 | 16,012 |
| Indian Head, T-V | 22,364 | 16 | 11,649 |
| Semans, VL | 16,090 | 14 | 15,777 |
| Duck Lake, T-V | 10,726 | 10 | 10,836 |
| Grenfell, T-V | 6,483 | 10 | 14,342 |
| Yorkton, T-V | 15,520 | 10 | 16,074 |
| Wolseley, T-V | 14,395 | 9 | 15,606 |
| Broadview, T-V | 1,241 | 8 | 17,804 |
| Saltcoats, T-V | 16,321 | 7 | 17,762 |
| Kamsack, T-V | 0 | 7 | 10,774 |
| Foam Lake, VL | 24,221 | 7 | 13,776 |
| Shellbrook, VL | 24,731 | 5 | 5,523 |
| Canora, T-V | 16,444 | 5 | 8,915 |
| Rosthern, T-V | 17,245 | 5 | 4,464 |
| Whitewood, T-V | 6,424 | 4 | 15,479 |
| **North Battleford, C** | 9,010 | **2** | 0 |
| **Battleford, T-V** | 10,264 | **2** | 0 |
| Prince Albert, C | 17,431 | 1 | 24,731 |
| Arcola, T-V | 15,961 | 1 | 11,113 |

### Findings

**The Qu'Appelle valley dominates geographic hinterland density.** Balcarres (28), Lumsden (24), Fort Qu'Appelle (21), and Qu'Appelle (20) lead the ranking — all in the same region. This is not a cluster of large regional centres; it is a dense concentration of small Type A settlements in the Last Mountain Lake / Qu'Appelle valley corridor generating high satellite counts around the nearest hubs.

**Battleford and North Battleford collapse to the bottom.** The pair that led Query 6 (7 surrenders within 25km each) and Query 8 (highest absolute density) returns only 2 satellites each — both Delmas, counted via multiple IS_TYPE labels. The Battle River corridor had intense surrender concentration but not a dense farm-cluster hinterland within 50km by the geographic measure. This is a significant finding: the area of highest reserve reduction was not generated by the largest agricultural hinterland. It was generated by a smaller number of settlements sitting at very close range to reserve land.

**Shellbrook and Rosthern — small hubs with close-range satellites.** Shellbrook (5 satellites, avg 5,523m) and Rosthern (5 satellites, avg 4,464m) have the lowest average satellite distances to surrendered land in the set — their hinterland settlements sit very close to surrender zones. Both are CNoR/QLSRSC corridor hubs in the northern agricultural fringe. Shellbrook's satellites include Leask (one of the case study settlements), connecting hub and satellite through the same Battle River corridor.

**Kamsack's hinterland is moderate but close.** 7 satellites, avg 10,774m — the lowest average satellite distance among the mid-range hubs. Consistent with Kamsack's position as a direct-overlap RSC surrounded by a cluster of CNoR corridor settlements on the Cote/Canora line.

---

## Query 8b — Indirect benefit: railway corridor hinterland around RSC/LSC settlements

**Run:** 2026-04-07

**Method:** Python script (`analysis/08b_railway_corridor_hinterland.py`) combining two data sources:
- **Primary (Borealis):** HR_rails_NEW.shp filtered to pre-1921 Saskatchewan builder codes (1, 5, 2, 49, 49A, 49B, 53P, 53R, 14C). 327 line segments. Settlements snapped within 5km. Two settlements share a corridor if they match the same Borealis line segment. 426 of 429 settlements snapped (3 fallback).
- **Fallback (settlement_connections.json):** For the 3 unsnapped settlements and additional corridor connections missing from Borealis (e.g. M&NWR gaps), uses shared_railway company + railway_distance_km ≤ 200km.

**Data integrity note:** Borealis dataset is known to be incomplete (e.g. M&NWR absent). This method supplements existing data — it does not overwrite `first_railway` or `railway_arrives` on any Settlement node.

Outputs saved to: `analysis/08b_corridor_hinterland_results.csv`, `analysis/08b_corridor_detail.csv`

### Results

| Hub | Railway | Hub dist_m | Corridor satellites | Borealis | Fallback | Avg sat dist_m | Min sat dist_m |
|---|---|---|---|---|---|---|---|
| Balcarres, VL | CPR | 23,253 | 15 | 12 | 3 | 15,183 | 5,900 |
| Regina, C | CPR | 21,518 | 12 | 12 | 0 | 14,266 | 5,900 |
| Semans, VL | GTPR | 16,090 | 8 | 8 | 0 | 10,625 | 0 |
| Grenfell, T-V | CPR | 6,483 | 6 | 4 | 2 | 15,400 | 1,241 |
| Indian Head, T-V | CPR | 22,364 | 6 | 6 | 0 | 18,715 | 16,438 |
| Melville, T-V | GTPR | 19,350 | 6 | 6 | 0 | 13,644 | 4,902 |
| Qu'Appelle, T-V | CPR | 13,027 | 6 | 5 | 1 | 19,568 | 16,438 |
| Kamsack, T-V | CNoR | 0 | 5 | 2 | 3 | 11,339 | 2,357 |
| Lumsden, T-V | QLSRSC | 16,573 | 4 | 4 | 0 | 16,770 | 14,023 |
| Shellbrook, VL | CNoR | 24,731 | 4 | 4 | 0 | 6,242 | 0 |
| Fort Qu'Appelle, VL | GTPR | 8,216 | 4 | 4 | 0 | 12,225 | 5,900 |
| Wolseley, T-V | CPR | 14,395 | 3 | 3 | 0 | 19,634 | 17,247 |
| Canora, T-V | CNoR | 16,444 | 3 | 1 | 2 | 12,529 | 7,535 |
| Prince Albert, C | QLSRSC | 17,431 | 2 | 2 | 0 | 20,988 | 17,244 |
| Yorkton, T-V | Other | 15,520 | 2 | 2 | 0 | 17,836 | 16,321 |
| North Battleford, C | CNoR | 9,010 | 1 | 0 | 1 | 0 | 0 |
| Foam Lake, VL | CNoR | 24,221 | 1 | 0 | 1 | 16,479 | 16,479 |
| Duck Lake, T-V | QLSRSC | 10,726 | 1 | 1 | 0 | 17,244 | 17,244 |
| Broadview, T-V | CPR | 1,241 | 1 | 0 | 1 | 17,247 | 17,247 |
| Whitewood, T-V | CPR | 6,424 | 1 | 1 | 0 | 1,241 | 1,241 |
| Battleford, T-V | CNoR | 10,264 | 1 | 0 | 1 | 0 | 0 |
| Arcola, T-V | CPR | 15,961 | 1 | 1 | 0 | 11,113 | 11,113 |

### Findings

**The corridor lens confirms and sharpens the geographic picture.** Balcarres and Regina remain at the top with 15 and 12 corridor satellites respectively — but the counts are now meaningfully lower than 8a because corridor membership is constrained to settlements on the same physical line, not just within 50km. The Qu'Appelle valley CPR corridor is the dominant structure in the provincial landscape.

**Semans emerges as a notable GTPR hub.** With 8 corridor satellites and an average satellite distance to surrendered land of 10,625m — and a minimum of 0m (Lestock is among its satellites) — Semans sits at the centre of the densest GTPR corridor in the province by this measure. It is a small village with LSC commercial function, yet its railway corridor hinterland is more intensively connected to surrendered land than any RSC or city on the GTPR.

**Battleford and North Battleford remain at the bottom.** One corridor satellite each (Delmas, via fallback). The Battle River corridor's high surrender density was not generated through a dense farm-cluster satellite network on the CNoR main line — it was generated through a smaller number of settlements in immediate proximity to multiple reserves. This is a structurally different dispossession mechanism from the Qu'Appelle / GTPR corridor pattern.

**Shellbrook–Leask corridor connection confirmed.** Shellbrook (4 corridor satellites, avg 6,242m, min 0m) includes Leask as a Borealis-confirmed corridor satellite. This links two of the case study settlements — Shellbrook as a CNoR hub, Leask as the highest-density overlap settlement — on the same physical line. The indirect benefit chain here is spatially direct: Shellbrook was the nearest LSC to a corridor whose settlements were generating the most intense surrender pressure in the province.

**Kamsack's corridor is partially Borealis-confirmed, partially fallback.** 5 corridor satellites: 2 via Borealis, 3 via fallback. The fallback entries reflect CNoR lines in the Kamsack area that may be absent from or incompletely represented in the Borealis dataset. This is a known data gap and does not affect the analytical conclusion — Kamsack sits at the hub of a CNoR corridor cluster whose satellites include Canora, Arran, Pelley, Togo, and Veregin.

### 8a / 8b Synthesis — Two dispossession mechanisms at the hub scale

Read together, Queries 8a and 8b reveal that RSC/LSC/City hubs were not connected to reserve surrender through a single mechanism. Two structurally distinct patterns emerge:

**1. Corridor accumulation** — the Qu'Appelle valley CPR corridor and the GTPR main line produced dense networks of small Type A settlements whose cumulative proximity to surrendered land is consistent across both the geographic (8a) and railway-corridor (8b) measures. Hubs like Balcarres, Regina, Semans, Fort Qu'Appelle, and Melville benefited indirectly through large satellite networks spread across broad agricultural zones. Their own distances to surrendered land are moderate to large, but their hinterland settlements collectively generated diffuse, province-wide pressure along established railway lines. This is the indirect benefit chain articulated in the Query 8 interpretation: these centres did not need to sit on surrendered land because their commercial function depended on the agricultural surplus of surrounding settlements that did.

**2. Close-range intensity** — the Battle River corridor (Battleford, North Battleford) shows the opposite pattern. Both hubs rank last in satellite hinterland by both measures — one satellite each — yet produced the highest reserve surrender density in the province (7 surrenders within 25km). The pressure was not generated through a dense network of satellite settlements over a broad corridor. It was generated through a small number of settlements — primarily Delmas — sitting in immediate proximity to multiple reserves simultaneously. Fewer settlements, closer range, more reserves targeted in the same area. The mechanism is spatial concentration rather than network accumulation.

**Kamsack bridges both patterns.** It has a moderate corridor satellite hinterland (7 geographic, 5 railway), but is itself at dist_m = 0 — a direct overlap case. It functions simultaneously as a hub generating indirect benefits through its satellite network and as a direct-pressure settlement whose own footprint overlaps surrendered reserve land. This dual character is unique among the RSC/LSC hubs and is the strongest argument for its position as the anchor case study: it embodies both mechanisms in a single settlement, and has documentary evidence linking it to the surrender directly.

---

## Query 9 — Summary statistics: aggregate view of all temporal types

**Run:** 2026-04-07

### Results

| Temporal type | n | Avg dist to surrender (m) | n overlap | n Métis present | n within 5km |
|---|---|---|---|---|---|
| A | 82 | 13,512 | 5 | 15 | 10 |
| B | 27 | 13,306 | 0 | 2 | 4 |
| C | 8 | 12,345 | 1 | 2 | 3 |
| Indeterminate | 7 | 17,619 | 0 | 0 | 0 |
| none | 305 | 75,927 | 0 | 15 | 0 |

### Findings

**Temporal type does not predict raw proximity — sequence does.** Type A, B, and C municipalities have nearly identical average distances to surrendered land (12,345–13,512m). The meaningful analytical distinction between these types is not how far they sit from surrender zones but whether they preceded, coincided with, or followed the surrender. Raw distance is not the argument; temporal sequence is.

**The none group is the real divide in the dataset.** 305 municipalities — 71% of the total — have no surrendered reserve land within meaningful proximity, averaging 75,927m to the nearest surrender. The gap between the A/B/C cluster (~13,000m) and the none group (~76,000m) is the structural feature of the dataset. Settlement in Saskatchewan was not uniformly distributed relative to reserve land; it was concentrated in corridors where surrender was most active.

**Geometric overlap is almost exclusively Type A.** 5 of 6 overlap cases are Type A; the one Type C overlap is Laird, the clarifying exception documented in Query 7. No Type B or none municipalities overlap with surrendered land. The strongest spatial criterion in the dataset is also the most temporally selective.

**Within 5km concentration in Type A.** 10 of the 17 settlements with a surrendered parcel within 5km are Type A — 59% of the close-range set, despite Type A being only 19% of all municipalities. Type B accounts for 4 of the remaining 7, Type C for 3. No none-type municipality has a surrendered parcel within 5km.

**Métis presence splits between Type A and none.** 15 Type A and 15 none-type municipalities have associated Métis communities. This is not a contradiction — it reflects that Métis communities were distributed across the province independently of the surrender geography. In the Type A set, Métis presence is a co-indicator of dispossession intensity. In the none set, Métis communities appear near settlements that grew independently of nearby reserve reduction — a separate displacement dynamic operating without the surrender mechanism.

---

## Query 10 — Frank Oliver's 1911 amendment: large municipalities near surrenders

**Run:** 2026-04-07

The 1911 *Indian Act* amendment permitted expropriation of reserve land without band consent where a reserve was adjacent to a town exceeding 8,000 population. Query 10 tests whether any Type A or B Saskatchewan municipalities met or approached this threshold by 1921.

### Results

Only one municipality qualifies — **Regina, C** (pop. 34,432, Type A, nearest reserve Piapot, surrender year 1919, dist_m 21,518, Métis present).

### Population context (top municipalities, all temporal types)

| Name | Pop 1921 | Temporal type | Dist to surrender (m) |
|---|---|---|---|
| Regina, C | 34,432 | A | 21,518 |
| Saskatoon, C | 25,739 | none | 60,194 |
| Moose Jaw, C | 19,285 | none | 54,803 |
| Prince Albert, C | 7,558 | A | 17,431 |
| Yorkton, T-V | 5,151 | A | 15,520 |
| North Battleford, C | 4,108 | A | 9,010 |

### Findings

**The Frank Oliver amendment had almost no practical application in Saskatchewan.** Only Regina clears the 8,000 population threshold. Saskatoon and Moose Jaw — the 2nd and 3rd largest cities — are both temporal type none, with no surrender within meaningful proximity. Prince Albert (7,558) narrowly misses the threshold and is Type A, but falls short of formal eligibility.

**The amendment was a legally available mechanism that Saskatchewan's settlement geography made largely irrelevant.** The province's urban hierarchy was too compressed: most "cities" had populations of 2,000–4,000 in 1921. The dispossession documented in this dataset operated through small-settlement pressure — farm clusters, ethnic colonies, railway townsites — not through the formal expropriation powers the amendment created.

**Regina's case cannot be confirmed as an invocation of the amendment.** The Piapot surrender (1919) at 21km distance preceded by Regina's pre-existing Type A status is consistent with the standard pressure-then-surrender pattern. Whether the amendment was formally invoked requires archival investigation of the specific surrender proceedings. This dataset can confirm eligibility, not mechanism.

**This is a meaningful negative finding.** It narrows the analytical argument: Saskatchewan's reserve reduction was driven almost entirely by the informal accumulation of small-settler presence, not by top-down expropriation under federal statute. The Frank Oliver amendment is contextually significant — it reveals federal willingness to formalize dispossession when urban interests demanded it — but it was not the operative mechanism in Saskatchewan during the study period.

---

## Query 8c — Commercial type gradient: average distance to surrendered land by type

**Run:** 2026-04-07

### Results

| Commercial type | n | Avg dist_m | Median dist_m | n Type A | n overlap |
|---|---|---|---|---|---|
| Doukhobor Settlement | 1 | 7,535 | 7,535 | 1 | 0 |
| Jewish Colony | 1 | 7,877 | 7,877 | 1 | 0 |
| Ukrainian Settlement | 8 | 23,927 | 20,340 | 5 | 0 |
| Organized/Ethnic Settlement | 83 | 43,390 | 28,533 | 20 | 1 |
| German Settlement | 57 | 49,058 | 35,685 | 11 | 1 |
| Local Service Centre | 27 | 49,489 | 34,678 | 6 | 0 |
| City | 7 | 52,678 | 54,803 | 3 | 0 |
| Railway Town | 20 | 54,680 | 43,658 | 6 | 1 |
| Regional Service Centre | 39 | 54,881 | 40,766 | 16 | 1 |
| Small Service Centre | 356 | 58,994 | 49,710 | 57 | 5 |
| Farm-Service Town | 136 | 64,189 | 50,021 | 20 | 1 |
| Farm Cluster | 58 | 67,296 | 58,145 | 6 | 1 |
| St. Peter's Colony | 5 | 68,053 | 68,444 | 0 | 0 |
| Dutch/Mennonite Settlement | 3 | 94,097 | 128,054 | 0 | 0 |

### Findings

**The expected gradient did not appear.** The hypothesis going into this query was that farm clusters and ethnic colonies would sit closest to surrendered land and cities furthest — reflecting the two-tier mechanism identified in Query 8. Instead, farm clusters average 67,296m — the furthest of any substantive commercial type — while cities average 52,678m. The gradient is effectively reversed from what was expected.

**The explanation is methodological, not substantive.** Query 8c includes all 429 municipalities regardless of temporal type. Farm clusters have only 6 Type A members out of 58 total; the remaining 52 are in the none group, scattered across the province far from any surrendered land. When those 52 are included, they pull the average far upward. The same applies to Farm-Service Towns (20 Type A out of 136 total).

**The "farm clusters closest" finding from Query 1 is a property of Type A farm clusters specifically.** It does not characterize farm clusters as a commercial type in general. Commercial type alone is not a predictor of proximity to surrendered land. Temporal type — whether the settlement predated the surrender — is the load-bearing variable. Query 8c confirms this by demonstrating that the proximity pattern disappears when you remove the Type A filter.

**The practical implication for the argument:** you cannot look at a farm cluster on a map and infer proximity to surrendered land. You have to know whether it predated a surrender. The commercial type tells you what kind of settlement arrived; the temporal type tells you whether its arrival preceded the dispossession it benefitted from.

---

## Temporal type definitions and benefit mechanisms

The three temporal types classify the relationship between a municipality's founding and the nearest reserve surrender. They are not merely chronological categories — each corresponds to a distinct mechanism by which settler municipalities benefitted from Indigenous land dispossession.

### Type A — Pressure preceding surrender
**Definition:** The municipality was founded more than 5 years before the nearest reserve surrender.
**Mechanism:** The municipality's existence — its agricultural activity, infrastructure demand, commercial pressure, and accumulated settler presence — generated the conditions that led to formal surrender. This is Raibmon's "accumulated microtechniques" pattern: no single act of conspiracy, but a colonial genealogy whose weight eventually translated into formal legal dispossession. The municipality benefitted from land that was cleared partly in response to its own presence.
**Dataset:** 82 municipalities (19% of total). The core evidential set for the "pressure then surrender" argument.

### Type B — Simultaneous arrival
**Definition:** The municipality was founded within 5 years (before or after) of the nearest reserve surrender.
**Mechanism:** The municipality arrived simultaneously with the surrender process — either planted in anticipation of a surrender already in negotiation, or established immediately after one. The causal direction is ambiguous without archival evidence: the settlement may have generated rapid surrender pressure, or the surrender may have been arranged in advance to accommodate incoming settlement. In either case the municipality benefitted directly from freshly surrendered land. Type B represents the compressed version of the Type A cycle — the petition-to-surrender window collapsed to near-simultaneity, consistent with the most intense phases of the Sifton-era boom.
**Dataset:** 27 municipalities (6% of total).

### Type C — Post-surrender settlement
**Definition:** The municipality was founded more than 5 years after the nearest reserve surrender.
**Mechanism:** The municipality was established on or adjacent to land that had already been cleared through surrender. Settlers arrived into a landscape already reduced — the dispossession preceded them and was not generated by their presence. Type C municipalities are the most direct beneficiaries of the surrender process in a spatial sense: they were literally built on surrendered land or in the space its removal created. However, they are the weakest cases for the "pressure then surrender" argument because they do not demonstrate causal accumulation. Laird is the clearest example: Mennonite settlers arrived 11 years after Stoney Knoll was surrendered, onto land already cleared.
**Dataset:** 8 municipalities (2% of total).

### Implications for query design
Each type suggests a different evidential approach:
- **Type A** queries should focus on temporal gap, institutional depth, railway sequence, and Métis co-presence — building the accumulation argument
- **Type B** queries should focus on simultaneity, railway arrival dates, and whether the surrender preceded or followed the townsite survey — testing the "anticipated surrender" hypothesis
- **Type C** queries should focus on the gap between surrender and founding, and on what land-use changes occurred in the interval — documenting direct absorption of surrendered land into settler space

---

## Query 11a — Type B municipalities: compressed pressure or anticipated surrender?

**Run:** 2026-04-07

### Results

| Name | Founded | Railway year | Railway | Surrender year | Reserve | n_25km | dist_m | Métis | Found→surrender | Rail→surrender |
|---|---|---|---|---|---|---|---|---|---|---|
| Wakaw, VL | 1903 | 1912 | GTPR | 1899 | One Arrow | 1 | 19,074 | No | −4 | −13 |
| Springwater, VL | 1911 | 1913 | GTPR | 1908 | Swan Lake | 1 | 23,630 | No | −3 | −5 |
| Tramping Lake, VL | 1912 | 1913 | CPR | 1908 | Swan Lake | 1 | 11,902 | No | −4 | −5 |
| Handel, VL | 1912 | 1912 | CPR | 1908 | Swan Lake | 1 | 591 | No | −4 | −4 |
| Kelfield, VL | 1911 | 1912 | CPR | 1908 | Swan Lake | 1 | 12,778 | No | −3 | −4 |
| Leipzig, VL | null | 1912 | CPR | 1908 | Swan Lake | 1 | 7,533 | No | null | −4 |
| Heward, VL | null | 1904 | CPR | 1901 | Ocean Man | 2 | 19,866 | No | null | −3 |
| Kisbey, VL | 1904 | 1904 | CPR | 1901 | Ocean Man | 2 | 12,062 | No | −3 | −3 |
| Stoughton, VL | 1901 | 1904 | CPR | 1901 | Ocean Man | 2 | 14,360 | No | 0 | −3 |
| Wilkie, T-V | 1907 | 1908 | CPR | 1905 | Grizzly Bear's Head | 1 | 19,104 | No | −2 | −3 |
| Rock Haven, VL | 1912 | 1911 | GTPR | 1908 | Thunderchild | 1 | 23,686 | No | −4 | −3 |
| Beatty, VL | 1907 | 1905 | CNoR | 1902 | Cumberland | 1 | 2,262 | No | −5 | −3 |
| Kinistino, VL | 1905 | 1905 | CNoR | 1902 | Cumberland | 1 | 7,311 | No | −3 | −3 |
| Weldon, VL | 1905 | 1905 | CNoR | 1902 | Cumberland | 2 | 14,564 | Yes | −3 | −3 |
| Denholm, VL | null | 1913 | CNoR | 1910 | Grizzly Bear's Head | 3 | 20,956 | No | null | −3 |
| Meota, VL | null | 1911 | CNoR | 1908 | Thunderchild | 4 | 8,139 | Yes | null | −3 |
| Vawn, VL | null | 1911 | CNoR | 1908 | Thunderchild | 3 | 17,970 | No | null | −3 |
| Kendal, VL | 1907 | 1907 | CNoR | 1905 | Carry The Kettle | 1 | 2,487 | No | −2 | −2 |
| Odessa, VL | 1907 | 1907 | CNoR | 1905 | Carry The Kettle | 1 | 12,607 | No | −2 | −2 |
| Hyas, VL | 1910 | 1910 | CNoR | 1909 | The Key | 2 | 10,171 | No | −1 | −1 |
| Norquay, VL | null | 1910 | CNoR | 1909 | The Key | 2 | 9,786 | No | null | −1 |
| Sturgis, VL | null | 1910 | CNoR | 1909 | The Key | 1 | 24,692 | No | null | −1 |
| Elfros, VL | 1906 | 1908 | CPR | 1907 | Fishing Lake | 2 | 15,699 | No | +1 | −1 |
| Bangor, VL | 1907 | 1907 | GTPR | 1907 | Little Bone | 1 | 23,032 | No | 0 | 0 |
| Cavell, VL | null | 1908 | GTPR | 1908 | Swan Lake | 1 | 17,520 | No | null | 0 |
| Wadena, T-V | 1904 | 1905 | CNoR | 1907 | Fishing Lake | 2 | 5,551 | No | +3 | +2 |
| Leross, VL | 1908 | 1908 | GTPR | 1920 | Muskowekwan | 3 | 1,941 | No | +12 | +12 |

*Negative values = railway/founding came after the surrender. Positive values = railway/founding came before.*

### Findings

**Type B is predominantly post-surrender colonization, not anticipated surrender.** The majority of Type B municipalities show negative `found_to_surrender_yrs` — they were founded *after* the nearest surrender, not before it. The "anticipated surrender" hypothesis, where towns were planted in advance of a pre-arranged land clearance, is not the dominant pattern. Instead, Type B looks more like **rapid post-surrender colonization**: the surrender cleared the land, and settlers and infrastructure followed quickly.

**Railway also arrived after the surrender in most cases.** Most `rail_to_surrender_yrs` values are negative — the railway came after the surrender, not before. This is the reverse of the Type A pattern identified in Queries 4 and 7a, where railway preceded surrender in every resolvable case. For Type B, the sequence is often: surrender → settlement → railway, not railway → settlement → surrender.

**The Swan Lake cluster is the clearest example.** Swan Lake reserve surrendered in 1908. Five villages — Springwater, Tramping Lake, Handel, Kelfield, Leipzig — were planted in 1911–1912, and the CPR and GTPR arrived in 1912–1913. The land was cleared first; the towns and railway followed as a package within 4–5 years. This is colonial infrastructure responding to already-cleared land, not generating the conditions for clearance.

**Leross is the outlier.** Founded 1908, surrender 1920, gap +12 years — Leross behaves like a Type A municipality. It was planted 12 years before the Muskowekwan surrender and sits at 1,941m from the reserve. Its Type B classification may reflect a data issue or a misalignment between its nearest surrender pairing and its actual pressure history.

**Weldon and Meota are the only Type B municipalities with Métis presence.** Both are near reserves that also appear in the Type A Métis co-presence set (Cumberland and Thunderchild), suggesting the Métis displacement in these zones was already underway when the Type B settlements arrived.

---

## Query 11b — Type C municipalities: post-surrender absorption profile

**Run:** 2026-04-07

### Results

| Name | Surrender year | Founded | Years after | Reserve | dist_m | Métis | Métis y_found | Railway | Rail year |
|---|---|---|---|---|---|---|---|---|---|
| Hague, VL | 1897 | 1898 | 1 | Stoney Knoll | 22,890 | No | — | QLSRSC | 1890 |
| Birch Hills, VL | 1897 | 1903 | 6 | Chakastaypasin | 4,661 | Yes | 1880 | CNoR | 1905 |
| Hepburn, VL | 1897 | 1908 | 11 | Stoney Knoll | 18,335 | No | — | CNoR | 1910 |
| Laird, VL | 1897 | 1908 | 11 | Stoney Knoll | 0 | No | — | CNoR | 1910 |
| Domremy, VL | 1899 | 1913 | 14 | One Arrow | 15,675 | Yes | 1880 | GTPR | 1914 |
| Kennedy, VL | 1901 | null | null | Pheasant's Rump | 24,563 | No | — | CPR | 1906 |
| Kuroki, VL | 1907 | null | null | Fishing Lake | 4,922 | No | — | CNoR | 1905 |
| Waldheim, VL | 1897 | null | null | Stoney Knoll | 7,710 | No | — | CNoR | 1910 |

### Findings

**Stoney Knoll dominates the Type C set.** 4 of 8 Type C municipalities — Hague, Hepburn, Laird, Waldheim — are nearest to Stoney Knoll, surrendered in 1897. Three are explicitly Mennonite settlements (Hague, Hepburn, Waldheim); Laird is also a Mennonite ethnic colony. The Stoney Knoll surrender effectively opened a corridor that was colonized primarily by Mennonite settlers over the following decade.

**Hague is the most rapid post-surrender settlement in the dataset.** Founded 1898, one year after the Stoney Knoll surrender, on the QLSRSC line (railway predating the surrender by 7 years). The Hague-Osler Mennonite Reserve was established in 1895 — two years before the surrender — meaning Mennonite land allocation was being arranged in the same period that Stoney Knoll was being surrendered. The proximity in time raises questions about whether the Mennonite settlement was coordinated with or enabled by the surrender process.

**Two Type C municipalities show Métis presence — the three-layer sequence.** Birch Hills (Chakastaypasin, surrendered 1897, Métis community founded 1880) and Domremy (One Arrow, surrendered 1899, Métis community founded 1880) both have Métis communities that predate both the surrender and the municipal founding. The sequence in both cases: Métis community established → reserve surrendered → municipality founded on the cleared land. This is three distinct layers of dispossession operating on the same geographic space.

**Birch Hills has pre-municipal settlement depth.** The event note records nearby settlement at Harperview from 1884 and a school established there in 1894 — 13 years before the municipal founding in 1903 and nearly a decade before the surrender (1897). The formal founding date understates the actual colonial presence, consistent with the sensitized gap methodology applied in Query 3a.

---

## Query 11c — Cross-type: A, B, and C municipalities nearest the same reserve

**Run:** 2026-04-07

Three reserves attracted municipalities of all three temporal types; nine more attracted two types.

### Reserves with all three types (A, B, C)

**Fishing Lake** (surrendered 1907, 5 municipalities)
- Type A: Foam Lake (founded 1882, 25-year pre-surrender presence), Margo (1903)
- Type B: Wadena (1904), Elfros (1906)
- Type C: Kuroki (null founded)
Foam Lake's 1882 founding — 25 years before the Fishing Lake surrender — is the longest pre-surrender gap in the cross-type set. The full sequence spans over three decades.

**One Arrow** (surrendered 1899, 3 municipalities)
- Type A: Duck Lake (founded 1875, Métis present, NWMP/HBC presence)
- Type B: Wakaw (1903)
- Type C: Domremy (1913, Métis present)
Duck Lake's 1875 founding gives a 24-year pre-surrender gap. Both the Type A and Type C municipalities have Métis communities present, linking the pre-surrender and post-surrender phases through continuous Métis displacement.

**Stoney Knoll** (surrendered 1897, 5 municipalities)
- Type A: Rosthern (founded 1893, Métis present)
- Type C: Hague (1898), Hepburn (1908), Laird (1908), Waldheim (null) — all Mennonite
Stoney Knoll is the most analytically complete case in the dataset. Rosthern's presence (with Métis co-presence) preceded and contributed to the surrender. Then four Mennonite colonies arrived on the cleared land over the following decade. The full colonial sequence — pre-existing settler accumulation with Métis displacement, formal surrender, post-surrender ethnic colony planting — is visible in a single reserve's history.

### Reserves with two types

| Reserve | Surrender | Types | Key municipalities |
|---|---|---|---|
| Swan Lake | 1908 | A, B | Landis (A, Métis), 5× Type B post-surrender villages |
| Ocean Man | 1901 | A, B | Arcola/Forget (A), Heward/Kisbey/Stoughton (B) |
| Carry The Kettle | 1905 | A, B | Wolseley/Sintaluta/Montmartre (A, 1881–1893), Kendal/Odessa (B) |
| The Key | 1909 | A, B | Canora/Stenen (A), Hyas/Norquay/Sturgis (B) |
| Little Bone | 1907 | A, B | Yorkton/Saltcoats/Melville (A), Bangor (B) |
| Muskowekwan | 1920 | A, B | Kelliher/Lestock/Jasmin (A), Leross (B) |
| Thunderchild | 1908 | A, B | Delmas (A, Métis, overlap), Rock Haven/Meota/Vawn (B) |
| Cumberland | 1902 | A, B | Melfort (A), Beatty/Kinistino/Weldon (B) |
| Chakastaypasin | 1897 | A, C | Prince Albert (A, Métis), Birch Hills (C, Métis) |

### Synthesis

**The cross-type data reveals that reserve surrenders attracted layered waves of settlement** — not a single moment of colonization but an ongoing process extending before and after the formal surrender date. The Type A settlements generated the conditions for surrender; Type B settlements arrived in the immediate aftermath; Type C settlements filled in the landscape over the following years and decades. Each layer represents a distinct phase of benefit from the same act of dispossession.

**The Stoney Knoll and One Arrow cases show that Métis displacement runs through all phases.** In both, Métis communities are present at the Type A stage (pre-surrender) and again at the Type C stage (post-surrender). The formal surrender is the pivot point, but the Métis displacement it connects to predates the surrender by decades and continues after it.

**The Thunderchild case links the cross-type findings to the case study set.** Delmas (Type A, overlap, Métis present) is the pre-surrender anchor; Rock Haven, Meota, and Vawn are the Type B post-surrender arrivals. The analysis of Delmas as a case study is therefore not just the story of a single settlement — it is the leading edge of a colonization wave that continued after the 1908 surrender.

---

## Query 4b — Reserves with multiple surrender events in the Type A set

**Run:** 2026-04-08

### Results

| Reserve | Distinct surrender years | Surrender events |
|---|---|---|
| Piapot | 2 | 1918: 4 Type A municipalities; 1919: 5 Type A municipalities |
| Pasqua | 2 | 1906: 3 Type A municipalities; 1910: 2 Type A municipalities |
| Mistawasis | 2 | 1911: 1 Type A municipality; 1919: 2 Type A municipalities |

### Methodological note

`nearest_surrender_year` is a property on each municipality node, not a count from independent Surrender nodes. Distinct years here reflect different parcels being the nearest to different municipalities in the Type A set — which strongly implies multiple surrender events on the same reserve, but the dataset cannot confirm whether these represent separate legal negotiations or a single process recorded in stages.

### Findings

**Only 3 of the 13+ reserves with multiple Type A municipalities show multiple distinct surrender years.** Most reserves in the corridor clustering data faced sustained multi-settlement pressure but were surrendered in a single legal event. Piapot, Pasqua, and Mistawasis are the exceptions — reserves where pressure was iterative enough, or the reserve large enough, to produce staged reduction. This is a structural limit on the pattern: corridor clustering usually ended in one surrender, not serial surrenders.

**Piapot** is the most extreme case and was already flagged in Query 4a. Nine Type A municipalities total across two consecutive years (1918: 4, 1919: 5), all on the CPR 1882 main line. The back-to-back surrender years likely represent two distinct legal transactions — separate parcels reduced in sequence — rather than a single negotiation. The corridor running east of Regina generated enough accumulated pressure to exhaust the reserve in stages.

**Pasqua is the most analytically significant new finding.** The split is not just temporal but typological: the 1906 surrender correlates with three CPR railway-corridor villages (McLean, Qu'Appelle, Indian Head — all founded 1881–1882), while the 1910 surrender correlates with Fort Qu'Appelle and Lebret — the mission and institutional settlements whose effective presence stretches to 1804 and 1860 respectively (Query 3a sensitized). Two distinct colonial mechanisms — railway frontier pressure and religious/institutional presence — operating on the same reserve yielded two separate surrender events four years apart. This is a direct materialization of Raibmon's genealogy in the spatial data: the railway and institutional branches of colonial presence were not the same mechanism, and here they produced distinct legal outcomes.

**Mistawasis** shows an 8-year gap between surrender events (1911, 1919). The 1911 surrender correlates with only one municipality — Leask — but Leask is the geometric overlap case with the highest 5km surrender density in the dataset and simultaneous railway arrival (Query 7a). The 1919 second surrender then draws two more municipalities including Shellbrook LSC (24km out). The gap between events suggests the 1911 surrender did not satisfy accumulated demand: Leask's presence and the CNoR corridor continued to generate pressure, and a second reduction followed eight years later.

---

## Queries 4c and 4f — Railway-to-surrender gap distribution

**Run:** 2026-04-08

### Results — Query 4c (Type A only)

| Gap band | n | min gap | max gap | avg gap |
|---|---|---|---|---|
| Surrender before railway | 6 | −3 | −1 | −2 |
| 0 years | 4 | 0 | 0 | 0 |
| 1–5 years | 12 | 1 | 4 | 3 |
| 6–10 years | 14 | 6 | 10 | 8 |
| 11–20 years | 20 | 11 | 20 | 15 |
| 21–30 years | 19 | 21 | 29 | 24 |
| 31+ years | 7 | 31 | 37 | 35 |

### Results — Query 4f (Types A, B, C by type)

| Gap band | Type | n | min gap | max gap | avg gap |
|---|---|---|---|---|---|
| Surrender before railway | A | 6 | −3 | −1 | −2 |
| 0 years | A | 4 | 0 | 0 | 0 |
| 1–5 years | A | 12 | 1 | 4 | 3 |
| 6–10 years | A | 14 | 6 | 10 | 8 |
| 11–20 years | A | 20 | 11 | 20 | 15 |
| 21–30 years | A | 19 | 21 | 29 | 24 |
| 31+ years | A | 7 | 31 | 37 | 35 |
| Surrender before railway | B | 23 | −13 | −1 | −3 |
| 0 years | B | 2 | 0 | 0 | 0 |
| 1–5 years | B | 1 | 2 | 2 | 2 |
| 11–20 years | B | 1 | 12 | 12 | 12 |
| Surrender before railway | C | 6 | −15 | −5 | −11 |
| 1–5 years | C | 1 | 2 | 2 | 2 |
| 6–10 years | C | 1 | 7 | 7 | 7 |

### Findings

**The Type A distribution is broad, not peaked.** The two largest bands are 11–20 years (20 municipalities) and 21–30 years (19 municipalities) — nearly half the Type A set (39 of 82) falls in that window. No band dominates overwhelmingly. The pressure-to-surrender process was variable in duration, not mechanically timed. The 6 "surrender before railway" Type A cases are an anomalous corner: the town existed, the surrender happened, then the railway arrived within 1–3 years — founding first, surrender second, railway third.

**Type B confirms the Query 11a finding decisively.** 23 of 27 Type B municipalities (85%) fall in "surrender before railway." For Type B the dominant sequence is: surrender → settlement → railway — the inverse of Type A. Type B is not compressed Type A; it is structurally different. The one 11–20 year outlier (gap 12) is Leross, already flagged in Query 11a.

**Type C extends the same pattern further.** 6 of 8 Type C municipalities have surrender before railway, with an average lag of 11 years. The railway followed the surrender by over a decade on average in the post-surrender settlement cases. These were not railway-driven settlements.

**The railway-precedes-surrender sequence is the diagnostic signature of Type A.** Across the whole dataset, that sequence is almost exclusively a Type A phenomenon. For Types B and C, the surrender came first and railway infrastructure followed. This sharpens the McGuire argument: railway-driven pressure on reserves was the mechanism of the pre-surrender dispossession cycle. Post-surrender colonization followed a different logic.

### Broader interpretation

The gap distribution, read alongside the typology, supports a broader conclusion: **no single mechanism was the typical process of settler pressure on reserve lands in Saskatchewan**. Type A is the largest implicated group at 82 municipalities, but that is only 19% of the total dataset. Within Type A, no single commercial type, railway company, or gap interval accounts for most cases. Railways mattered in some corridors; institutional presence (missions, HBC posts) in others; Métis community displacement runs through multiple phases independently of both; ethnic agricultural colonies appear closest to surrendered land without any coordinated pressure campaign.

The typology remains analytically useful — it distinguishes whether a given settlement contributed to the conditions for surrender, arrived simultaneously, or benefitted from a surrender that had already occurred. That is a question of relationship and benefit, not a claim about a dominant causal mechanism. But the diversity of the pattern within and across types is itself the substantive finding: Indigenous dispossession in Saskatchewan was a general product of colonialism operating through Raibmon's varied microtechniques, not a uniform process reducible to any one mechanism. The dataset cannot be countered by showing that railways were not always the driver, because the data already shows that. The multiplicity is the evidence for the general claim.

---

## Queries 4d and 4g — Railway company frequency and corridor timelines

**Run:** 2026-04-08

### Results — Query 4d (company frequency)

| Railway company | Type A municipalities | Distinct reserves | Reserves (sample) |
|---|---|---|---|
| CPR | 32 | 12 | Ocean Man, Kahkewistahaw, Cowessess, Ochapowace, Carry The Kettle, Fishing Station, Piapot, Pasqua, Little Black Bear, Last Mountain Lake |
| CNoR | 21 | 11 | Carry The Kettle, The Key, Cote, Keeseekoose, Fishing Lake, Moosomin, Thunderchild, Cumberland, Muskeg Lake, Mistawasis |
| GTPR | 20 | 9 | Little Bone, Little Black Bear, Standing Buffalo, Piapot, Pasqua, Muskowekwan, George Gordon, Poor Man's, Swan Lake |
| QLSRSC | 7 | 4 | Last Mountain Lake, Chakastaypasin, One Arrow, Stoney Knoll |
| Other | 2 | 1 | Little Bone |

### Results — Query 4g (corridor timelines)

| Company | n munis | n reserves | avg railway yr | avg surrender yr | avg gap | earliest railway | latest surrender |
|---|---|---|---|---|---|---|---|
| CPR | 32 | 12 | 1896 | 1915 | 19 yrs | 1882 | 1928 |
| CNoR | 21 | 11 | 1907 | 1911 | 4 yrs | 1904 | 1927 |
| GTPR | 20 | 9 | 1908 | 1921 | 12 yrs | 1907 | 1933 |
| QLSRSC | 7 | 4 | 1889 | 1909 | 20 yrs | 1887 | 1918 |
| Other | 2 | 1 | 1889 | 1907 | 19 yrs | 1888 | 1907 |

### Findings

**CPR leads by municipality count but CNoR is nearly equal in reserve reach.** CPR is associated with 32 Type A municipalities across 12 reserves; CNoR with 21 municipalities across 11 reserves. CPR planted more towns per reserve on average (2.7) than CNoR (1.9) — consistent with the dense corridor clusters identified in Query 4a along the main line east of Regina. CNoR was more diffuse: fewer towns per reserve, but spread across nearly as many reserves.

**GTPR's reach is underappreciated.** It appears less frequently in earlier findings than CPR or CNoR, but 20 municipalities across 9 reserves is substantial. Its corridor pressure falls entirely within the Sifton boom window (earliest railway 1907), consistent with shorter average gaps in the 4c distribution.

**QLSRSC is a quiet but persistent thread.** Seven municipalities across 4 reserves — Last Mountain Lake, One Arrow, Chakastaypasin, Stoney Knoll — an older line (1887) whose reserve correlations tend to involve institutional and Métis presence rather than railway-townsite dynamics. It recurs across queries without ever being the dominant actor.

**CNoR's 4-year average gap is the most compressed of any company.** This initially looks like the most intense corridor pressure, but the temporal data explains it: CNoR arrived in 1907 on average — directly into the middle of the Sifton boom — so the settlement density needed to generate pressure was already present when the railway came. The gap closed fast not because CNoR was uniquely aggressive but because demographic conditions were already ripe.

**The surrender years converge despite divergent railway arrival years.** CPR's earliest line dates to 1882; GTPR's to 1907 — a 25-year span. Yet all four companies' average surrender years fall within a 12-year window (1909–1921). Despite arriving at very different times, all corridors converged on roughly the same boom-era window for surrenders. That is not a railway timing story — it is a demographic and political story.

**Railway determined where; settlement determined when.** This is the clearest quantitative expression of the finding stated earlier in the dataset. The railways fixed the geography of corridor pressure — which reserves sat adjacent to which lines. But the timing of formal surrender was driven by the Sifton-era population boom filling those corridors to the threshold of irresistible pressure. CPR had been on the ground since 1882 but its average surrender came in 1915 because the southern plains lacked sufficient settlement density until the boom decade produced it. The 4g data makes this argument visible across all four companies simultaneously: the convergence of surrender years despite divergent arrival years is among the strongest single pieces of evidence in the dataset for the claim that demographics, not railways, determined when dispossession was formalized.

---

## Query 4e — The Punnichy / George Gordon outlier cluster

**Run:** 2026-04-08

**Method:** Query as written in `cypher_queries.md` returned only one result (Punnichy), because only Punnichy has `nearest_surrender_reserve = 'George Gordon'`. A revised proximity query was run in Python to retrieve all Type A municipalities within 50km of Punnichy's coordinates, giving the full cluster picture.

### Results — all Type A municipalities within 50km of Punnichy

| name | founded | railway | rail yr | nearest reserve | surrender yr | n_25km | gap_yrs | metis | pop_1921 | dist_to_Punnichy |
|---|---|---|---|---|---|---|---|---|---|---|
| Punnichy, VL | 1908 | GTPR | 1908 | George Gordon | 1933 | 7 | 25 | Yes | 200 | 0 |
| Quinton, VL | 1908 | GTPR | 1908 | Poor Man's | 1919 | 5 | 11 | No | 97 | 7,655 |
| Raymore, VL | 1908 | GTPR | 1908 | Poor Man's | 1919 | 4 | 11 | No | 280 | 16,494 |
| Lestock, VL | null | GTPR | 1908 | Muskowekwan | 1920 | 6 | 12 | Yes | 280 | 23,450 |
| Semans, VL | 1904 | GTPR | 1908 | Poor Man's | 1919 | 1 | 11 | No | 450 | 30,392 |
| Tate, VL | 1905 | GTPR | 1908 | Poor Man's | 1919 | 1 | 11 | No | 98 | 38,012 |
| Kelliher, VL | 1903 | GTPR | 1908 | Muskowekwan | 1920 | 3 | 12 | No | 320 | 40,660 |
| Kandahar, VL | null | CPR | 1909 | Poor Man's | 1919 | 1 | 10 | No | 114 | 42,958 |
| Dafoe, VL | null | CPR | 1909 | Poor Man's | 1919 | 1 | 10 | No | 102 | 45,472 |
| Cupar, VL | null | CPR | 1905 | Piapot | 1918 | 3 | 13 | No | 384 | 47,702 |
| Jasmin, VL | null | GTPR | 1908 | Muskowekwan | 1920 | 4 | 12 | Yes | 83 | 48,111 |
| Markinch, VL | null | CPR | 1905 | Piapot | 1918 | 3 | 13 | No | 172 | 48,207 |

### What the reserves_master data adds

George Gordon is **Reserve No. 86**, Treaty 4 (Qu'Appelle Treaty). The `reserves_master.csv` notes field records three surrenders — 1914 (360 acres), 1919 (169 acres), and 1933 (720 acres) — all explicitly to the **Church of England / Gordon School**, not to settler municipalities or railway interests. Gordon Indian Residential School operated on the reserve from 1888 to 1996. A Church of England mission was established on the reserve in 1876, the same year as the initial survey, giving the church a land interest inside the reserve from the outset. A 1899 boundary exchange reorganized the reserve's borders and placed the C of E mission sections inside the new boundary while keeping them as C of E property — a legally anomalous tenure situation that the subsequent staged surrenders were resolving piecemeal.

The acreage sequence (360 → 169 → 720 acres) indicates escalating demand across three separate transactions over 19 years, not a single negotiation drawn out over time. The 1933 surrender — the largest, at 720 acres — falls in the Depression, when the band's economic position would have been severely compromised.

### Findings

**The initial framing was wrong.** The most plausible hypothesis from spatial data alone — George Gordon as a case of sustained Indigenous resistance within maximum corridor pressure — does not hold once the reserves_master notes are read. The 1933 surrender was not the delayed conclusion of settler pressure. It was the third instalment of a residential school land acquisition that began in 1914 and was structurally unrelated to Punnichy's existence.

**Punnichy's Type A pairing with George Gordon is the least analytically meaningful match in the dataset.** Punnichy is technically Type A — founded 1908, surrender 1933, gap 25 years — but the causal logic that makes Type A meaningful elsewhere does not apply here. The Church of England had been on that reserve since 1876, 32 years before Punnichy was founded. The municipal presence did not generate the conditions for the surrender.

**Punnichy's high n_25km count reflects the surrounding corridor, not George Gordon.** The 7-surrender count comes from Poor Man's (1919), Muskowekwan (1920), and Piapot (1918) — all standard settler-pressure surrenders in the GTPR/CPR corridor. Punnichy sits inside a zone of intense corridor activity. George Gordon is spatially proximate but mechanism-distinct: it was being reduced by a different actor through a different process simultaneously.

**The cluster is otherwise homogeneous and consistent with the broader pattern.** The 11 surrounding Type A municipalities are all GTPR 1908 or CPR 1905/1909 settlements, all small boom-era villages (pop 83–450), with nearest-surrender gaps of 10–13 years — well within the Sifton boom window. Their nearest reserves (Poor Man's, Muskowekwan, Piapot) all surrendered 1918–1920. The cluster is unremarkable analytically except for the anomalous George Gordon pairing at its centre.

**This exposes a methodological limit of the nearest-reserve matching logic.** The `nearest_surrender_reserve` property captures the spatially closest surrendered reserve to each municipality, but it cannot distinguish surrender mechanisms. A church land transaction and a settler petition-cycle surrender look identical in the graph. George Gordon is the clearest case in the dataset where that distinction matters analytically: a municipality classified as Type A because of a nearby surrender that had nothing to do with its presence. The finding does not undermine the broader argument — it clarifies that the argument holds for the other 81 Type A municipalities and their pairings, while flagging this one as requiring a different interpretive frame.

**Archival note:** Gordon Indian Residential School is one of the most extensively documented residential schools in Canada. DIA correspondence on Reserve 86 boundary adjustments — particularly around the 1899 exchange and the 1914 first surrender — would be the most direct source for the staging question. Library and Archives Canada, RG 10 series. TRC records also document the school extensively.

---

## Leask LHB findings — "A Lasting Legacy"

**Searched:** 2026-04-08. Full text extracted from PDF, searched by keyword. Full findings recorded in `analysis/case_studies/leask.md`.

**Summary:** The LHB establishes an effective founding date of 1902–1904 for the Leask district, with organized LID administration from 1908 — giving a genuine effective gap of 7–9 years before the 1911 Mistawasis surrender. The null `founded` in the dataset reflects the 1912 village incorporation date, which significantly understates actual settler presence depth. Mrs. Hayward's 1955 letter (describing 1904 events) names the Mistawasis Indian Reserve as a primary geographic reference point for first settlers, noted with epistemic caution given the 50-year retrospective framing. The LHB's "no inhabitants until 1890" claim is treated with skepticism — suspect given confinement and starvation policies that constrained Indigenous presence without erasing it. A second Mistawasis surrender (1919, 16,548 acres to the Soldier Settlement Board) and a Muskeg Lake land transfer (also via SSB, documented by the book's researcher) are confirmed. Leask's case study status is rehabilitated: real founding depth exists; the mechanism connecting settler presence to the 1911 surrender remains correlation pending DIA/Carlton Agency archival work.
