# Map transition candidate catalog

Updated: 2026-09-30

## Scope

This pass catalogs map-transition candidates only. It does not implement the
HTML viewer and does not integrate NPC or sprite data.

Canonical ROM SHA-256: F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98
Git HEAD used for generation: 944e26e14ac6c232ef3c40b601f4046c6b04e5cf

## Handler-level promotion

Normal VM opcode 0x53 dispatches to C4:8B3F, performs transition pre-work,
then directly JSRs C4:8B6A. It therefore shares the same two transition
operands and three-byte advance as the 0x56 core.

Normal VM opcode 0x55 dispatches to C4:8B56. It saves the current primary
X/Y pair on the CPU stack, calls 81:8244 to restore an indexed saved map state,
restores the current primary X/Y pair, and then falls through to the C4:8B6A
transition core. It therefore also consumes destination pack/entry operands.

Normal VM opcode 0x56 dispatches to C4:8B6A and is three bytes total.
The handler copies the old global map pack $0305 to $15CF, writes operand 1
to both $15D0 and $0305, writes operand 2 to $13B8/$13B9, calls
81:837F, clears $1984, and advances by three bytes.

Normal VM opcode 0x57 dispatches to C4:8BD4. When $13B8 != 0, its one-byte
operand is passed to 86:8000, the LoROM mirror of C6:8000. C6:8000 doubles
the route index, loads a route pointer from C6:8060, builds saved map-state
nodes, and leaves the final pack/X/Y/entrance active.

Normal VM opcode 0x58 dispatches to C4:8BE2. When $13B8 != 0, its four
operands are written to primary map coordinates $1573/$157D and secondary
map coordinates $15C3/$15C4. Existing map analysis independently identifies
these fields as current-map coordinates.

## Confidence policy

- confirmed: preserved runtime-observed transition evidence.
- strong_candidate: an exact bounded VM-substream tail of
  53 <destination_pack> <destination_entry> B0,
  55 <destination_pack> <destination_entry> B0, or
  56 <destination_pack> <destination_entry> B0, with the same destination
  entry present in destination record 0. Exact terminal
  57 <route_index> B0 is also strong_candidate when route_index resolves through
  the proven C6:8060 route table.
- structural_candidate: a terminal form whose destination entry is unresolved,
  or a non-terminal raw 0x53/0x55/0x56 shape retained only because its
  destination entry independently contains an aligned 0x58 coordinate setter.

The script-pack containing 0x53/0x55/0x56 is not automatically treated as the source map
pack. VM pack context and global map pack can differ, so static source map fields
remain blank unless independently proven.

## Counts

- total candidate rows: 1301
- confirmed: 3
- strong candidates: 1141
- structural candidates: 157
- rows with source configuration: 3
- runtime-confirmed static triggers: 1
- runtime-confirmed edges without observed trigger PC: 1
- rows with destination pack: 1301
- rows with unique destination configuration: 1066
- rows with destination X/Y: 778
- rows cross-linked to structural event records: 27
- rows carrying existing event-source xrefs: 17
- terminal 0x56 forms: 724
- terminal 0x56 forms with matching destination entry: 719
- terminal 0x56 forms with aligned destination 0x58 coordinates: 271
- non-terminal 0x56 coordinate-crosslinked structural rows: 25
- terminal 0x53 forms: 394
- terminal 0x53 forms with matching destination entry: 373
- terminal 0x53 forms with aligned destination 0x58 coordinates: 330
- non-terminal 0x53 coordinate-crosslinked structural rows: 94
- terminal 0x55 forms: 40
- terminal 0x55 forms with matching destination entry: 40
- terminal 0x55 forms with aligned destination 0x58 coordinates: 35
- non-terminal 0x55 coordinate-crosslinked structural rows: 12
- terminal 0x57 route-table forms: 2
- entry-start non-terminal 0x57 route-table forms: 8

Opcode 0x54 is destination-indirect: it requests a saved-map-state return
rather than encoding a destination beside the opcode. Its exact terminal forms
are cataloged separately in saved_state_return_candidates.csv.

## Runtime-confirmed anchor

Three runtime anchors are now preserved.

The earlier trace confirms cfg_t07_l015_v2 / pack 0x2E transitions to
cfg_t04_l008_v2 / pack 0x50. During that transition, $0305 changes first,
then $126E/$12B4 converge to 0x50, and selector 4/8/2 becomes active.
The exact event opcode address for that interior-to-exterior edge remains unknown.

The 2026-09-29 world-map trace confirms cfg_t01_l001_v1 / pack 0x4C at
coordinate (54,236) entering pack 0x50. At frame 14455 $0305 changes
0x4C -> 0x50. The only matching terminal 0x53 static row in script pack 0x4C
is record 2 / entry 0x77 / trigger CC:0B08, targeting destination entry 0x02.
That entry's aligned 0x58 setter at CC:1C4E predicts (29,55), and runtime
coordinates become exactly (29,55) by frame 14657. The visible destination
label is 旅立ちの村. This promotes CC:0B08 from strong_candidate to confirmed.

A second 2026-09-29 trace captures the reverse edge from 旅立ちの村 /
cfg_t04_l008_v2 / pack 0x50 back to cfg_t01_l001_v1 / pack 0x4C.
During a Down atomic capture, $0305 changes 0x50 -> 0x4C at frame 14787
while the active DP pointer remains CD:FA4F. By frame 14937 selector 1/1/1 is
active under pack 0x4C at coordinate (54,237). The edge is confirmed, but the
exact execution PC was not captured. C1:8244/C1:8255 saved-map-state restore is
therefore recorded only as a strong mechanism candidate, not as the observed
trigger address.

## Important structural finding

The second transition operand used by 0x53, 0x55 and 0x56 behaves as a
destination entry selector. Across the conservative terminal corpus,
destination record 0 contains the same entry ID for
1132 of 1158 rows. Where that entry begins with opcode
0x58, or with the independently proven two-byte 0x96 prefix followed by 0x58,
the arrival/current-map coordinates can be extracted without guessing.

For pack 0x50, the independently found 0x56 shapes using entry IDs 0x04, 0x0B
and 0x10 cross-link to record-0 entries carrying 0x58 coordinate setters,
including coordinates (29,55) and (34,49).

Opcode 0x57 forms a second transition grammar: the operand is a native route
index rather than a destination pack. Two exact terminal forms are currently
proven, route index 3 ending at pack 0x50 / (39,37) / entrance 0x02 and route
index 14 ending at pack 0x6A / (88,20) / entrance 0x02.

Eight additional non-terminal forms are promoted because 0x57 is byte 0 of the
parsed entry, independently proving the instruction boundary. All eight are
immediately followed by aligned opcode 0x58, so the route table supplies the
destination pack while 0x58 supplies the effective X/Y and secondary X/Y.
Raw non-terminal 0x57-shaped bytes elsewhere remain excluded.

## Deliberate non-promotions

Opcode 0x04 is a proven VM pack-context switch for $126E, but it is not treated
as a global map transition because it does not itself write $0305.

Raw 0x53/0x55/0x56-shaped bytes outside the bounded policy are not cataloged.
Non-terminal shapes are retained only when a destination-entry/0x58 coordinate cross-link
provides an independent structural anchor.

## Related state fields

- $0305 is the global current-map pack field written by the C4:8B6A core used by opcodes 0x53, 0x55 and 0x56.
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

These sites are separately inventoried because some are save/restore or
temporary-context writes rather than explicit destination operands. Runtime-only
edges may still use them as mechanism candidates without claiming the execution
PC was observed.

## Reproducible outputs

- data/maps/transitions/map_transition_candidates.csv
- data/maps/transitions/map_transition_candidates_summary.json
- docs/analysis/map_transition_candidate_catalog.md
- tools/python/catalog_map_transition_candidates.py
- data/maps/transitions/world_pack4c_to_pack50_entry02_20260929.json
- data/maps/transitions/tabidachi_village_to_world_pack4c_restore_20260929.json
- data/maps/transitions/saved_state_return_candidates.csv
- data/maps/transitions/saved_state_return_summary.json
- docs/analysis/map_saved_state_return_catalog.md
- tools/python/catalog_saved_state_return_candidates.py

## Remaining blockers

- static source map/config is not inferred from script-pack identity
- five terminal 0x56 shapes and twenty-one terminal 0x53 shapes do not resolve a destination record0 entry
- non-terminal 0x53/0x55/0x56 shapes remain structural unless source instruction alignment is proven
- remaining non-terminal raw 0x57 route-index shapes are not promoted until source opcode alignment is proven
- destination config stays null when destination pack record0/entry1 has multiple confirmed selectors
- 0x58 coordinate setter is promoted only at entry start or after proven two-byte opcode 0x96 prefix
- exact trigger/event opcode for the runtime-confirmed 0x2E -> 0x50 edge remains unidentified
- opcode 0x04 changes VM pack context $126E and is not promoted as a map transition by itself
- event-record crosslink coverage is partial; rows outside the structural frame catalog retain vm_context only
- native STA $0305 restore/context writers outside the explicit 0x53/0x55/0x56 destination operand grammar remain separately inventoried
