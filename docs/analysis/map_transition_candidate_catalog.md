# Map transition candidate catalog

Updated: 2026-09-29

## Scope

This pass catalogs map-transition candidates only. It does not implement the
HTML viewer and does not integrate NPC or sprite data.

Canonical ROM SHA-256: F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98
Git HEAD used for generation: d11d3b1514a5ce1abce3b3608a6d0a228f106b3a

## Handler-level promotion

Normal VM opcode 0x53 dispatches to C4:8B3F, performs transition pre-work,
then directly JSRs C4:8B6A. It therefore shares the same two transition
operands and three-byte advance as the 0x56 core.

Normal VM opcode 0x56 dispatches to C4:8B6A and is three bytes total.
The handler copies the old global map pack $0305 to $15CF, writes operand 1
to both $15D0 and $0305, writes operand 2 to $13B8/$13B9, calls
81:837F, clears $1984, and advances by three bytes.

Normal VM opcode 0x58 dispatches to C4:8BE2. When $13B8 != 0, its four
operands are written to primary map coordinates $1573/$157D and secondary
map coordinates $15C3/$15C4. Existing map analysis independently identifies
these fields as current-map coordinates.

## Confidence policy

- confirmed: preserved runtime-observed transition evidence.
- strong_candidate: an exact bounded VM-substream tail of either
  53 <destination_pack> <destination_entry> B0 or
  56 <destination_pack> <destination_entry> B0, with the same destination
  entry present in destination record 0.
- structural_candidate: a terminal form whose destination entry is unresolved,
  or a non-terminal raw 0x53/0x56 shape retained only because its destination
  entry independently contains an aligned 0x58 coordinate setter.

The script-pack containing 0x53/0x56 is not automatically treated as the source map
pack. VM pack context and global map pack can differ, so static source map fields
remain blank unless independently proven.

## Counts

- total candidate rows: 1238
- confirmed: 1
- strong candidates: 1092
- structural candidates: 145
- rows with destination pack: 1238
- rows with unique destination configuration: 1048
- rows with destination X/Y: 720
- rows cross-linked to structural event records: 24
- rows carrying existing event-source xrefs: 14
- terminal 0x56 forms: 724
- terminal 0x56 forms with matching destination entry: 719
- terminal 0x56 forms with aligned destination 0x58 coordinates: 271
- non-terminal 0x56 coordinate-crosslinked structural rows: 25
- terminal 0x53 forms: 394
- terminal 0x53 forms with matching destination entry: 373
- terminal 0x53 forms with aligned destination 0x58 coordinates: 330
- non-terminal 0x53 coordinate-crosslinked structural rows: 94

## Runtime-confirmed anchor

The existing runtime trace confirms cfg_t07_l015_v2 / pack 0x2E transitions
to cfg_t04_l008_v2 / pack 0x50. During the transition, $0305 changes first,
then $126E/$12B4 converge to 0x50, and selector 4/8/2 becomes active.
The exact event opcode address for this observed edge is still unknown.

## Important structural finding

The second transition operand used by both 0x53 and 0x56 behaves as a
destination entry selector. Across the conservative terminal corpus,
destination record 0 contains the same entry ID for
1092 of 1118 rows. Where that entry begins with opcode
0x58, or with the independently proven two-byte 0x96 prefix followed by 0x58,
the arrival/current-map coordinates can be extracted without guessing.

For pack 0x50, the independently found 0x56 shapes using entry IDs 0x04, 0x0B
and 0x10 cross-link to record-0 entries carrying 0x58 coordinate setters,
including coordinates (29,55) and (34,49).

## Deliberate non-promotions

Opcode 0x04 is a proven VM pack-context switch for $126E, but it is not treated
as a global map transition because it does not itself write $0305.

Raw 0x53/0x56-shaped bytes outside the bounded policy are not cataloged.
Non-terminal shapes are retained only when a destination-entry/0x58 coordinate cross-link
provides an independent structural anchor.

## Related state fields

- $0305 is the global current-map pack field written by the C4:8B6A core used by opcode 0x56 and the opcode 0x53 wrapper.
- $126E is VM pack context. Opcode 0x04 changes $126E, so it is useful context
  but is not sufficient evidence for a global map transition.
- $12B4 is the resolved current source family/pack context used by source
  selection. In the confirmed runtime transition it converges with $126E after
  $0305 has already changed.
- normal opcode 0x50 writes primary selector state $139C/$139E/$139B
  (tileset/layout/variant).
- normal opcode 0x51 writes secondary selector state $139D/$139F.
- the destination configuration columns are therefore joined from the existing
  confirmed 0x50 selector catalog, not inferred from the transition operands.
- data/events/event_record_frame_catalog.csv is range-joined against each
  trigger address. Matching record IDs are stored in event_record.
- data/events/event_source_crosslink.csv is then joined by record ID and stored
  in event_sources. Rows outside the structural frame catalog keep event_record
  blank while vm_context preserves script pack/record/entry without guessing.

## Additional native $0305 writer inventory

Outside C4:8B7B inside opcode 0x56, exact STA-absolute $0305 byte patterns occur
at: C1:8255, C1:99ED, C1:EE43, C1:EE73, C5:9240, C5:9310, C5:CB81, C6:8027, C6:8191, C6:81B9, C6:82FD

These sites are retained as unresolved native writer candidates and are not
promoted into transition rows until native instruction boundary and source-value
flow are proven.

## Reproducible outputs

- data/maps/transitions/map_transition_candidates.csv
- data/maps/transitions/map_transition_candidates_summary.json
- docs/analysis/map_transition_candidate_catalog.md
- tools/python/catalog_map_transition_candidates.py

## Remaining blockers

- static source map/config is not inferred from script-pack identity
- five terminal 0x56 shapes and twenty-one terminal 0x53 shapes do not resolve a destination record0 entry
- non-terminal 0x53/0x56 shapes remain structural unless source instruction alignment is proven
- destination config stays null when destination pack record0/entry1 has multiple confirmed selectors
- 0x58 coordinate setter is promoted only at entry start or after proven two-byte opcode 0x96 prefix
- exact trigger/event opcode for the runtime-confirmed 0x2E -> 0x50 edge remains unidentified
- opcode 0x04 changes VM pack context $126E and is not promoted as a map transition by itself
- event-record crosslink coverage is partial; rows outside the structural frame catalog retain vm_context only
- eleven additional native STA $0305 sites remain outside the promoted opcode 0x53/0x56 transition grammar
