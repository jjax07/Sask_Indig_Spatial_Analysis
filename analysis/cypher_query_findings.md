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
