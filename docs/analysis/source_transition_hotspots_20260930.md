# Source transition hotspot catalog - 2026-09-30

## Result

This pass closes the first full source-side path:

    cfg_t01_l001_v1 / world grid (54..55,237)
      -> CC:0B08
      -> pack 0x50 entry 0x02
      -> cfg_t04_l008_v2
      -> arrival (29,55)

The source hotspot is not inferred from script_pack. The pack/config relation is
independently anchored by the existing runtime-confirmed world transition.

## Static predicate proof

Normal-VM dispatch table C4:87D4 maps opcode 0x5D to C4:908D.

C4:908D compares current map coordinates $1573/$157D with the four command
operands. It returns 1 through C4:8387 only when the current position is inside
the inclusive rectangle, otherwise 0 through C4:838C.

The exact record-2 body is:

~~~text
CC:0B01  5D 36 ED 37 ED   ; X=54..55, Y=237
CC:0B06  B3 05            ; zero => skip transition
CC:0B08  53 50 02         ; destination pack 0x50, entry 0x02
CC:0B0B  B0
~~~

Runtime evidence independently records Down from (54,236), the 0x4C -> 0x50
switch, and destination (29,55). The world structural layer has metatile 96/96
exactly at (54,237)/(55,237).

## Mechanical expansion

The same fail-closed exact grammar:

    5D xmin ymin xmax ymax B3 05 (53|56) dest_pack dest_entry B0

produces 19 source hotspot rows in pack 0x4C.

Only runtime anchor CC:0B08 is promoted to confirmed_runtime_and_static. The
other exact static rows remain strong_candidate. This catalog does not globally
equate script pack with source map.

Current counts:

- hotspots: 19
- source config resolved: 19
- source X/Y resolved: 19
- destination config resolved: 16
- destination coordinates resolved: 15
- confirmed_runtime_and_static: 1
- strong_candidate: 18

## Priority-route status

### World -> 旅立ちの村

Closed through source physical position, predicate, transition, destination
configuration and arrival coordinates.

### 旅立ちの村 -> world

Runtime transition is confirmed, but its exact source-side physical predicate is
not yet statically connected. Evidence points to saved-map-state restore
C1:8244/C1:8255, and the exact execution caller PC remains unobserved. No
rectangle is fabricated for this edge.

### cfg_t07_l015_v2 / pack 0x2E -> 旅立ちの村

Runtime transition is confirmed, but pack 0x2E contains no exact supported
0x5D + B3 + explicit 0x53/0x56 source-hotspot form. The source exit coordinate
therefore remains unresolved instead of being guessed from the visible doorway.

## Outputs

- data/maps/transitions/source_transition_hotspots.csv
- data/maps/transitions/source_transition_hotspots_summary.json
- tools/python/catalog_source_transition_hotspots.py
- graphics/viewer_validation/world_to_tabidachi_source_hotspot.svg

The SVG overlays the exact two-cell world hotspot and the runtime pre-entry cell
without changing viewer implementation.
