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
- Source approach: settler perspectives in newspapers and local histories alongside government policy record; look for evidence of settlers farming reserve land before formal surrender

**Key case studies to pursue:** Kamsack (most obvious — near Cote, Keeseekoose, Key First Nation reserves), Regina, North Battleford, Prince Albert, Broadview. Any municipality with reserves in proximity.

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
Priority cases for qualitative follow-up in corpus (local histories, newspapers):
1. **Kamsack** — near Cote, Keeseekoose, Key First Nation reserves
2. **Regina** — Métis community presence + reserve proximity
3. **North Battleford** — reserve adjacency + Métis communities at Battleford/Bresaylor
4. **Prince Albert** — major centre with Métis presence
5. **Broadview** — reserve proximity

For each: query `Métis_Communities_Research (1).docx` and the graphrag corpus for settler-perspective accounts of land use, encroachment, and the period around formal surrender.

---

## Status

- [x] Data inventory complete
- [x] Export verification complete (Sask_Reserves, SK_Metis_Communities, Urban_Munis)
- [ ] Spatial analysis script
- [ ] Temporal sequencing analysis
- [ ] Case study corpus queries
