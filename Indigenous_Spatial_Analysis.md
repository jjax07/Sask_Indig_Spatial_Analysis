# Indigenous Spatial Analysis: Reserves, Métis Communities, and Urban Space in Saskatchewan, 1921

## Research Context

Subproject of *Saskatchewan Urban Settlements, 1921* (Jim Clifford / Cheryl Troupe, University of Saskatchewan). Companion to the StoryMap "Mapping Settler Colonialism in Saskatchewan": https://storymaps.arcgis.com/stories/8288eb9615484e708922e81411e63936/

**Primary working directory:** `/Users/baebot/Documents/ClaudeCode/Reserves_Urban_Spaces/`

## Research Questions

This subproject examines the spatial relationships between:
1. First Nations reserve land surrenders (1870s–1933)
2. Métis community presence and displacement
3. The 429 incorporated urban municipalities of Saskatchewan as of 1921

**Core argument:** Urban municipalities did not simply occupy empty land — they grew on or adjacent to Indigenous spaces that were systematically reduced through surrender, coercion, and encroachment. The temporal sequence matters: in many cases settler pressure preceded and drove formal surrender rather than following it.

**Theoretical frame:**
- Paige Raibmon's lens on colonial dispossession — bottom-up settler pressure, ideological privileging of "productive" farming, government accommodation of fait accompli
- Bill Waiser, *Cheated: First Nations Land Surrenders on the Prairies 1896–1911* — the mechanics of surrender under the Laurier government
- Peggy Martin-McGuire, *First Nation Land Surrenders on the Prairies, 1896–1911* (Indian Claims Commission, 1998) — the primary comparative study of all 25 prairie surrenders in this period; confirms and deepens the Waiser frame with archival citations
- Source approach: settler perspectives in newspapers and local histories alongside government policy record; look for evidence of settlers farming reserve land before formal surrender

**Key case studies to pursue:** Kamsack (most obvious — near Cote, Keeseekoose, Key First Nation reserves), Regina, North Battleford, Prince Albert, Broadview. Any municipality with reserves in proximity.

---

## Policy Mechanisms — Martin-McGuire Confirmed Findings

_Peggy Martin-McGuire, *First Nation Land Surrenders on the Prairies, 1896–1911* (Indian Claims Commission, 1998). Findings confirmed with page citations from Executive Summary and chapters._

### Frank Oliver quotes (1906) — on settler priority

The 1906 *Indian Act* amendment raising the distribution ceiling from 10% to 50% was explicitly justified by Oliver as an inducement to surrender (Executive Summary, pp. xxi–xxii):

> "Of course, the Indian Department or the government have no right or authority to interfere with their holding, although it is in excess of the amount contemplated by the treaty. The only way they can be induced to release their holding is by purchase, as they are proprietors in every sense. . . . The present conditions, when land is in demand, when towns are building up in many cases in close proximity to these reserves is certainly one which demands attention, and the purpose of this Bill is that it shall be given attention."

> "of course the interests of the people must come first and if it becomes a question between the Indians and the whites, the interests of the whites will have to be provided for."

### Three mechanisms by which railway development drove surrender demand (Ch. 7)

1. **Right-of-way split:** A railway severed the reserve, leading officials to conclude one portion should be surrendered (e.g., Peigan)
2. **Station grounds → townsite:** Railway company wanted a surrender for station grounds, which led to an initiative to surrender a larger area for townsite development (e.g., **Cote/Kamsack**, The Pas, Fishing Lake, Moosomin)
3. **Proximity raised market value:** The line simply made reserve land more valuable to outsiders and speculators (e.g., Crooked Lakes/**Cowessess**, Michel, Pasqua, **Muscowpetung**, Moose Mountain, Bobtail)

This taxonomy directly supports the Type A temporal classification used in this project: in all three cases, the railway precedes or accompanies the surrender pressure.

### "Excess lands" rationale — applied in at least 10 of 25 surrenders (Executive Summary, pp. xxvii–xxix)

The rationale originated with Hayter Reed's peasant farming policy (1888), which withheld machinery and allotted land individually, creating an appearance of "surplus." As bands recovered agricultural productivity in the post-Reed era, the same rationale was applied against them — precisely when reserves were most economically active, not least.

Critically: the "excess lands" argument was deployed when bands were prosperous and outsiders perceived the land as economically valuable. Examples confirmed: Cote, Moosomin/Thunderchild, Mistawasis, Samson and Bobtail, Roseau River, Crooked Lakes, Michel, Moose Mountain, Stony Plain/Enoch.

### 1911 Indian Act amendment — expropriation without consent (Executive Summary, p. xxiii)

> "In a 1911 amendment that directly contravened the treaties, the *Indian Act* allowed the government to take reserve land without consent, where the reserve was in or near a town of over 8,000 people, or where the land was needed for public purposes."

Applicable to all case studies involving urban municipalities that exceeded 8,000 population by 1911 (Regina: 34,432 in 1921; Prince Albert: 7,558 in 1921 — likely borderline).

### Senior officials speculating in surrendered land

Smart and Pedley (successive DSGIAs 1897–1913) conspired to purchase land from surrendered reserves including Pheasant's Rump, Ocean Man, Chacastapaysin, Cumberland 100, and Enoch. The Ferguson Commission (1915) found this to be a conflict of interest. Liberal MP T.O. Davis (Prince Albert) also acquired Chacastapaysin lands, transferred to Fenton Farms Ltd. in 1917. The Kamsack Land Company (1908) included the Indian Agent who took the Cote surrender and the physician who had advocated it.

---

## Data Inventory

### 1. First Nations Reserves (`Sask_Reserves/`)

| File | Type | Features | Description |
|------|------|----------|-------------|
| `Reserves_Initial_Survey.geojson` | Polygon | — | Original reserve extents from initial DLS surveys, 1874–1906. Fields: `TCPUID_CSD_1921`, `Reserve_Name`, `Reserve_Number`, `Year_Established`, `Treaty`, `First_Map_Year`. Links to 1921 census via TCPUID. |
| `SK_ReserveSurrenders_1933.geojson` | Polygon | 54 | Surrendered/taken land parcels as of 1933. Rich attributes: `YEAR_SURR`, `ACRES_SURR`, `RESERVE_NU`, `RSRVE_NAME`, `ORIG_ACRE`, population series 1881–1931, qualitative `Notes` on circumstances of surrender. **Core layer for dispossession analysis.** |
| `Reserve_Boundary_Changes.geojson` | Polygon | 20 | Documented boundary corrections and resurveys. Fields: `RSRVE_NO`, `RSRVE_NAME`, `YEAR`, `Notes`. |
| `Reserves_CD_1921.geojson` | Polygon | 144 | Reserve boundaries aggregated by census division as of 1921. Fields: `TCPUID_CSD_1921`, `Name_CD_1921`, `Name_CSD_1921`. |
| `File_Hills_Colony.geojson` | Polygon | 2 | File Hills Farm Colony on Peepeekisis Reserve, surveyed 1901/02 and 1906. Pre-carved-out case study. |
| `SK_Reserves_In_FeaturesToJSO.geojson` | Polygon | 128 | Reserve geometries with minimal attributes (FID, UNIQUE_ID only). Likely the full reserve polygon set; needs attribute join. |
| `Sask_Reserves_1931.xlsx` | Table | 113 reserves | Master attribute table. Key columns: `UNIQUE_ID`, `RSRV_NAME`, `TREATY_No.`, `YEAR_TS` (treaty signed), `YEAR_IS` (initial survey), `ORIG_ACRE`, `ACRES_1902`, `ACRES_1913`, surrender acreage by individual year (`SURR_1877` through `SURR_1933`), population 1881–1931, `ETHNO_GROUP`, `Notes`, `Data_Certainty`. |
| `SK_Reserves_Table_1.xls` / `_Table_2.xls` | Table | — | Legacy attribute tables for reserve layers; field names include `YEAR_SURVEYED`, `RESERVE_NO`, `UNIQUE_ID`. |
| `SK_Reserves_Initial_Table.csv` | Table | 128 | ID/UNIQUE_ID mapping for reserve geometries. |
| `SaskGrid_2021_Township.geojson` | Polygon | — | Saskatchewan DLS township grid (2021). For georeferencing. |
| `SaskGrid_2021_Section.geojson` | Polygon | — | Saskatchewan DLS section grid (2021). For georeferencing. |
| `SaskGrid_2021_Township_Table.csv` | Table | 7,674 | Township/range/meridian codes. |
| `SaskGrid_2021_Section.csv` | Table | 249,196 | Section-level DLS codes. |
| `Sask_Reserves_1931_Abbreviations.docx` | Doc | — | Data dictionary for abbreviations used in the reserves table. |

**Join key across reserve files:** `UNIQUE_ID` (format: `PRQA160`, `PRF114`, etc.)

---

### 2. Métis Communities (`SK_Metis_Communities/`)

| File | Type | Features | Description |
|------|------|----------|-------------|
| `SK_Metis_Communities.geojson` | Point | 42 | Primary community layer (georeferenced subset). Fields: `UNIQUE_ID`, `Name`, `NoteType`. |
| `Metis_Community.geojson` | Point | 42 | Duplicate of above with full (non-truncated) field names. Same 42 records. |
| `Metis_Farms.geojson` | Polygon | 9 | Farm colony extents: Green Lake, Baljennie, Duck Lake, Glen Mary, Lestock, Crescent Lake, Crooked Lake, Lebret, Willow Bunch Lacerte Co-op. |
| `Metis_Hivernant.geojson` | Point | 17 | Wintering sites (hivernants). |
| `Metis_RoadAllowance.geojson` | Point | 11 | Road allowance communities. |
| `Forts.geojson` | Point | 9 | Fur trade / HBC fort locations. |
| `Métis_Communities.xlsx` | Table | 113 | **Master table — contains temporal data absent from geojson exports.** Fields: `UNIQUE_ID`, `NAME`, `ALT_NAME`, `1901_Census_Name`, `LOCATION`, `TYPE`, `Y_FOUND`, `Y_DEPART`, `LEADERSHIP`, `SURNAMES`, `LAND_LOC_1/2/3`, `POP_1860`, `POP_1880`, `POP_1900`, `POP_1921_CSD`, `POP_1940`, `NOTES`, `SOURCE`. |
| `Métis_Communities_Research (1).docx` | Doc | 2,572 paragraphs | Detailed narrative research notes by community with citations, family histories, and temporal markers. 30MB. Query by community name. |
| `Métis_Communities_Bibliography (1).docx` | Doc | — | 142 sources: books, articles, GDI oral history interviews, theses. |

**Important notes:**
- 113 communities in the xlsx; only 42 are georeferenced in the geojson. 71 communities lack map coordinates as of the last ArcGIS export.
- `Y_FOUND` and `Y_DEPART` dates are approximate; wintering sites have the most precision per the methodology notes.
- Road allowance communities are the most data-sparse category.
- Join key: `UNIQUE_ID` (format: `MSC2025Ax`)
- `SK_Metis_Communities` and `Metis_Community` are effectively duplicates — use `Metis_Community` for full field names.

**Community types in xlsx:** Community, Wintering Site, Métis Farm, Road Allowance, Post

---

### 3. Urban Municipalities (`Urban_Munis/`)

| File | Type | Features | Description |
|------|------|----------|-------------|
| `Sask_1921_Urban_Muni_Full.geojson` | Polygon | 810 | Full 1921 Saskatchewan census CSD layer — includes urban municipalities, rural municipalities, homesteads, and other CSDs. Must be filtered to the 429 urban municipalities. Key fields: `TCPUID_CSD_1921` (join key to Neo4j), `Name_CSD_1921`, `CSD_TYPE`, `POP_TOT_1921`, religious affiliation counts, 216 additional census fields. |
| `Sask1921Full.lyrx` | Layer file | — | ArcGIS layer definition (symbology/source pointer). Not a data file. |

**Filter strategy:** Use `TCPUID_CSD_1921` matched against the 429 known TCPUIDs from Neo4j, or filter by `CSD_TYPE` to urban types (Village, Town, City, etc.).

---

## Analysis Plan (Scoped)

**Out of scope (deferred):** David Allen's homestead records layer — incomplete provincial coverage; relevance depends on how this analysis develops.

### Phase 1 — Spatial Proximity Analysis
- Filter urban municipality polygons to 429 settlements
- For each surrendered reserve parcel (`SK_ReserveSurrenders_1933.geojson`): compute distance to nearest urban municipality boundary
- Flag municipalities within defined thresholds (e.g., 5km, 10km, 25km) of surrendered land
- Cross-reference surrender year (`YEAR_SURR`) with municipal incorporation year (from Neo4j `founded` field)
- Identify cases where surrender postdated municipal founding — potential "pressure then surrender" sequence

### Phase 2 — Temporal Sequencing
- Use `Sask_Reserves_1931.xlsx` year-by-year surrender columns to reconstruct timeline of reserve reduction for each affected reserve
- Compare with municipal growth trajectory (population at census dates, railway arrival, commercial tier)
- Identify cases of pre-surrender settler encroachment suggested by rapid municipal growth adjacent to reserves

### Phase 3 — Métis Overlap
- Join `Métis_Communities.xlsx` to georeferenced points via `UNIQUE_ID`
- Compare `Y_FOUND` / `Y_DEPART` dates with municipal incorporation dates for co-located communities (Saskatoon, Regina, Moose Jaw, Prince Albert, Battleford, Estevan all appear in both datasets)
- Road allowance communities as evidence of displacement into marginal Crown land

### Phase 4 — Case Studies
Priority cases for qualitative follow-up in corpus (local histories, newspapers) — expanded to 7 following Phase 1–3 results review:
1. **Kamsack** — direct geometric overlap with Cote reserve; surrender notes explicitly name Kamsack as driver
2. **Broadview** — largest pre-emptive temporal gap (+25–37 yrs); 5 reserves within 25 km; railway and founding both 1882
3. **North Battleford** — 7 reserves within 25 km; Métis community (Battleford) predated municipality by 7 years
4. **Prince Albert** — Métis community predated municipality by 23 years (founded 1862, muni 1885)
5. **Regina** — 36-year gap between founding (1882) and Piapot surrender (1919); long-established pressure argument
6. **Duck Lake** — Type A against Stoney Knoll (1877, earliest surrender in dataset); Métis community 1870; 1885 Resistance site
7. **Fort Qu'Appelle** — clearest documented Métis displacement arc: community 1870, muni 1880, Y_DEPART 1950

For each: query `Métis_Communities_Research (1).docx` and the graphrag corpus for settler-perspective accounts of land use, encroachment, and the period around formal surrender.

---

## Synthesis — How Phases 1–4 and McGuire Fit Together

The quantitative phases establish the structural pattern; McGuire and the case study record fill in the mechanism — specifically the urban-commercial side of it.

**Phase 1 (spatial proximity)** shows that surrendered reserves cluster near urban municipalities and rail lines. This is the *what*. McGuire's three-mechanism railway taxonomy gives it a causal spine: railways generated townsite demand (Type 2, e.g., Kamsack/Cote) or raised land market value that attracted speculation (Type 3, e.g., Broadview/Cowessess, Regina/Muscowpetung). The rail arrival dates in the spatial data now have a documented demand chain behind them.

**Phase 2 (temporal sequencing)** classifies most cases as Type A — municipality predated surrender. The multi-year gaps are not absence of evidence; McGuire's archival record shows they are filled by documented petition cycles. Broadview's 25-year gap (1882–1907) is 1885, 1886, 1891, 1899, 1902, 1904, then surrender. The gap *is* the pressure.

**The urban-commercial network is the analytical core.** What the spatial and temporal data cannot show on their own is that the pressure was organized, town-based, and commercially motivated. McGuire makes this visible:
- Settler petitions came from named town residents and their MPs (Broadview, Moosomin)
- Land companies buying surrendered land were composed of town-based actors — local physicians, Indian agents, school principals, Yorkton realtors (Kamsack Land Company)
- The same individual (Agent Blewett) took the Cote surrenders *and* was a founding director of the company that bought the land, *and* later triggered The Key 1909 surrender
- Urban newspapers (Winnipeg Free Press) reported reserve openings as fait accompli before formal process — settler anticipation generating settler pressure

**What remains (Phase 5):** The spatial pattern and policy record are established. What is missing is the settler-perspective voice from within the towns — local newspaper accounts, booster literature, petitions in the graphrag corpus. That is where the bottom-up urban experience becomes legible.

---

## Status

- [x] Data inventory complete
- [x] Export verification complete (Sask_Reserves, SK_Metis_Communities, Urban_Munis)
- [x] Repositories initialized: GitHub `jjax07/Sask_Indig_Spatial_Analysis`, GitLab `jjack07/sask_indig_spatial_analysis`
- [x] Implementation plan written (`plan.md`)
- [x] Phase 0 — Data preparation complete (`analysis/00_prepare_data.py`)
- [x] Phase 1 — Spatial proximity analysis complete (`analysis/01_spatial_proximity.py`)
- [x] Phase 2 — Temporal sequencing analysis complete (`analysis/02_temporal_sequencing.py`)
- [x] Phase 3 — Métis overlap analysis complete (`analysis/03_metis_overlap.py`)
- [x] Phase 4 — Case study builder complete (`analysis/04_case_studies.py`, profiles in `analysis/case_studies/`)
- [x] Phase 5 — Neo4j enrichment complete (`analysis/05_neo4j_enrichment.py`, log in `analysis/05_enrichment_log.xlsx`)
- [ ] Case study corpus queries (graphrag / local histories)
