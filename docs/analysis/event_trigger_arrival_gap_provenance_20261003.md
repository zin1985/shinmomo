# Event-trigger arrival gap provenance classification (2026-10-03)

## Confirmed
The current event-trigger backlog contains nine `arrival_xy_only` rows. Joining each row to committed `map_transition_candidates.csv` by trigger address recovers its destination `(pack, entry)` pair.

A ROM-free corpus-wide check found **zero** cases where any of those nine destination `(pack, entry)` pairs already has arrival XY on another committed transition row. Therefore the successful CC:0F71 strategy (independent same-destination route carrying coordinates) cannot currently be repeated from the committed transition catalog alone.

CC:0BD7 is specifically `pack 0x96 / entry 0x02 / cfg_t09_l098_v2`; the transition row has no aligned destination coordinate address. This is a real provenance hole, not a missed join in the current catalog.

## Strong hypothesis / next evidence
Recover destination-entry coordinate provenance below the transition catalog layer: aligned or non-local opcode `0x58`, saved-state arrival, or an independent route-table coordinate source. Start with pack `0x96` entry `0x02` (CC:0BD7), then apply the recovered grammar to the other eight rows.

## Not claimed
No arrival XY is inferred from neighboring transitions, map layout, or coordinate similarity. Terrain/passability and CC:1160 phase selection remain separate problems.

Generated evidence: `data/events/event_trigger_arrival_gap_provenance.csv` and summary JSON, reproducible with `tools/python/classify_event_trigger_arrival_gaps.py`.