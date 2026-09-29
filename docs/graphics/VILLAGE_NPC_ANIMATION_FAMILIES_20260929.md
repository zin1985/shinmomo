# 旅立ちの村 NPC animation families — 2026-09-29

No-input runtime stepping binds several village actors to full animation families.

## Group 2: slow village NPC

Runtime slot 13 uses group 2 with signed tile displacement -0x20.

| state | direction | frames | ticks/frame |
| ---: | --- | --- | ---: |
| 216 | right | 237,238 | 64 |
| 217 | down | 239,240 | 64 |
| 218 | left | 241,242 | 64 |
| 219 | up | 243,244 | 64 |

During idle stepping, F239/F240 was observed while the actor's screen Y increased, confirming state 217 as down. The standard right/down/left/up state ordering then matches the two independently observed group-3 families below.

## Group 3: red-hat NPC

Runtime slot 17 uses tile displacement +32.

| state | direction | frames | ticks/frame |
| ---: | --- | --- | ---: |
| 5 | right | 9,10 | 16 |
| 6 | down | 11,12 | 16 |
| 7 | left | 13,14 | 16 |
| 8 | up | 15,16 | 16 |

F15 was observed while the actor moved upward under no player input.

## Group 3: purple/green NPC

Runtime slot 15 uses tile displacement +8.

| state | direction | frames | ticks/frame |
| ---: | --- | --- | ---: |
| 17 | right | 33,34 | 16 |
| 18 | down | 35,36 | 16 |
| 19 | left | 37,38 | 16 |
| 20 | up | 39,40 | 16 |

The actor changed from F39 while moving upward to F33 while moving right, directly anchoring the direction order.

## Group 7: blue NPC

Runtime slot 22 uses tile displacement +136. It alternated F15/F16 every 32 frames while its screen position remained unchanged. This is currently classified as a stationary idle pair, not a proven directional walk cycle.

## Consequence

Village actors use several animation clocks: 16 ticks for the group-3 walkers, 64 ticks for the slow group-2 NPC, and 32 ticks for the stationary group-7 idle pair. NPC behavior is therefore not represented by one universal walk cadence.
