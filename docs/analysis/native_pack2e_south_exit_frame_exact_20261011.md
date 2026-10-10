# Confirmed center-cell native return: pack 0x2E -> pack 0x50
Date: 2026-10-11
Repository: zin1985/shinmomo, normal main worktree

## What changed

The previous source hotspot for native out-of-bounds return from
cfg_t07_l015_v2 (pack 0x2E interior) to cfg_t04_l008_v2
(pack 0x50 village) was a **3-cell static corridor candidate**,
x=8..10 at y=12. Its previous reverse runtime fixture established
the destination but did not capture the exact source exit cell.

A controlled isolated hidden BizHawk replay now establishes **only
the center source cell x=9,y=12**, crossing south into x=9,y=13.
The adjacent x=8 and x=10 corridor cells remain unverified and
are not included in the confirmed hotspot.

## Reproduction

The existing game SaveRAM has a one-dan (level 1) continuation
record in 旅立ちの村. From the protected title/menu state, the
continue menu is reached and two separate A confirmations load an
interior map, pack 0x2E, initially x=9,y=9 at frame 661523.

The isolated dedicated emulator had been loaded from the saved
state vmtrace_tabidachi_pack2e_interior_20261011.State. It was
controlled using **exactly one frame of Down per command**,
never desktop keyboard/mouse input.

Validated frame-by-frame WRAM samples:

| frame | pack | player x,y | observation |
| --- | --- | --- | --- |
| 661523 | 0x2E | 9,9 | Before input |
| 661524 | 0x2E | 9,10 | Moving toward south exit |
| 661528 | 0x2E | 9,11 | Inside native map bounds |
| 661532 | 0x2E | 9,12 | Center exit cell in bounds |
| 661535 | 0x2E | 9,12 | Last recorded inside sample |
| 661536 | 0x2E | 9,13 | First out-of-bounds position |
| 661545 | 0x2E | 9,13 | Return transition still pending |
| **661546** | **0x50** | **29,17** | First destination map sample |

23 consecutive, gap-free one-frame traces cover start through
the first target pack switch. The final arrival coordinate
exactly matches the independently established reverse saved-return
position from CC:1CDA. The native source map bounds are x=0..19
and y=0..12 (ROM opcode 0x52, CB:DE74).

The target pack change can precede complete redraw of the
on-screen map, so WRAM and captured frame history are the proof,
not a screen-only guess. All raw traces/screens/savestates remain
outside the repo in the local hidden lab. The original protected
state was restored after the replay.

## Source and graph updates

- data/maps/transitions/pack2e_exact_south_exit_20261011.json:
  canonical identity, raw capture SHA-256, verified source/destination
  coordinate and first out-of-bounds/switch frames
- tools/python/verify_native_south_exit_replay.py:
  rejects missing/overlapping frames, forged input devices, out-of-range
  destinations and mismatch between per-step and trace data
- data/maps/transitions/source_transition_hotspots.csv:
  replaces the former 3-cell candidate source with a *single
  runtime-confirmed center hotspot* x=9,y=12. The 3-cell *possible*
  corridor remains recorded separately in the old analysis.
- data/maps/transitions/pack2e_south_boundary_to_tabidachi_20260930.json:
  updates exact source proof and cautions
- viewer/data/world.json: rebuilt from the existing source catalog
- scripts/test_native_saved_return_context.py and
  scripts/test_native_south_exit_replay.py: regression checks

After deterministic viewer rebuild:
- Map configurations: **149** (unchanged)
- Bound edges: **56** (unchanged)
- Native context for cfg_t07_l015_v2 -> cfg_t04_l008_v2:
  x=9,y=12,width=1,height=1, status confirmed_exact_cell.
- Runtime gate stays unknown without the actual saved-state
  return stack and position. No hypothetical story state is
  classified as currently navigable.

## CPU execution instrumentation failure to be fixed

The hidden BizHawk Lua bridge now registers **34** hooks:
18 VM-family and 16 native-boundary/WRAM map-write variants.
Despite an independently observed actual 0x2E->0x50 map switch,
**all execution and write callbacks reported zero hits**.

Consequently the hook system is NOT verified effective for this
BizHawk core and MUST NOT be used as proof that no opcode ran.
The 23 per-frame WRAM states do independently prove the native
map transition. Further work should diagnose BizHawk's execution
event domain/API or implement exact per-frame WRAM snapshots
inside the bounded trace command as a reliable fallback.

The native return mechanism is distinct from scripted VM opcode
0x56; do NOT increment VM56 handler runtime hit counts on this
native boundary. Official overall completion remains 51.4%.
