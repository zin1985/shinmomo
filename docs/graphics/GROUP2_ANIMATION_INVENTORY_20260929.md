# Group 2 animation inventory — 2026-09-29

Group 2 contains **229 animation states** and **124 unique frame/duration sequences**.

## Early state families

| state(s) | frames | duration | current interpretation |
| --- | --- | --- | --- |
| 1–4 | 1/2, 3/4, 5/6, 7/8 | 32/32 | Momotaro normal 4-direction walk |
| 5–8 | 9/10, 11/12, 13/14, 15/16 | 32/32 | alternate 4-direction two-frame set |
| 9 | 17 | 255 | fixed special pose |
| 10 | 18,19,20,21,22 | 5,5,5,5,255 | special sequence |
| 11 | 23,24,25,26,26 | 5,6,7,8,255 | special sequence |
| 12 | 27,28,27,28,27,29,30,27,28,27,28 | variable | longer special/event sequence |
| 14–17 | 31/32, 22/33, 6/5, 34/35 | 32/32 | Ginji normal 4-direction walk |

Frames 9–16 visually form another coherent four-direction pose set. Frames 17–22 still resemble Momotaro-oriented pieces, but frames 23 onward look fragmentary and include villager-like/person-like parts in the raw no-offset contact sheet. They must not be treated as one continuous Momotaro animation strip.

The runtime Ginji reconstruction proves that B294 frame definitions are not character identity by themselves: the same group/frame geometry can point at a different character through a per-object dynamic tile displacement. Group 2 is therefore better modeled as a shared OAM-layout / pose-definition pool used by multiple actors, with character identity resolved only after applying the object's runtime tile-base/offset and palette state.

## Wider inventory

Longer unique sequences include state 35 with 25 frame steps, states 34 and 12 with 11 steps, and later four-direction event families such as states 163–170 that begin with normal directional frames then branch into frames 181–196. These are candidate shared pose/event templates, not yet attributable to one character until runtime object binding and tile displacement are observed.

The two contact sheets committed with this note are intended as visual indexes, not canonical gameplay screenshots.
