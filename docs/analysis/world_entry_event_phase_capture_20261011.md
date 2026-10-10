# Tabidachi world-to-village event phase evidence
Date: 2026-10-11
Canonical repo: zin1985/shinmomo

## Problem closed

World -> village transitions may change WRAM map pack $0305 **well before**
the player coordinate is actually replaced by the destination arrival.

A new generic audit now correlates the bounded input window and its
contiguous no-input settling window, validates every frame, extracts
event/VM state changes and requires a stable arrival coordinate that is
distinct from the coordinate at map-switch time.

Script:
- tools/python/audit_transition_phases.py
- scripts/test_transition_phases.py

Reproducible local-only test runner:
- tools/remote_lab/probe_map_transition.ps1

The one-command runner checks that the dedicated emulator is hidden,
takes a rollback savestate, loads the requested fixture, captures two
consecutive WRAM frame-series files, runs the fail-closed Python
auditor, and **always restores** the prior emulator state before
returning. Failure to prove a transition returns ok=false, never
promotes an edge, and preserves logs locally. Rollback failure is a
hard error.

Example:

    & .\tools\remote_lab\probe_map_transition.ps1 -StateName vmtrace_world_pack4c_x55_y236_preentry_20261011 -Buttons Down -InputFrames 18 -SettleFrames 120

Each interval is capped at 120 frames, player 1 SNES input only; no
OS keyboard/mouse or visible emulator window operations.

## Actual runtime observations

The previously captured real source save is world cfg_t01_l001_v1,
pack 0x4C at (55,236). The x55 entry hotspot is reached at frame
663048, after input Down.

At frame **663064**, the same frame-end snapshot shows:

| WRAM field | Immediately before | At pack switch |
| --- | --- | --- |
| $0305 current map pack | 0x4C | **0x50** |
| $13B8 entry | 0x00 | **0x02** |
| DP $98-$9A raw pointer | CD:FA55 | **CC:07DE** |
| $15CF previous saved pack | 0x00 | **0x4C** |
| $15D0 target pack | 0x00 | **0x50** |
| Current player coordinate | (55,237) | (55,237) |

At **663169**, the *first stable new* destination coordinate is
**(29,55)** in pack 0x50. It remains unchanged through observed frame
663184. Delta: **105 frames** between map-switch and arrival.

The pointer **CC:07DE** is a raw DP script pointer at frame-end, not a
captured executing CPU PC. The separate static VM opcode 0x53
candidate for this world hotspot is **CC:0B08**. The two values must
not be mistaken for the same kind of address or used as proof that
the CPU executed CC:0B08. Memory-read framing may also occur after a
script has already initiated the transition.

The trace has only 18 input frames plus 120 no-input frames and
identical contiguous frame counters across the boundary.

Metadata-only evidence in repository:
- data/maps/transitions/tabidachi_world_entry_phase_evidence_20261011.json
- Raw JSON capture SHA-256 digests appear in that file.
- Screens, ROM, savestates and raw trace files remain LOCAL only.

## Test outcomes and safety

1. The successful hidden-lab replay returned switch 663064, stable
   arrival 663169/(29,55), and rollback_state_loaded=true.
2. An intentionally non-transitioning Right/1 frame plus 8 neutral
   frames returned **ok=false**, did not promote an edge, reported
   rollback_state_loaded=true, and returned the emulator to protected
   frame 660112, map 0xF1.
3. Python audit negative tests reject missing switch, ambiguous
   multiple switches, noncontiguous input/settling frame windows,
   unverified non-neutral settling, and unstable/absent destination.

The temporary Mole Remote connection did restart during an earlier
failed-script-output test. The fallback Desktop Commander connection
confirmed the emulator and clean working data survived. The probe
now writes expected Python errors to LOCAL files instead of streaming
them as a remote transport failure.

## Next work

For each dungeon or story event, load an independently identified
save position and replay a bounded input action plus neutral
settling. Collect map identity, source map config, opcode evidence if
actually observable, saved-return state, first switch frame and
settled destination. Do not extrapolate unknown story predicates,
source-map bindings or full exit widths. The 35 registered CPU/write
hooks still have unverified callback delivery.

Official progress unchanged at 51.4%. Viewer 149 map configurations,
56 bound edges. No new event source edge was promoted by this work.
