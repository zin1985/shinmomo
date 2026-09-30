# Source transition hotspot catalog - 2026-09-30

## Result

This pass now has **55 source hotspots** on two independently runtime-anchored
source maps.

- cfg_t01_l001_v1 / world: 46
- cfg_t04_l008_v2 / 旅立ちの村: 9
- opcode 0x5D inclusive rectangles: 19
- opcode 0x69 exact points: 36

No row is attached to a map merely because script_pack equals a map pack. For
each scanned source pack, the pack/config relation must already exist in a
runtime-confirmed transition row.

## Predicate semantics

### Opcode 0x5D

Normal-VM dispatch C4:87D4 maps 0x5D to C4:908D. The handler compares current
map coordinates $1573/$157D against four operands and returns true only inside
the inclusive rectangle.

Exact accepted grammar:

~~~text
5D xmin ymin xmax ymax B3 05 (53|56) destination_pack entry B0
~~~

### Opcode 0x69

Normal-VM dispatch C4:87D4 maps 0x69 to C4:9320. The handler compares operand 1
with $1573 and operand 2 with $157D. It returns true only when both coordinates
match exactly.

Exact accepted grammar:

~~~text
69 x y B3 05 (53|56) destination_pack entry B0
~~~

The one-cell form is particularly useful for doors and facility entrances.

## Closed anchor: world -> 旅立ちの村

~~~text
cfg_t01_l001_v1
world hotspot X=54..55, Y=237
  -> CC:0B08
  -> pack 0x50 entry 0x02
  -> cfg_t04_l008_v2
  -> arrival (29,55)
~~~

CC:0B08 remains the only hotspot promoted to confirmed_runtime_and_static.
Runtime and static evidence independently agree on this path.

## New 旅立ちの村 entrance set

Pack 0x50 contains nine exact opcode-0x69 point predicates leading directly to
explicit 0x53 transitions. Their source coordinates are:

~~~text
(51,46) -> CC:1C7F -> cfg_t07_l009_v2
(46,32) -> CC:1C8C -> cfg_t07_l010_v2
(41,47) -> CC:1C99 -> cfg_t07_l014_v2
(34,44) -> CC:1CA6 -> cfg_t07_l016_v2
(41,39) -> CC:1CB3 -> cfg_t07_l012_v2
(34,35) -> CC:1CC0 -> destination config unresolved
(51,40) -> CC:1CCD -> cfg_t07_l013_v2
(29,17) -> CC:1CDA -> cfg_t07_l015_v2
(56,46) -> CC:1CE7 -> cfg_t07_l047_v2
~~~

Seven of the nine points land on metatile 112, a repeated door-position pattern
in map_008. The (29,17) point lies on the large northern structure and leads to
cfg_t07_l015_v2.

## 旅立ちの村 -> cfg_t07_l015_v2

This direction is now statically cross-linked:

~~~text
cfg_t04_l008_v2
source point (29,17)
  -> opcode 0x69 equality
  -> CC:1CDA / opcode 0x53
  -> pack 0x2E entry 0x02
  -> cfg_t07_l015_v2
  -> arrival (9,12)
~~~

It remains strong_candidate because execution of CC:1CDA has not been captured
at runtime.

The reverse edge cfg_t07_l015_v2 -> cfg_t04_l008_v2 is already runtime
confirmed, but its source-side trigger is still native/boundary-side and is not
fabricated here.

## 旅立ちの村 -> world blocker

The runtime edge cfg_t04_l008_v2 -> cfg_t01_l001_v1 remains confirmed.

Static follow-up found:

- no valid opcode 0x54 in pack 0x50 VM substreams;
- the return therefore is not a simple pack-0x50 0x54 tail;
- C1:97BC restores indexed saved map state through 81:8244 when $13B8 == 0;
- the exact movement/boundary path that raises the restore condition is still
  unresolved.

The map_008 road continuing to the lower edge is not sufficient evidence to
invent a bottom-edge hotspot, so no such row is emitted.

## Current counts

- hotspots: 55
- source config resolved: 55
- source X/Y resolved: 55
- confirmed_runtime_and_static: 1
- strong_candidate: 54

Destination-resolution counts are recorded in the generated summary JSON.

## Outputs

- data/maps/transitions/source_transition_hotspots.csv
- data/maps/transitions/source_transition_hotspots_summary.json
- tools/python/catalog_source_transition_hotspots.py
- graphics/viewer_validation/world_to_tabidachi_source_hotspot.svg
- graphics/viewer_validation/world_source_hotspots.svg
- graphics/viewer_validation/tabidachi_source_hotspots.svg
