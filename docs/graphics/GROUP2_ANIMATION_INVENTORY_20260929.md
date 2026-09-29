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

Frames 9–16 visually form another coherent four-direction character set. Frames 17–30 are structurally and visually different from normal walking and should remain semantically unnamed until a runtime event ties them to an action.

## Wider inventory

Longer unique sequences include state 35 with 25 frame steps, states 34 and 12 with 11 steps, and later four-direction event families such as states 163–170 that begin with normal directional frames then branch into frames 181–196. This strongly suggests group 2 combines normal movement with event/action animations for the same actor family.

The two contact sheets committed with this note are intended as visual indexes, not canonical gameplay screenshots.
