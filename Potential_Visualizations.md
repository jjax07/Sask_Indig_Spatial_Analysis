# Potential Visualizations

Assessment of which findings from the reserve surrender analysis and census synthesis are map-ready with data as it currently stands, versus which would require significant design work to be visually legible.

---

## Tier 1 — Map-ready now

These findings have inherently spatial relationships that would be visually obvious with minimal design work.

### 1. Geometric overlap cases — municipal polygons over surrendered reserve land

**What it shows:** The 6 municipalities (Kamsack, Delmas, Leask, Lestock, Regina Beach, Laird) whose 1921 polygon boundaries directly overlap with surrendered reserve land.

**Layers needed:**
- 1921 municipal polygon boundaries
- Reserve boundaries (pre-surrender extent)
- Surrendered parcel polygons
- Métis community locations (where present)
- Railway lines

**Why it works:** The overlap is a direct spatial relationship requiring no interpretation — the polygons either intersect or they don't. Showing the municipal boundary sitting inside or across a former reserve boundary is the most literal possible expression of the "urban municipalities did not occupy empty land" argument. Each of the 6 cases could also be shown as an inset map for the case studies.

**Data status:** Municipal polygons and surrender parcels are already in the spatial analysis pipeline. Métis community points are in `analysis/data/metis_full.csv`. Railway lines available from Borealis HR_rails_NEW.shp.

---

### 2. Corridor clustering — Type A municipalities along railway lines

**What it shows:** Strings of Type A municipalities running adjacent to CPR, CNoR, and GTPR lines, with surrendered reserves nearby. The corridor pattern — multiple Type A settlements near the same reserve, planted by the same railway company — is inherently spatial.

**Layers needed:**
- All 429 municipality points, coloured by temporal type (A / B / C / none)
- Railway lines, coloured or labelled by company
- Surrendered reserve parcels
- Optionally: lines connecting Type A municipalities to their nearest surrender reserve, to make the clustering explicit

**Why it works:** The corridor structure is a geographic phenomenon — the strings of settlements follow the railway lines across the map. The CPR main line cluster east of Regina, the CNoR north-central corridor, and the GTPR corridor would resolve into visually distinct bands. This is the spatial expression of the Query 4a finding (13+ reserves with 3+ Type A municipalities within 25km).

**Data status:** Temporal type is a property on all Settlement nodes. Railway company is stored as `first_railway` on Settlement nodes and as shapefiles in Borealis.

---

### 3. Case study inset maps — individual settlement profiles

**What it shows:** For each of the 6 geometric overlap case studies, a close-range map showing the settlement, the reserve, the surrendered parcel(s), the railway line, and the Métis community location. Intended as figures within the case study chapters rather than province-wide maps.

**Kamsack / Cote:** Municipal boundary adjacent to Cote reserve; Crowstand Residential School location; CNoR line.

**Delmas / Thunderchild:** Municipal boundary overlapping Thunderchild surrender; Métis community point (1882 anchor); CNoR line.

**Leask / Mistawasis:** Municipal boundary overlapping Mistawasis surrender (1911 and 1919 parcels); CNoR line arriving 1911.

**Lestock / Muskowekwan:** Municipal boundary overlapping Muskowekwan surrender (1920); Métis community inside boundary; GTPR line.

**Regina Beach / Last Mountain Lake:** Municipal boundary overlapping Last Mountain Lake surrender (1918); Métis community inside boundary; QLSRSC line.

**Laird / Stoney Knoll:** Municipal boundary overlapping Stoney Knoll surrender (1897); CNoR line (1910); the clarifying exception — surrender preceded town by 11 years.

**Why it works:** At close range, the spatial relationships are unambiguous and analytically legible without supplementary interpretation. The inset format allows each case to tell its own story while contributing to the overall argument.

**Data status:** All required layers are available. Leask and Lestock have null `founded` dates — the data gap should be noted in the figure caption rather than treated as a map issue.

---

## Tier 2 — Workable with design choices

These findings are spatial in principle but require deliberate design decisions to avoid visual noise.

### 4. Province-wide temporal type distribution

**What it shows:** All 429 municipalities plotted by location and coloured by temporal type (A / B / C / none). Intended to show the geographic distribution of the "pressure then surrender" pattern across the province.

**Challenge:** The majority of municipalities (71%) fall in the "none" category and would dominate the map visually. Without careful colour choice and layering, the Type A pattern (82 municipalities, 19% of total) could be visually lost. The temporal argument is also not inherently spatial — Type A municipalities are distributed across multiple corridors rather than clustering in one region.

**Design recommendation:** Use a muted neutral for "none" and reserve high-contrast colour for Type A only. Overlay railway lines to anchor the corridor structure. May work better as a small-multiple series (one map per type) than as a single composite.

---

### 5. Indirect benefit hinterlands — RSC satellite networks

**What it shows:** RSC and City settlements connected by lines to their Type A satellite settlements within 50km, showing which commercial hubs sat at the centre of the densest dispossession-adjacent agricultural hinterlands (Query 8a findings).

**Challenge:** At province scale, hub-and-spoke lines connecting every RSC to 20–28 satellite settlements would produce a dense web that obscures rather than clarifies. The Qu'Appelle valley cluster (Balcarres, Lumsden, Fort Qu'Appelle, Qu'Appelle) and the Battle River corridor would likely be the most visually legible cases, but province-wide the map risks becoming unreadable.

**Design recommendation:** Either restrict to the top 5–6 RSCs by satellite count, or show as a choropleth (RSCs shaded by satellite density) rather than explicit connection lines.

---

### 6. Multiple surrender events — Piapot, Pasqua, Mistawasis

**What it shows:** The three reserves that show multiple distinct surrender years (Query 4b), with the Type A municipalities associated with each surrender event mapped and distinguished. Intended to show the iterative nature of dispossession on the same reserve.

**Challenge:** The distinction between first and second surrender events on the same reserve requires careful symbology. At province scale the three reserves are geographically dispersed. This works better as three close-range inset maps than as a single province-wide figure.

**Design recommendation:** One inset per reserve, showing the reserve boundary, the two surrendered parcel groups (distinguished by year), and the associated Type A municipalities coloured by which surrender event they are nearest to.

---

## Tier 3 — Not map-ready without significant data work

These findings are fundamentally temporal or statistical and do not have natural map expressions with the current data.

### 7. Railway determines where, demographics determine when

The convergence of surrender years across railway companies despite divergent arrival years (Query 4g) is a temporal argument visible in a table or chart, not a map. The geographic expression of this finding — all corridors' surrenders clustering in 1909–1921 — would look identical to the corridor clustering map (Tier 1, item 2) without the temporal dimension being legible.

**Alternative:** A timeline chart (x = year, y = railway company or corridor, dots = surrender events) would express this argument more clearly than any map.

### 8. Gap distribution across temporal types

The railway-to-surrender gap distribution (Queries 4c, 4f) is a statistical distribution — the finding lives in the shape of the histogram across bands, not in the geography of individual settlements. A bar chart or stacked histogram by type would be the appropriate visualization.

### 9. Census commercial tier hierarchy

The founding-order hierarchy (Cities mean 1888, SSCs mean 1906) is a temporal finding best expressed as a timeline or box plot, not a map. A map of commercial types by location exists implicitly in the data but would not show the temporal argument.

---

## Priority order for development

| Priority | Visualization | Format | Rationale |
|---|---|---|---|
| 1 | Case study inset maps (×6) | Close-range map per case | Most direct spatial argument; needed for case study chapters |
| 2 | Corridor clustering — Type A along railway lines | Province-wide map | Visually legible; expresses core corridor argument |
| 3 | Geometric overlap — provincial context | Province-wide map with insets | Situates the 6 overlap cases in the broader dataset |
| 4 | Multiple surrender events (Piapot, Pasqua, Mistawasis) | 3 inset maps | Supports iterative dispossession argument |
| 5 | Indirect benefit hinterlands | Choropleth or restricted hub-spoke | Useful if Tier 1 maps already establish the argument |
| 6 | Timeline chart — surrender years by corridor | Chart, not map | Railway-determines-where argument; no map equivalent |
