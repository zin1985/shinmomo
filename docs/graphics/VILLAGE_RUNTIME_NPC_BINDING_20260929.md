# 旅立ちの村 runtime NPC binding — 2026-09-29

A live pack `0x50` capture was used to bind visible village actors back to the object manager and sprite renderer.

## Confirmed visible actors

| slot | group | frame | tile offset | runtime interpretation |
| ---: | ---: | ---: | ---: | --- |
| 13 | 2 | 240 | -0x20 | village NPC; member of the F237–F244 directional family |
| 22 | 7 | 15 | +136 | village NPC |
| 15 | 3 | 35 | +8 | village NPC |
| 17 | 3 | 11 | +32 | village NPC |
| 23 | 5 | 6 | +154 | flame/effect-like object, not a person |

Derived sprite reconstructions were visually compared against the live game screen and match the corresponding actors.

## Group 2 F237–F244 promotion

States 216–219 select:

- state 216: F237/F238, 64 ticks each
- state 217: F239/F240, 64 ticks each
- state 218: F241/F242, 64 ticks each
- state 219: F243/F244, 64 ticks each

At runtime in 旅立ちの村, slot 13 used group 2 / frame 240 with signed dynamic tile displacement -0x20. This directly connects the F237–F244 family to a village NPC. The family is therefore no longer just a visual candidate.

## Architectural consequence

Village characters are distributed across multiple sprite groups and dynamic tile displacements. B294 group/frame is best treated as shared pose/layout data. Character identity requires the runtime tuple:

`object slot + sprite group + frame + tile displacement + palette/attr`

This same model already separates Momotaro and Ginji correctly.

Raw screenshots and raw memory captures remain local-only; only derived reconstruction images and scalar bindings are committed.
