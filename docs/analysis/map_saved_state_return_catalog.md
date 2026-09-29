# Saved-state map return candidate catalog

Updated: 2026-09-30

This catalog covers VM opcode 0x54 separately from explicit-destination
opcodes 0x53/0x55/0x56.

## Handler chain

- 0x54 dispatches to C4:8B4F.
- C4:8B4F calls 81:895A.
- 81:895A saves current pack $0305 into $15CF, sets transition bits in $DE,
  clears $13B8, and clears $1984.
- C1:97BC tests $13B8. When zero, C1:97C1 calls 81:8244.
- C1:8244 restores indexed map state from $151D..$1522.
- C1:8255 is the restore write into $0305.

This is therefore a destination-indirect transition family: unlike 0x53,
0x55 and 0x56, the destination is not encoded beside the opcode.

## Conservative extraction

Only exact bounded substreams ending in 54 B0 are cataloged. Raw 0x54 bytes
inside arbitrary data or non-terminal streams are not promoted.

Candidates: **51**
Unique script packs: **41**
Event-record crosslinks: **1**
Event-source crosslinks: **0**

The sole event-frame crosslink is pack 0xF9 / record 10 / entry 0x89 at
CE:1314, whose complete parsed body is exactly 54 B0. It belongs to structural
event frame FF9-L009. No event-source crosslink is currently available for
that frame, so its game-facing caller/source remains unresolved.

Source map/config and destination fields stay blank unless independently
proven. In particular, script pack must not be treated as source map pack.

## Runtime anchor

The existing 2026-09-29 runtime evidence confirms 旅立ちの村 / pack 0x50
returning to world map pack 0x4C at coordinate (54,237). That behavior is
compatible with saved-map-state restore, but the execution PC was not captured.
No individual 0x54 candidate is therefore marked confirmed.

The captured DP context before the reverse transition is **CD:FA4F**.
Static pack-range mapping places that pointer inside script pack
**0xF1 / record 1**. That script pack contains
**0** exact terminal 54 B0 candidates. This is negative
evidence against simply treating the captured DP pointer as the executing 0x54
stream. It also reinforces the rule that runtime map pack, script pack, and
controller/context pointer are separate layers.

## Outputs

- data/maps/transitions/saved_state_return_candidates.csv
- data/maps/transitions/saved_state_return_summary.json
- docs/analysis/map_saved_state_return_catalog.md
- tools/python/catalog_saved_state_return_candidates.py
