# Cypher Query Findings — Analytical Synthesis

Synthesizes findings from all queries run against the Neo4j graph following Phase 5 enrichment: Queries 1–12, 4b–4g, 8c–8d, and supplementary LHB and reserves_master work. Draws together the major analytical threads and states the argument the data as a whole supports.

---

## Definitions

### Temporal types
Classifications assigned to each municipality based on the relationship between its founding date and the year of the nearest reserve surrender.

- **Type A** — Municipality founded more than 5 years *before* the nearest reserve surrender. The core "pressure then surrender" set: 83 municipalities (19% of 429).
- **Type B** — Municipality founded within 5 years (before or after) of the nearest reserve surrender. Simultaneous arrival: 27 municipalities (6%).
- **Type C** — Municipality founded more than 5 years *after* the nearest reserve surrender. Post-surrender settlement: 8 municipalities (2%).
- **Indeterminate** — Founding date or surrender year missing or unresolvable: 6 municipalities (1%). See Query 12 findings for full characterization. Note: Leslie, VL was reclassified from Indeterminate to Type A (2026-04-08) after recovery of its 1882 founding date from KG context fields.
- **None** — No surrendered reserve parcel within meaningful proximity (roughly 25km): 305 municipalities (71%).

### Commercial tiers
Classifications of each municipality's economic function, drawn from the Knowledge Graph's `SettlementType` nodes. A single municipality may carry more than one label.

- **City** — Major urban centre with wholesale distribution, state administration, and banking functions.
- **RSC (Regional Service Centre)** — Town serving as a commercial hub for a multi-community hinterland; retail, professional services, some wholesale.
- **LSC (Local Service Centre)** — Smaller town providing basic retail and services to an immediate rural area.
- **SSC (Small Service Centre)** — Village-scale settlement with minimal commercial function; primarily farm-service.
- **Farm-Service Town** — Settlement whose primary function was supplying agricultural inputs and receiving farm outputs.
- **Farm Cluster** — Small agricultural colony or hamlet, often ethnically organized, with little commercial infrastructure.
- **Railway Town** — Settlement whose founding and growth was directly tied to railway infrastructure and operations.
- **Organized/Ethnic Settlement** — Community established as a deliberate ethnic or religious colony (Doukhobor, Mennonite, Ukrainian, Jewish, German, Icelandic, Swedish, etc.).

### Spatial measures
- **dist_m / min_dist_to_surrender_m** — Boundary-to-boundary distance in metres between a municipality polygon and the nearest surrendered reserve parcel.
- **n_surrenders_5km / n_surrenders_25km** — Count of distinct surrendered reserve parcels within 5km or 25km of the municipal boundary.
- **overlap_with_surrender** — Boolean: the municipality's 1921 polygon geometrically intersects a surrendered reserve parcel.
- **nearest_surrender_reserve** — Name of the reserve whose surrendered parcel is closest to the municipality.
- **nearest_surrender_year** — Year of the surrender of that nearest parcel.

### Gap measures
- **Formal gap** — `nearest_surrender_year − founded`: years between the municipality's formal founding date and the nearest reserve surrender.
- **Effective gap** — `nearest_surrender_year − effective_start`: years between the earliest documented colonial presence (institutional event year or Métis community founding year, whichever is earlier) and the nearest reserve surrender. A correction to the formal gap that surfaces accumulated presence predating the formal founding date.
- **Railway gap** — `nearest_surrender_year − railway_arrives`: years between a railway's arrival in the municipality and the nearest reserve surrender.

### Railway companies
- **CPR** — Canadian Pacific Railway. Main line completed across Saskatchewan 1882.
- **CNoR** — Canadian Northern Railway. Branch lines built 1904–1911.
- **GTPR** — Grand Trunk Pacific Railway. Main line across northern Saskatchewan 1907–1908.
- **QLSRSC** — Qu'Appelle, Long Lake and Saskatchewan Railroad and Steamboat Company. Older line, 1887, connecting Regina north through the Qu'Appelle valley.

### Other abbreviations
- **LHB** — Local History Book: community-authored historical volumes compiled for Saskatchewan municipalities, typically published 1950s–1990s.
- **DIA** — Department of Indian Affairs (federal).
- **SSB** — Soldier Settlement Board: federal body established post-WWI to settle veterans on agricultural land, often purchased from reserves.
- **LID** — Local Improvement District: pre-municipal administrative unit for rural Saskatchewan.
- **NWMP / RNWMP** — North-West Mounted Police / Royal North-West Mounted Police.
- **HBC** — Hudson's Bay Company.
- **NWC** — North West Company (fur trade, predecessor to HBC merger 1821).
- **TRC** — Truth and Reconciliation Commission of Canada.

---

## 1. The Core Argument — What the Data Demonstrates

83 of 429 Saskatchewan municipalities (19%) were founded before the nearest reserve surrender — the Type A "pressure then surrender" set. 27 (6%) arrived simultaneously within 5 years (Type B). 8 (2%) arrived after. 305 (71%) have no surrendered reserve within meaningful proximity.

The meaningful divide in the dataset is not between Types A, B, and C — which have nearly identical average distances to surrendered land (12,345–13,512m) — but between those three types collectively and the none group (75,927m average). Settlement in Saskatchewan was not uniformly distributed relative to reserve land. It concentrated in corridors where surrender was most active. Within those corridors, 19% of municipalities were there first.

The 5 of 6 geometric overlap municipalities that are Type A are the strongest spatial expression of this: the settlements that ended up geometrically absorbing surrendered reserve land were, in five of six cases, the settlements that existed before the surrender occurred.

The argument the data supports is not that settler municipalities conspired against reserves. It is that their accumulated presence — mundane, dispersed, independent — generated the conditions that made formal surrender inevitable. This is Raibmon's accumulated microtechniques argument made spatially and temporally measurable.

---

## 2. The Temporal Structure — Formal Founding Understates Accumulated Presence

The formal `founded` date is a poor measure of how long colonial presence had been building before a surrender. The sensitized Query 3a shows that for 24 of 35 long-gap Type A municipalities, the formal founding date is not the real start of accumulated colonial presence.

Three anchors capture presence more accurately:
- **Institutional event year** (earliest colonization company, NWMP, mission, church, or school): determinative in 9 of 35 cases
- **Nearest Métis community founding year**: determinative in 15 of 35 cases, with corrections of 20–30 years typical
- **Formal founding**: the earliest documented presence in only 11 of 35 cases

The extreme case is Fort Qu'Appelle, where a 1804 NWC post (Métis labour presence from the earliest fur trade) gives an effective gap of 106 years before the 1910 Pasqua surrender. The institutional genealogy in the Qu'Appelle Valley — fur trade 1804, established Métis community 1840, NWMP barracks 1880, homesteading from 1880, municipal founding 1880 — is the longest documented accumulation in the dataset.

The practical implication: any analysis that uses the formal `founded` date as the measure of pre-surrender presence is systematically understating the depth of colonial accumulation. The null `founded` problem compounds this further — Leask's 1912 village incorporation date rendered it apparently Type C, but local history book research established an effective founding of 1902–1904 and an LID from 1908, giving a genuine effective gap of 7–9 years before the 1911 surrender. Formal administrative dates capture when colonial administration recognized a settlement; they do not capture when colonial presence began.

---

## 3. The Railway Finding — Where vs. When

Railways structured the geography of pressure on reserves. They did not determine its timing.

Despite CPR arriving on the Saskatchewan plains in 1882 and GTPR not until 1908 — a 26-year span — all four major railway companies' average surrender years fall within a 12-year window (1909–1921). CPR's average surrender came in 1915, 19 years after its average arrival. CNoR's came in 1911, just 4 years after its average arrival. This is not because CNoR was uniquely aggressive. CNoR arrived in 1907 on average — directly into the middle of the Sifton-era settlement boom. The demographic density needed to generate irresistible surrender pressure was already present when the railway came.

The railway-precedes-surrender sequence is the diagnostic signature of Type A. For Types B and C, the sequence runs the other direction: surrender came first, and settlement and railway infrastructure followed. This is confirmed by the full gap distribution (Query 4f): 85% of Type B municipalities have surrender before railway; 75% of Type C show the same. The railway-driven pressure mechanism is almost exclusively a Type A phenomenon.

**Railway determined where; settler population density determined when.** The convergence of surrender years across all corridors despite divergent arrival years is the single strongest quantitative expression of this argument in the dataset.

---

## 4. Two Distinct Dispossession Mechanisms at the Hub Scale

Queries 8a and 8b together reveal that RSC/LSC/City hubs were not connected to reserve surrender through a single mechanism. Two structurally distinct patterns emerge:

**Corridor accumulation** — the Qu'Appelle valley CPR corridor and the GTPR main line produced dense networks of small Type A settlements whose cumulative proximity to surrendered land is consistent across both geographic and railway-corridor measures. Hubs like Balcarres, Lumsden, Fort Qu'Appelle, and Qu'Appelle commanded hinterlands of 12–16 Type A satellite settlements. Their own distances to surrendered land are moderate, but their satellites collectively generated diffuse, province-wide pressure along established railway lines. The indirect benefit chain operated through commercial flows: agricultural surplus, grain shipping, farm equipment sales, banking — economic activity generated in farm clusters near surrendered land flowing to service centres that may themselves have been distant from any reserve.

**Close-range intensity** — the Battle River corridor (Battleford, North Battleford) shows the opposite pattern. Both hubs lead on surrender density (7 surrendered parcels within 25km each) but rank last in satellite hinterland — one satellite each. The pressure was not generated through a dense satellite network over a broad corridor. It was generated through a small number of settlements sitting at very close range to multiple reserves simultaneously. Fewer settlements, closer range, more reserves targeted in the same area.

These two mechanisms were not sequential phases — they operated in parallel across the province. The corridor accumulation pattern dominates the Qu'Appelle valley and GTPR main line; the close-range intensity pattern characterizes the Battle River corridor. Both are consistent with Raibmon's accumulated microtechniques framework; they are different expressions of the same underlying process at different spatial scales.

---

## 5. The Commercial Type Finding — Temporal Type Is the Load-Bearing Variable

Within the Type A set, commercial type predicts proximity to surrendered land: Farm Clusters average 10,945m (closest), Cities average 15,986m (furthest). This is the microtechniques argument made spatially visible — agricultural communities needed direct land access; larger commercial centres benefited indirectly through the flows that agricultural activity generated.

But Query 8c shows that this gradient disappears when the Type A filter is removed. Farm Clusters average 67,296m across all 429 municipalities — the furthest of any substantive commercial type. Only 6 of 58 Farm Cluster municipalities are Type A; the remaining 52 are scattered across the province far from surrendered land.

**Commercial type alone does not predict proximity to surrendered land. Temporal type is the load-bearing variable.** The commercial type gradient within Type A is not a parallel explanatory claim — it describes how the benefits produced by dispossession were distributed across different kinds of settlements. The temporal finding describes how dispossession was produced in the first place. The latter was the precondition for the former.

The practical implication for the argument: the "farm clusters closest" finding is a property of Type A farm clusters specifically. It is one of the strongest findings in the dataset when correctly bounded; it becomes misleading when generalized.

---

## 6. What Predicts Proximity and Gap Length — A Cross-Query Structural Synthesis

Queries 14 and 14a–14e completed the systematic testing of settlement characteristics against proximity to surrendered land and gap length. Together with Queries 8, 8c, 4, and 9, they produce a coherent picture with a clear causal structure: accumulated pre-surrender presence produced dispossession, and dispossession produced differentiated benefits depending on what kind of settlement a community was. These are not parallel claims — the temporal mechanism is the precondition for the commercial outcome.

**At the level of the full 429 municipalities, temporal type is the only load-bearing variable for proximity.** Whether a settlement predated a nearby surrender is what predicts whether it sat close to surrendered land. What kind of settlement it was — its population size (Query 14), CSD administrative type (14a), ethnic/organized character (14d), or how many surrendered parcels were nearby (14c) — produces no consistent signal. Query 9 states the aggregate version of this plainly: the meaningful divide is between Types A, B, and C collectively (avg 12,345–13,512m) and the none group (75,927m). Every structural characteristic tested dissolves into noise at this level.

**Within Type A, founding decade is the primary predictor of gap length.** Across Queries 14, 14a, 14c, and 14d, no structural characteristic of settlements predicts how long before a surrender they were founded — except when they were founded. Query 14b shows a monotonic decrease across decades: 1870s cohort avg 29 years, 1880s avg 26, 1890s avg 15, 1900s avg 13, 1910s avg 10. Earlier-founded settlements accumulated pressure over a longer period before formal surrender resolved it; later-founded settlements arrived into an administrative landscape already primed for processing surrender petitions. This is Raibmon's accumulated microtechniques argument quantified: it is the duration and density of dispersed colonial presence that matters, not the form that presence takes.

**The founding decade finding reframes the railway finding.** Queries 4, 4d, and 4g established that average surrender years converge across all four railway companies within a 12-year window despite divergent arrival years. Query 14b explains why: CPR's longer average gaps reflect earlier founding dates, not a company-specific dynamic. The railway structured geography — where settlement concentrated and where pressure was therefore directed. Founding decade structured pace — how long accumulated presence had to build before formal surrender followed. Neither is reducible to the other.

**Query 14e identifies the pre-railway founding set as the clearest expression of non-railway pressure.** Fort Qu'Appelle (railway_lag 31 years), Battleford (30), Lebret (25), Duck Lake (15) are settlements where the railway arrived years or decades after the community, and in six cases after the surrender itself. These are the institutional, mission, and NWMP founding cases from Query 3a confirmed from a second angle. They demonstrate that accumulated presence — administrative authority, mission infrastructure, Métis community presence, homesteading — generated sufficient pressure to produce surrenders without railway catalysis. The mechanism is different from the CPR townsite pattern; the temporal logic is identical.

**Commercial type within Type A describes the distribution of benefits, not the mechanism of dispossession.** The Query 8c proximity gradient — farm clusters closest (avg 10,945m), cities furthest (15,986m) — is not a competing explanatory variable. It shows how the benefits produced by dispossession were distributed: agricultural settlements at the reserve boundary extracted direct land benefit; cities and regional service centres further back extracted indirect commercial benefit through the agricultural flows that direct settlement generated. Both forms of benefit were downstream of the same temporal mechanism. The gradient in proximity is the gradient in directness of benefit from dispossession, not a separate causal story.

---

## 7. The Indirect Benefit Chain — Beyond the Type A Frontier

The indirect benefit argument was confirmed and extended across three queries. Query 8a measured how many Type A farm-cluster satellites sat within 50km of RSC/LSC hubs, and the average satellite distance to surrendered land. Query 8b measured the same through the railway network. Query 8d removed the Type A restriction on hubs and asked which service centres commanded the largest Type A hinterlands regardless of their own temporal type.

The Qu'Appelle valley dominates all three measures. The ranking is stable: Balcarres, Lumsden, Fort Qu'Appelle, Qu'Appelle lead whether the measure is geographic, railway-corridor, or hub temporal type.

The key extension from 8d is **Lemberg**: second in the province with 15 Type A satellites (after deduplication), temporal type `none`, sitting 31km from any surrendered land. Lemberg never appears in the pressure-then-surrender argument. It simply sat at the hub of a corridor whose settlements did. It is the purest case in the dataset of indirect commercial benefit from the dispossession frontier — a service centre that captured agricultural surplus generated in a landscape of active reserve reduction without having any formal relationship to that reduction.

Four other none-type hubs appear in the top 20 of 8d (Govan, Wynyard, Esterhazy, Nokomis), all with Type A satellite hinterlands of 4–6 settlements. The indirect benefit chain extended well beyond the Type A set into commercial centres with no surrender correlation of their own. The dispossession frontier generated value that flowed through the prairie commercial economy at multiple removes from the formal surrender events.

---

## 8. The Métis Dimension — Prior Presence and the Three-Layer Sequence

The Métis dataset adds a layer of prior presence to the colonial genealogy that the formal municipal founding dates systematically erase.

**62% of municipalities with Métis community associations were built into pre-existing Métis settlements** (Query 5a: 21 of 34 are `metis_first`). The precedence gaps range from 5 years (Duck Lake) to 50 years (Weldon/Glen Mary). Among the 21 `metis_first` cases, 9 are also Type A — the double-dispossession cases: the municipality incorporated an established Métis settlement and simultaneously correlated with surrender pressure on an adjacent reserve.

The full sequence in these 9 cases: Métis community established → settler municipality built into or near that community → reserve surrender follows. Three temporally stacked displacements operating in the same location.

Métis displacement operated through two distinct processes visible in the dataset:
1. **Reserve-adjacent displacement** — Métis communities near reserves, where the municipality was in the pressure-then-surrender sequence. The spatial and dispossession histories are intertwined.
2. **Urban-core displacement** — Métis communities absorbed directly into city growth (Saskatoon, Moose Jaw, Swift Current) independently of reserve surrenders. A separate dispossession mechanism operating through municipal expansion, road allowance removal, and city boundary extension rather than through the surrender process.

Raibmon's framework applies to both, but through different branches of the colonial genealogy. The two processes are visible in a single dataset but require different evidential approaches to document.

---

## 9. The Cross-Type Picture — Layered Colonization Waves

Reserve surrenders did not attract a single wave of settlement. Three reserves — Fishing Lake, One Arrow, and Stoney Knoll — attracted municipalities of all three temporal types, showing the full colonization sequence operating on a single piece of land:

**Type A** settlements generated the conditions for surrender through accumulated pre-surrender presence. **Type B** settlements arrived in the immediate aftermath of surrender — the compressed post-surrender colonization wave. **Type C** settlements filled in the landscape over the following years and decades, building on land already cleared.

The Stoney Knoll case is the most complete: Rosthern (Type A, Métis present, founded 1893) preceded the 1897 surrender, then four Mennonite colonies (Hague, Hepburn, Laird, Waldheim — all Type C) arrived on the cleared land over the following decade. The full colonial sequence — pre-existing settler and Métis presence, formal surrender, post-surrender ethnic colony planting — is visible in a single reserve's history.

The Thunderchild case links this finding directly to the case study set: Delmas (Type A, overlap, Métis present) is the pre-surrender anchor; Rock Haven, Meota, and Vawn are the Type B post-surrender arrivals. The analysis of Delmas as a case study is therefore not just the story of a single settlement — it is the leading edge of a colonization wave that continued after the 1908 surrender.

Type B is structurally different from Type A, not compressed Type A. For 85% of Type B municipalities, the railway came after the surrender; for Type A, railway-precedes-surrender is the diagnostic signature. Post-surrender colonization followed a different logic from pre-surrender pressure.

---

## 10. The Multiple Surrender Events — Iterative Pressure and Distinct Mechanisms

Only 3 reserves in the Type A set show multiple distinct surrender years: Piapot (1918 and 1919), Pasqua (1906 and 1910), and Mistawasis (1911 and 1919). Most corridor clusters ended in a single legal surrender despite sustained multi-settlement pressure.

**Pasqua is analytically the most significant.** The 1906 surrender correlates with three CPR railway-corridor villages (McLean, Qu'Appelle, Indian Head — all founded 1881–1882); the 1910 surrender correlates with Fort Qu'Appelle and Lebret — the mission and institutional settlements whose effective presence stretches to 1804 and 1860 respectively. Two distinct colonial mechanisms — railway frontier pressure and religious/institutional presence — operating on the same reserve yielded two separate surrender events four years apart. This is a direct materialization of Raibmon's genealogy in the spatial data: the railway and institutional branches of colonial presence were not the same mechanism, and here they produced distinct legal outcomes.

**Mistawasis** shows an 8-year gap between surrender events (1911, 1919). The 1911 surrender correlates with Leask — the geometric overlap case with the highest 5km surrender density in the dataset and simultaneous railway arrival. The 1919 surrender (16,548 acres to the Soldier Settlement Board) was confirmed by the Leask local history book, which records that the land was settled predominantly by WWI veterans. The gap between events suggests the 1911 surrender did not satisfy accumulated demand; pressure continued, and a second reduction followed.

---

## 11. What the Data Cannot Show — Methodological Limits

**The nearest-reserve matching logic cannot distinguish surrender mechanisms.** George Gordon (Reserve 86, Punnichy) is the clearest case: classified as a Type A pairing because the 1933 surrender is the spatially nearest, but reserves_master notes establish that all three George Gordon surrenders (1914, 1919, 1933) were Church of England/Gordon Residential School land acquisitions, not settler corridor pressure. The Type A classification is technically correct but analytically inert — Punnichy's presence did not generate the conditions for the surrender. The dataset can identify proximity and sequence; it cannot identify mechanism without external sources.

**Commercial type alone does not predict proximity to surrendered land** (8c). Temporal type is the load-bearing variable. This means the commercial type gradient finding (farm clusters closest) only holds within the Type A filter, and overstating it as a general property of farm clusters would be methodologically wrong.

**IS_TYPE duplication inflated 8a absolute satellite counts.** The 8a results (Balcarres 28, Lumsden 24) were produced by the same inflation corrected in 8d (Balcarres 16, Lumsden 14). Relative rankings remain valid; absolute counts in 8a should be treated with caution.

**Formal founding dates systematically understate accumulated colonial presence.** This is not a data error — it is a property of the administrative record. Municipal founding dates capture when colonial administration recognized a settlement, not when colonial presence began. The sensitized gap methodology and local history book work are partial corrections, not complete solutions.

**The dataset establishes correlation and temporal sequence, not causation.** Only Kamsack has documentary evidence establishing a causal link between settler presence and a reserve surrender (the Cote surrender notes name the town). All other Type A pairings are correlations that warrant archival follow-up. This is not a weakness of the argument — it is the epistemological position Raibmon's methodology is designed for. The accumulated spatial and temporal evidence is strong enough to demand explanation; the mechanism of each individual case requires archival sources to confirm.

**The dataset is state-colonial in character and cannot represent the Indigenous experience of dispossession.** All sources used in this analysis — municipal founding records, DIA surrender documentation, railway records, census data, local history books — were generated by colonial administrative processes. They record settler presence and Indigenous land as administrative objects; they systematically suppress Indigenous agency, resistance, and experience as subjects. This is not a technical gap in the data collection but a structural property of the archive itself. The analysis can demonstrate the settler-side mechanism of dispossession with considerable rigour; it cannot demonstrate what that dispossession meant or cost for the First Nations and Métis communities involved.

*Note for thesis writing:* If future archival work — including LAC research on scrip and land speculation, DIA correspondence, and Indigenous oral or community sources — yields material that speaks to the Indigenous experience of the dispossession documented here, a dedicated section or thread should be added to the argument. If that material is not available by the time of writing, this structural limitation of the archive must be stated explicitly in the thesis, framed not as an apology but as a property of the evidentiary base: colonial records are the appropriate source for demonstrating settler mechanism; a different archive is required to recover Indigenous experience of that mechanism.

**The cost side of the ledger has been documented at the macro level by McKenzie and Mosby (2024).** "Reconciling the Ledger: The Rupert's Land Purchase, Settler Capitalism, and Indigenous Dispossession on the Prairies" (*Journal of the Canadian Historical Association*, 34:1) quantifies what was taken: HBC received 6.6 million acres of prime agricultural land (generating ~$96 million net profit in land sales alone by 1930); First Nations received 3 million acres in reserves through Treaties 1–7 — less than half what the HBC received and less than per capita treaty entitlement; 874,000 acres were officially "surrendered" from reserves between 1871 and 1928, the national universe that includes the 54 Saskatchewan surrender parcels in this dataset. This project does not need to replicate that macro-level cost analysis. Its contribution is the bottom-up mechanism analysis: documenting how dispersed settler accumulation generated the individual surrenders within the structural framework McKenzie and Mosby describe. The two projects are complementary — McKenzie and Mosby establish the scale and conditions; this project documents the ground-level process.

**The term "surrender" throughout this analysis uses colonial administrative designation, not Indigenous legal understanding.** Krasowski's *No Surrender: The Land Remains Indigenous* (University of Regina Press, 2019) demonstrates through treaty bundle analysis, Elder testimony, and close reading of colonial correspondence that Indigenous negotiators understood treaties as agreements to share land — not to cede it. Crown commissioners had a systematic strategy of omitting or downplaying the surrender clause during negotiations. "Surrender" in DIA records and in this dataset is therefore the colonial legal fiction applied to transactions whose meaning was understood very differently by the other party. This project uses the term because the evidentiary base requires it — the surrender parcels, surrender years, and acreage figures all come from DIA administrative records — but the thesis must note explicitly that "surrender" is a colonial administrative designation, not a neutral description of what First Nations consented to.

---

## 12. The Frank Oliver Corollary — A Meaningful Negative

The 1911 *Indian Act* amendment permitting expropriation without consent near towns exceeding 8,000 population was effectively irrelevant in Saskatchewan. Only Regina qualifies; Saskatoon and Moose Jaw — the 2nd and 3rd largest cities — are temporal type `none` with no surrender within meaningful proximity. The province's urban hierarchy was too compressed: most "cities" had populations of 2,000–4,000 in 1921.

This is analytically significant because it narrows the argument precisely. Saskatchewan's reserve reduction was driven almost entirely by the informal accumulation of small-settler presence — farm clusters, ethnic colonies, railway townsites — not by top-down expropriation under federal statute. The Frank Oliver amendment reveals federal willingness to formalize dispossession when urban interests demanded it, but it was not the operative mechanism in Saskatchewan. The dispossession documented in this dataset was produced by the ground-level processes Raibmon describes, not by the legislative ceiling the amendment created.

---

## 13. The Case Study Picture — What the Queries Established and What Remains

The six geometric overlap municipalities are the most spatially concentrated expression of colonial dispossession in the dataset. What the cross-query evidence establishes for each:

**Kamsack** — the anchor case. Documentary causation in the event data. Effective_start 1889 (Crowstand Residential School). Railway gap 2 years. Both corridor accumulation hub and direct-overlap case simultaneously. No archival gap for the mechanism argument.

**Delmas** — the clearest McGuire petition-cycle case (railway 1905, founding 1905, surrender 1908, gap 3 years). Métis anchor 1882 gives effective gap of 26 years. The formal 3-year gap disguises a much longer accumulation. Mechanism remains correlation — no petition document in the data.

**Leask** — rehabilitated by local history book research. Effective founding 1902–1904, LID 1908 — genuine effective gap of 7–9 years before the 1911 surrender. Null `founded` in dataset reflects 1912 village incorporation, understating presence significantly. Highest 5km surrender density in the entire dataset. Mechanism remains correlation pending Carlton Agency archival work.

**Lestock** — reserves_master notes confirm "7485 acres surrendered in 1920, pursued by settlers." Mechanism partially confirmed in the same source that resolved George Gordon. Métis community inside municipal boundary (dist_m = 0). Effective gap 30 years from Métis anchor 1890.

**Regina Beach** — deepest effective gap in the overlap set (48 years from Métis anchor 1870). Colonization company documented (Pearson Land Company, 1902). CPR 1911, surrender 1918 — railway gap 7 years. Mechanism remains correlation.

**Laird** — the clarifying exception. Stoney Knoll surrendered 1897, Laird established 1908, CNoR 1910. Type C. No Métis presence. Distinguishes geographic overlap from the pressure-then-surrender dynamic that defines the other five cases. Its analytical role is to sharpen the argument by contrast.

The dataset identifies where archival follow-up is most productive: Carlton Agency (DIA) correspondence for Leask, Mistawasis petition records for Leask and Lestock, Thunderchild surrender records for Delmas, Last Mountain Lake and Pearson Land Company records for Regina Beach.

---

## Summary — The Argument the Dataset Supports

Saskatchewan's 429 incorporated municipalities were not built on empty land. They grew on or adjacent to Indigenous spaces systematically reduced through surrender, coercion, and institutional accumulation. The data supports this argument at several levels simultaneously:

1. **Spatial:** 19% of municipalities geometrically overlap with or sit within 5–25km of surrendered reserve land. 5 of 6 geometric overlap cases predated the surrender.

2. **Temporal:** The formal founding-to-surrender gap understates accumulated colonial presence. Effective presence — measured by institutional event anchors, Métis community founding dates, and local history book research — extends the colonial genealogy substantially further back in almost every resolvable case.

3. **Structural:** Railway infrastructure preceded surrender in virtually every Type A case. Post-surrender colonization (Types B and C) followed a structurally different logic, confirming that railway-driven pressure was the distinctive mechanism of the pre-surrender wave.

4. **Métis:** 62% of municipalities with documented Métis associations were built into pre-existing Métis settlements. In 9 cases, the same municipal presence both absorbed a Métis community and correlated with a nearby reserve surrender — three layers of dispossession in the same location.

5. **Commercial:** The dispossession frontier generated value that flowed through the prairie commercial economy from farm clusters to service centres to cities, whether or not those centres were themselves proximate to surrendered land. The benefit chain was not confined to the settlement frontier.

6. **Epistemic:** The argument does not require demonstrating conspiracy or coordination. The accumulated presence of dispersed, independent settler communities — agricultural, institutional, commercial — constitutes the mechanism Raibmon describes. Kamsack is the only case where documentary evidence establishes the causal link directly; all other cases are correlations that the spatial and temporal evidence makes very difficult to explain otherwise, and that archival investigation of petition records and DIA correspondence would be most likely to confirm or complicate.
