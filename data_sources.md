# FoodMap source register and limitations

The offline demonstration is generated with seed 3304. No generated values are represented as real observations. The real-data importer uses the following official source releases and records their URLs, import date and counts in a JSON manifest beside the new database.

| Source | Release / use |
|---|---|
| [ACS 5-year table-based summary files](https://www.census.gov/programs-surveys/acs/data/summary-file.2024.html) | 2020–2024, B01003 total population, B19013 median household income, B17001 poverty below threshold divided by population with determined poverty status, B08201 zero-vehicle households divided by all households |
| [Census TIGER/Line](https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.2024.html) | 2024 Texas tract polygons for point-in-polygon matching; 2020 cartographic ZCTA polygons for approximate ZIP labels |
| [USDA historical SNAP retailer data](https://fns-prod.azureedge.us/snap/retailer-locator/data) | Authorization spells active at 2025-12-31; Texas stores only, deduplicated, spatially matched to selected tracts |
| [VIA Metropolitan Transit developer resources](https://www.viainfo.net/developer-resources/) | GTFS stops.txt, downloaded at import time. Data provided by VIA Metropolitan Transit. [Developer license](https://www.viainfo.net/developers-license-agreement/) |
| [USDA Food Access Research Atlas](https://www.ers.usda.gov/data-products/food-access-research-atlas/download-the-data) | 2025 SRAM tract records, filtered into an independent reference CSV. Official indicators are not substituted for our custom scores. |
| [OpenStreetMap](https://www.openstreetmap.org/) | Optional supplemental source in proposal, not imported: missing SNAP retailer coordinates are excluded rather than fabricated. |

Scope: Bexar, Comal and Guadalupe counties, Texas. One area = census tract. ZIP is the ZCTA closest to a tract representative point; multiple tracts can share a ZIP. The Query 3 filter uses that area ZIP, not the individual mailing ZIP. Areas with unusable ACS estimates are excluded and counted. Stores and stops outside retained areas are excluded. Supermarkets, grocery stores and farmers markets are treated as likely fresh produce sources; actual inventory is unverified. All imported retailers are SNAP-authorized as of the historical snapshot, so estimates represent SNAP retailer access, not the entire grocery market. Other retailer types are treated conservatively as not confirmed fresh. Transit proximity is a straight-line estimate multiplied by 1.3, not a walking route, and ignores service frequency, travel time and street barriers. FoodMap's rankings are screening indicators, not official USDA food-desert designations. ACS estimates have sampling error and source vintages differ.

The import is an implemented, offline-fixture-tested pipeline; the full live download has not been executed or verified in the authoring environment. No raw external downloads are committed.
