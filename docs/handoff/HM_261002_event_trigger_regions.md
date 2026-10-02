# Handoff — event-trigger regions — 2026-10-02 23:14 JST

Completed: normalized the committed source-transition hotspot corpus into `data/events/event_trigger_regions.csv` with reproducible generator `tools/python/catalog_event_trigger_regions.py`.

Current counts: 57 regions = 37 points + 19 inclusive rectangles + 1 native-boundary corridor. Predicate layers: 55 VM + 2 native-boundary. Destination config resolved 52/57; arrival XY resolved 47/57.

Evidence boundary: do not merge native-boundary regions with terrain passability or object occupancy. The three-cell pack2E corridor remains a candidate corridor, not three proven passable cells.

Next: extend transition -> event/trigger crosslinks by resolving the five missing destination configs and ten missing arrival-coordinate pairs, then attach event provenance where available.

Drive canonical ROM was unavailable in this cycle; no substitute ROM was used.
