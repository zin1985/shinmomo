# Map transition candidate catalog

Updated: 2026-09-30

## Scope

This pass catalogs map-transition candidates only. It does not implement the
HTML viewer and does not integrate NPC or sprite data.

Canonical ROM SHA-256: F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98
Git HEAD used for generation: c6d8a91faefcb648374731787e34ce66ebb434dd

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

## CFG boundary grammar

The fail-closed 0x57 reachability walk now carries additional handler-level
length proofs without guessing unknown instructions:

- opcode 0x02 concrete operands 0x17, 0x1D, 0x25, 0x2D, 0x41, 0x5C and
  0x5E: C4:895E advances the caller by 2 bytes before the indirect call, and
  each inspected target returns through RTL.
- residual fixed lengths proven from handlers: 0x0A=4, 0x14=2, 0x1A=4,
  0x42=2, 0x4A=5, 0x4F=5, 0x66=4, 0x6C=2, 0x6F=2, 0x80=1, 0x89=1,
  compact B6=1, E-range 0xEF=1 and 0xF0=1.
- opcode 0x3D / C4:935C: subtype 0x02 consumes 3 bytes; 0x03/0x04/0x05/0x06
  consume 2 bytes; subtype 0x29 consumes 5 bytes.
- opcode 0x45 / C4:98AC: operand1 0 consumes 2 bytes; nonzero consumes 5.
- opcodes 0x7D and 0x8C both dispatch to C4:8963, whose first instruction is
  BRK. CFG treats either as a proven non-returning trap path and never invents
  fallthrough.
- opcode 0x2F / C4:968E: six operand bytes are consumed, so 7 bytes total.
- opcode 0x30 / C4:96CC: two 16-bit operands plus one byte are consumed, so
  6 bytes total.
- opcode 0x47 / C4:992F: four operand bytes are consumed, so 5 bytes total.
- opcode 0x52 / C4:8B16: operand1 below 0xFE consumes 5 bytes total; 0xFE/0xFF
  consumes 6 bytes total.
- opcode 0x5B / C4:8FF2: subtype at operand2 selects total length
  1 -> 4 bytes, 2 -> 5 bytes, 3/4 -> 3 bytes, all other values -> 5 bytes.
- opcode 0x67 / C4:924A: helper C4:9280 consumes four operand bytes and the
  caller consumes two more, so 7 bytes total.
- opcode 0x74 / C4:9488: all paths converge at Y=3, so 3 bytes total.
- compact A1 / C4:83CD consumes one operand and advances 2 bytes total.
- compact D0..DF use the D-range dispatcher at C4:8108 and consume two
  operand bytes, so 3 bytes total for the audited corpus.
- B0/B5 terminate a substream. B2 is an unconditional rel8 branch; B3/B4 add
  branch/fallthrough edges. B1 is a tail jump and never gains synthetic
  fallthrough.
- opcode A0 is a nested VM call. Caller continuation is allowed only when a
  recursive fail-closed walk has no unresolved blockers and finds at least one
  returning route. Proven 0x8C BRK routes terminate without fallthrough.
  Same-entry B1 tail targets are followed directly; external tail targets must
  independently close as returning substreams.

## Confidence policy

- confirmed: preserved runtime-observed transition evidence.
- strong_candidate: an exact bounded VM-substream tail of
  53 <destination_pack> <destination_entry> B0,
  55 <destination_pack> <destination_entry> B0, or
  56 <destination_pack> <destination_entry> B0, with a resolved destination
  entry, or an unresolved destination entry whose source opcode boundary is
  independently CFG-reachable. Exact terminal 57 <route_index> B0 is also
  strong_candidate when route_index resolves through the proven C6:8060 route table.
- structural_candidate: an unresolved terminal or non-terminal shape retained
  only while fail-closed source CFG analysis still contains blockers.

The script-pack containing 0x53/0x55/0x56 is not automatically treated as the source map
pack. VM pack context and global map pack can differ, so static source map fields
remain blank unless independently proven.

## Counts

- total candidate rows: 1295
- confirmed: 3
- strong candidates: 1292
- structural candidates: 0
- rows with source configuration: 3
- runtime-confirmed static triggers: 1
- runtime-confirmed edges without observed trigger PC: 1
- rows with destination pack: 1295
- rows with unique destination configuration: 1063
- rows with destination X/Y: 793
- rows cross-linked to structural event records: 22
- rows carrying existing event-source xrefs: 12
- terminal 0x56 forms: 722
- terminal 0x56 forms with matching destination entry: 721
- terminal 0x56 matches resolved outside record 0: 2
- terminal 0x56 forms with aligned destination 0x58 coordinates: 272
- non-terminal 0x56 coordinate-crosslinked retained rows: 20
- non-terminal 0x56 CFG-promoted strong rows: 20
- non-terminal 0x56 CFG-unreachable raw shapes dropped: 5
- non-terminal 0x56 CFG-blocked structural rows: 0
- terminal 0x53 forms: 392
- terminal 0x53 forms with matching destination entry: 390
- terminal 0x53 matches resolved outside record 0: 17
- terminal 0x53 forms with aligned destination 0x58 coordinates: 346
- non-terminal 0x53 coordinate-crosslinked retained rows: 93
- non-terminal 0x53 CFG-promoted strong rows: 93
- non-terminal 0x53 CFG-unreachable raw shapes dropped: 1
- non-terminal 0x53 CFG-blocked structural rows: 0
- terminal 0x55 forms: 40
- terminal 0x55 forms with matching destination entry: 40
- terminal 0x55 matches resolved outside record 0: 0
- terminal 0x55 forms with aligned destination 0x58 coordinates: 35
- non-terminal 0x55 coordinate-crosslinked retained rows: 9
- non-terminal 0x55 CFG-promoted strong rows: 9
- non-terminal 0x55 CFG-unreachable raw shapes dropped: 3
- non-terminal 0x55 CFG-blocked structural rows: 0
- unmatched terminal tails CFG-promoted by source reachability: 3
- unmatched terminal tails proven CFG-unreachable and dropped: 4
- unmatched terminal tails still CFG-blocked: 0
- terminal 0x57 route-table forms: 2
- entry-start non-terminal 0x57 route-table forms: 8
- branch-reachable non-terminal 0x57 route-table forms: 7
- all raw 57 <00..0F> shapes in parsed VM entries: 56
- promoted 0x57 transitions among those raw shapes: 17
- CFG-unreachable raw 0x57 shapes: 39
- reachable but unpromoted raw 0x57 shapes: 0
- unresolved / blocked raw 0x57 shapes: 0
- nested return targets proven by the closure walk: 14

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
destination entry selector. A pack-wide uniqueness audit across the conservative
terminal corpus finds 1151 of 1154 rows with exactly
one matching parsed entry anywhere in the destination pack. Of those,
19 resolve outside record 0. No terminal row has a
duplicated matching entry ID within its destination pack. The remaining
3 rows have no matching parsed entry anywhere in that
pack.

Where the unique entry begins with opcode 0x58, or with the independently proven
two-byte 0x96 prefix followed by 0x58, the arrival/current-map coordinates can
be extracted without guessing.

For pack 0x50, the independently found 0x56 shapes using entry IDs 0x04, 0x0B
and 0x10 cross-link to unique entries carrying 0x58 coordinate setters,
including coordinates (29,55) and (34,49).

The non-record0 extension is especially visible for destination pack 0xF7:
terminal 0x53 rows from packs 0xF3/0xF4 select entry IDs 0x02..0x07 and
0x0C..0x14. Each requested ID exists exactly once in pack 0xF7, in records
outside record 0, and the matched entries carry aligned 0x58 arrival setters.
The same unique non-record0 pattern resolves destination entries 0x0B/0x0C/0x0D
in pack 0xEE and entry 0x07 in pack 0xF0.

Opcode 0x57 forms a second transition grammar: the operand is a native route
index rather than a destination pack. Two exact terminal forms are currently
proven, route index 3 ending at pack 0x50 / (39,37) / entrance 0x02 and route
index 14 ending at pack 0x6A / (88,20) / entrance 0x02.

Eight additional non-terminal forms are promoted because 0x57 is byte 0 of the
parsed entry, independently proving the instruction boundary. All eight are
immediately followed by aligned opcode 0x58, so the route table supplies the
destination pack while 0x58 supplies the effective X/Y and secondary X/Y.
Seven further non-terminal 0x57 instructions are reachable from parsed entry
starts through the fail-closed CFG using proven B2/B3/B4 branch semantics and
independently bounded opcode lengths.

- pack 0x4E / record 0 / entry 0x03: CC:1916, route index 0x01. The path is
  D0 B9 13, D5 B8 13, E0, 96 00, then 57 01. The immediately following
  58 07 03 07 03 establishes effective coordinates (7,3).
- pack 0xDD / record 1 / entry 0x79: CD:B652, CD:B664 and CD:B676 with route
  indices 0x06, 0x07 and 0x08.
- the same pack/record/entry later reaches CD:B68D, CD:B6A1 and CD:B6B5 with
  route indices 0x09, 0x0A and 0x0B. Each is immediately preceded by opcode
  02 41. That opcode resolves to routine 81:EC60, while C4:895E advances the
  caller by two bytes before the indirect call and 81:EC60 returns through RTL,
  proving continuation to the following 0x57 instructions.

The remaining raw 0x57-shaped bytes are now fully closed by the same
fail-closed CFG. Across all parsed VM entries there are 56 raw
57 <00..0F> shapes: 17 are promoted transitions and the other
39 are unreachable from their parsed entry starts under the
proven grammar. There are 0 reachable-but-unpromoted
and 0 unresolved/blocked shapes. The earlier raw 0x57 backlog is
therefore closed rather than merely deferred.

## Deliberate non-promotions

Opcode 0x04 is a proven VM pack-context switch for $126E, but it is not treated
as a global map transition because it does not itself write $0305.

Raw 0x53/0x55/0x56-shaped bytes outside the bounded policy are not cataloged.
Non-terminal shapes first require a destination-entry/0x58 coordinate cross-link.
The fail-closed CFG then promotes reachable opcode boundaries to strong candidates,
drops coordinate-anchored raw shapes that are provably unreachable from the parsed
entry start, and retains only blocker-bearing shapes as structural candidates.

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
- 1 reachable terminal 0x56 shapes and 2 reachable terminal 0x53 shapes do not resolve a unique destination entry; transition pack is proven but arrival-entry semantics remain unresolved
- destination config stays null when destination pack record0/entry1 has multiple confirmed selectors
- 0x58 coordinate setter is promoted only at entry start or after proven two-byte opcode 0x96 prefix
- exact trigger/event opcode for the runtime-confirmed 0x2E -> 0x50 edge remains unidentified
- opcode 0x04 changes VM pack context $126E and is not promoted as a map transition by itself
- event-record crosslink coverage is partial; rows outside the structural frame catalog retain vm_context only
- native STA $0305 restore/context writers outside the explicit 0x53/0x55/0x56 destination operand grammar remain separately inventoried
