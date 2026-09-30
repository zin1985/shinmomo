# Saved-return origin crosslink - 2026-09-30

## Purpose

Source hotspot extraction and saved-state return are separate evidence tracks.

Opcode 0x53 does not merely switch destination pack. Its handler at C4:8B3F
first calls 81:8207, which saves the active map state into the indexed stack.
The saved fields include:

- current pack $0305
- current X/Y $1573/$157D
- secondary X/Y $15C3/$15C4
- entrance $13B9

Therefore an exact one-cell 0x53 source hotspot also proves the coordinate to
which a later saved-state restore returns.

This file does not invent the physical source location of the reverse exit.
It only records the already-proven saved destination of that reverse return.

## Native boundary-return mechanism

Static ROM analysis now proves this chain:

~~~text
C1:8943
  current $1573/$157D -> $030B/$030D
  -> JSL 81:81DD

81:81DD
  compare X against $15CA..$15CB
  compare Y against $15CC..$15CD
  CLC inside / SEC outside

C1:8953
  BCC return
C1:8955
  JSL 81:895A

81:895A
  save current pack into $15CF
  set transition bits in $DE
  clear $13B8 / $1984

C1:97BC..97C5
  if $13B8 == 0
  -> JSL 81:8244

81:8244
  restore indexed saved map state

C1:8255
  restore saved pack into $0305
~~~

The concrete runtime values of $15CA..$15CD for the two priority reverse
transitions were not captured. Therefore no reverse source hotspot is emitted
from this mechanism yet.

## Crosslink counts

There are 54 source hotspots whose transition is opcode 0x53.

- exact one-cell saved return coordinates: 36
- saved return regions whose exact cell depends on runtime position: 18
- rows with an independently confirmed runtime reverse edge: 2

## Priority closures

### 旅立ちの村 -> world reverse

Forward:

~~~text
world hotspot X=54..55 Y=237
  -> CC:0B08 / opcode 0x53
  -> 旅立ちの村
~~~

Runtime reverse is confirmed:

~~~text
旅立ちの村
  -> saved-state restore
  -> world (54,237)
~~~

The runtime return coordinate lies inside the exact forward saved region and
agrees with the saved-state model.

### cfg_t07_l015_v2 -> 旅立ちの村 reverse

Forward entry is now static:

~~~text
旅立ちの村 (29,17)
  -> CC:1CDA / opcode 0x53
  -> cfg_t07_l015_v2
  -> arrival (9,12)
~~~

Because the source hotspot is one cell, opcode 0x53 necessarily saves
旅立ちの村 coordinate (29,17).

The reverse runtime edge cfg_t07_l015_v2 -> cfg_t04_l008_v2 is already
confirmed. Its runtime arrival X/Y was not captured, but the saved-state return
target is statically exact at (29,17).

The remaining blocker is the physical **source exit coordinate inside
cfg_t07_l015_v2**, not the destination of the return.

## Outputs

- data/maps/transitions/source_saved_return_origins.csv
- data/maps/transitions/source_saved_return_origins_summary.json
- tools/python/catalog_source_saved_return_origins.py
