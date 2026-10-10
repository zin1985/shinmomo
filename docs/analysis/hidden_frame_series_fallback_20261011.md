# Hidden BizHawk single-command WRAM frame recorder
Date: 2026-10-11
Canonical repository: zin1985/shinmomo

## Why this exists

CPU onmemoryexecute/onmemorywrite hook registration was not evidence
of actual callback delivery on this BizHawk SNES core. Even with 34
registered handlers, a confirmed native map switch yielded zero events.
We registered another explicit WRAM-domain write hook for address
0x0305 (35 hook registrations total), but a repeated confirmed native
0x2E -> 0x50 transition still generated zero callbacks.

The cause of non-delivery is not proven. Do not infer that no opcode
executed from an empty hook log.

A dependable fallback records selected WRAM bytes at every
onframeend event. This is frame-by-frame state observation, NOT
CPU instruction tracing, and it does not prove VM opcode identity.

## Dedicated hidden-emulator commands

    & .\tools\remote_lab\shinmomo_background_lab.ps1 -Action vm-frames -Frames 60
    & .\tools\remote_lab\shinmomo_background_lab.ps1 -Action vm-frames-gamepad -Buttons Down -Player 1 -Frames 23

Both accept 1..120 exact frames. The latter sends SNES joypad input
ONLY inside the dedicated hidden BizHawk instance, never the
desktop keyboard or mouse. Every command writes before, after and
one sample per frame to LOCAL JSON outside GitHub.

Observed fields: frame, current pack $0305, mode $035F/$1398, entry
$13B8, script pointer bytes $98/$99/$9A, player position $1573/$157D,
and saved map context $15CF/$15D0.

The output declares:
- sampling_method = onframeend_WRAM_no_PC_hook
- cpu_execution_hook_delivery_proven = false

Audit any local capture with:

    py -3 tools/python/audit_vm_frame_series.py --trace LOCAL_VMFRAMES_JSON

The fail-closed verifier rejects missing or shifted frames, incomplete
final snapshots, unexpected input devices/buttons and invalid bytes.
It never promotes observed pack switches into new graph edges.

## Verified on real Shinmomo save data

| Segment | Frame window | Outcome |
| --- | --- | --- |
| Interior 0x2E -> village 0x50 | 661523..661546 (23 frames) | Switch at 661546, (9,13)->(29,17) |
| Village 0x50 -> world 0x4C | 662166..662186 (20 frames) | Switch at 662186, (29,56)->(55,237) |
| World 0x4C -> village 0x50 | 663046..663064 (18 frames) | Pack switches at 663064, stale coordinate (55,237) |
| Post-switch village settling | 663064..663184 (120 neutral frames) | First (29,55) at **663169** |

The village arrival position is committed 105 frames after pack
switch. Treat pack-change timestamp and *settled* destination
timestamp as separate observations.

All three pack-switch frames match the prior one-frame-at-a-time
replays, now using one command per segment instead of dozens.

## Reproduction and provenance

- tools/python/audit_vm_frame_series.py
- tools/python/verify_vm_frame_series_replays.py
- scripts/test_vm_frame_series_audit.py
- scripts/test_vm_frame_series_replays.py
- data/maps/transitions/tabidachi_frame_series_replay_20261011.json
  contains digests of four LOCAL raw capture files, not their bytes

The original protected emulator state was restored after tests.
No ROM, SaveRAM, raw traces or screenshots were committed. The
viewer remains 149 configurations and 56 bound edges, with overall
project progress 51.4%.

Next: use the same frame-end snapshots on scripted events, investigate
why CPU hooks do not fire and avoid making an unproven destination
or full-width exit corridor look confirmed.
