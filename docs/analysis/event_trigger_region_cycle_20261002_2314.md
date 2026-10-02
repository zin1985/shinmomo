# Event-trigger region normalization cycle — 2026-10-02 23:14 JST

## Theme
Generalize the existing source-transition hotspot corpus into one machine-readable event-trigger region layer without redoing map/transition extraction.

## Confirmed
- Existing hotspot corpus contains 57 rows.
- 55 are VM coordinate predicates: 36 opcode 0x69 exact points and 19 opcode 0x5D inclusive rectangles.
- Two are native-boundary predicates: one confirmed one-cell exit and one three-cell candidate corridor.
- Normalized region corpus has 37 point regions, 19 rectangles, and 1 corridor.
- 52/57 regions resolve a destination canonical config; 47/57 also resolve destination X/Y.
- VM and native-boundary predicates remain separate layers. Native boundary is not terrain passability or object occupancy.

## New artifacts
- `tools/python/catalog_event_trigger_regions.py`
- `data/events/event_trigger_regions.csv`
- `data/events/event_trigger_regions_summary.json`

## Strong hypothesis
The remaining five unresolved destination configs and ten unresolved arrival coordinates are the highest-information frontier for extending transition -> event/trigger joins, because predicate geometry is now normalized and no longer the blocking representation problem.

## Unconfirmed
No claim is made that every trigger region is player-walk activated, nor that the native corridor's three cells are all passable.

## ROM
Drive-designated canonical ROM was not accessed in this cycle; no substitute ROM was used. This cycle used only committed evidence.

## Next
Resolve destination/event provenance gaps in the 57-region catalog, prioritizing rows with known transition IDs but missing canonical destination config or arrival coordinates.
