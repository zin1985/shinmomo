# Native boundary -> trigger crosslink cycle 2026-10-02 22:19 JST

## Selected theme
Close the highest-priority static task by checking whether the confirmed pack 0x2E native south-boundary path is already joined to event/trigger provenance in the canonical transition corpus.

## Confirmed facts
- `pack2e_centerline_return_closure_20261002.json` proves the native south-boundary chain for `cfg_t07_l015_v2`: current `(9,12)` attempts `(9,13)`, fails inclusive Y max 12, reaches `C1:8955 -> 81:895A`, and restores saved map state to pack 0x50.
- `source_transition_hotspots.csv` already contains `hotspot_native_pack2e_south_exit_candidate` at source region X=8..10,Y=12 with trigger type `native_out_of_bounds_saved_state_restore`, trigger address `C1:8955`, destination `cfg_t04_l008_v2`, arrival `(29,17)`.
- The forward counterpart is `hotspot_CC_1CDA`: source `cfg_t04_l008_v2` exact point `(29,17)`, opcode 0x69 coordinate predicate (`C4:9320`), B3 zero-skip to opcode 0x53 terminal at `CC:1CDA`, destination `cfg_t07_l015_v2`, arrival `(9,12)`.
- Therefore the pack2E witness is already closed as a bidirectional static provenance pair: VM exact-point trigger into the interior, native boundary/saved-state restore out of it.

## Interpretation
**Confirmed:** priority-1 `native map-boundary -> event/trigger crosslink` is complete for the pack2E witness and should not remain `next`.

**Strong hypothesis:** the existing hotspot corpus can serve as the seed schema for a generalized event-trigger region layer because it already distinguishes opcode 0x69 exact points, opcode 0x5D inclusive rectangles, VM transition terminals, and native boundary restore corridors.

**Unconfirmed:** this does not establish terrain/metatile passability or object occupancy collision. The bank89 `$0959/$09D9` lead remains a separate blocked provenance problem.

## ROM status
The designated Google Drive ROM was not available in this execution environment. No substitute ROM was used; size/SHA-256 verification was not performed. This cycle used only committed metadata and static evidence.

## Next
Generalize event-trigger region structure across the hotspot corpus, then extend transition -> event/trigger joins beyond the pack2E witness.