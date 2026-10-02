# Event-trigger crosslink gap manifest (2026-10-03)

## Scope
This cycle extends the existing 57-row `event_trigger_regions.csv` corpus without re-extracting map transitions or reimplementing the viewer.

## Confirmed facts
- 57 trigger regions are already normalized from committed hotspot evidence.
- 42/57 regions have both canonical destination config and arrival X/Y.
- 15/57 retain a provenance gap.
- The 15 gaps split cleanly into 5 `destination_config_only` rows and 10 `arrival_xy_only` rows.
- No row lacks both destination config and arrival X/Y.

## Strong interpretation
The remaining transition-to-trigger backlog is therefore not one generic unresolved bucket. The five config-only rows already have arrival coordinates and need destination pack/entry/config resolution. The ten arrival-only rows already have canonical configs and need coordinate-setter or saved-state-arrival provenance.

## Not claimed
No missing destination config or arrival coordinate is inferred from neighboring maps, visual similarity, or duplicate coordinates. Terrain passability, object occupancy and native map-boundary semantics remain separate layers.

## Reproducible outputs
- `tools/python/catalog_event_trigger_crosslink_gaps.py`
- `data/events/event_trigger_crosslink_gaps.csv`
- `data/events/event_trigger_crosslink_gaps_summary.json`

## Next analysis
Prioritize the five destination-config-only rows first because resolving one pack/entry mapping can also improve source/destination graph connectivity. Then trace the ten arrival-only rows to opcode 0x58 coordinate setters or explicit saved-state arrival semantics.