# Group 2 character walk animation — 2026-09-29

Runtime world-map capture and OAM reconstruction now separate the overlapping actors cleanly.

## Confirmed runtime split

- visible object slot 2 is **Momotaro**. At the reference frame it uses group 2 / frame 4 and produces OAM entries 0 and 1.
- visible object slot 3 is **Ginji**. At the reference frame it uses group 2 / frame 33 and produces OAM entry 2.
- The previous mixed image was therefore Momotaro and Ginji rendered on top of each other.
- OBJ VRAM byte base for OBSEL=0x03 is confirmed by screen comparison as **0xC000**.

## Momotaro normal walk

B2C1 group-2 states 1–4 form four two-frame loops, each frame held for 32 ticks:

| direction | state | frames |
| --- | ---: | --- |
| right | 1 | 1, 2 |
| down/front | 2 | 3, 4 |
| left | 3 | 5, 6 |
| up/back | 4 | 7, 8 |

The directional assignment is supported by both the reconstructed silhouettes and one-frame runtime directional input captures. Down stabilized on frame 3, left on frames 5/6, up on frames 7/8, and right transitions into frames 1/2.

## Ginji normal walk

B2C1 group-2 states 14–17 form a second four-direction two-frame family:

| direction | state | frames |
| --- | ---: | --- |
| right | 14 | 31, 32 |
| down/front | 15 | 22, 33 |
| left | 16 | 6, 5 |
| up/back | 17 | 34, 35 |

Applying the runtime-proven Ginji tile displacement (+0x20 tiles for the current actor setup) reconstructs a coherent Ginji sprite in all eight frames.

## Engine correction

The visible-object group comes from `$0B25+slot`, not `$0B27+slot`. Also, `$0AE5+slot` is the currently selected B294 frame index, not the B2C1 animation-state number. The observation helper has been corrected while preserving the legacy `frame_state` field for downstream compatibility.

Raw WRAM/VRAM captures remain local-only.
