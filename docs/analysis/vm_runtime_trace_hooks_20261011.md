# Hidden BizHawk VM instruction execution trace (2026-10-11)

## Scope and safety

A new *opt-in* execution trace runs only in the isolated Shinmomo
background BizHawk instance. It is not a foreground keyboard/mouse
hook and does not watch the user's regular desktop.

Code:
- tools/remote_lab/shinmomo_remote_bridge.lua
- tools/remote_lab/shinmomo_lab.ps1
- tools/remote_lab/shinmomo_background_lab.ps1
- tools/python/audit_vm_execution_trace.py
- scripts/test_vm_execution_trace_audit.py

CLI after starting the dedicated hidden lab:

    & .\tools\remote_lab\shinmomo_background_lab.ps1 -Action vm-trace -Frames 60

Runs *neutral frames only*, 1..120 per command. No button input or
system-wide key events; 256-event cap and an explicit overflow counter.
Hooks are permanently registered after bridge startup but are
inert outside the bounded VM_TRACE command. Raw logs and their audit
reports are stored only in the local
%LOCALAPPDATA%\shinmomo-bg-lab\captures directory, not the repository.

## Hook inventory

Three variants for each monitored PC: bank 84, bank C4 in System Bus,
plus short-PC hook for compatibility with different BizHawk SNES
core callback address conventions.

- C4:8B6A: normal VM opcode 0x56 map transition handler
- C4:9517: opcode 0x25 asynchronous registration
- C4:9535: opcode 0x25 deferred callback
- C4:9803: opcode 0x39 handler
- C4:8FB3: opcode 0x40 handler
- C4:895E: normal VM pointer advance-by-two routine

Each execution hit is logged with frame, CPU PC/PBR/A/X/Y,
raw VM script pointer $98-$9A, active map pack $0305, mode
bytes $035F/$1398, entry $13B8, coordinates $1573/$157D
and saved return-context bytes $15CF/$15D0. Multiple executions
in the same frame are kept, even if they share the same PC.

The separate Python audit validates bounded neutral-frame intervals,
known hook types, no input, event cap and exact frame boundaries. It
reports candidate VM script pointer/catalog coincidences without
upgrading them to confirmed playable graph edges. The script pointer
and the Y offset remain distinct observations: a pointer match does
NOT prove current-map configuration, story flags or the actual
executed VM instruction unless separately grounded.

## Restart and first live test

The original isolated lab session was preserved as local savestate
vmtrace_preload_20261011.State, 93,267 bytes, before restarting
**only this dedicated** BizHawk process.

After loading the modified Lua bridge:
- New dedicated BizHawk PID 5396, hidden windows stayed hidden.
- Original frame 660050 was restored from savestate.
- 18 execution hooks registered; no registration errors reported.
- Neutral 2-frame test: 660050 -> 660052; 0 hits, 0 dropped.
- Neutral 60-frame test: 660052 -> 660112; 0 hits, 0 dropped.
- No input or foreground UI manipulation was used.

The 0-hit observations are NOT proof that the hooks would register an
execution event on this core: they show that the bridge installs hooks
and writes a valid zero-hit trace over a precisely bounded frame
interval. They also do not mean that a VM event never occurs, since
the test intentionally supplied no gameplay input.

## Reproduction

    $lab = ".\tools\remote_lab\shinmomo_background_lab.ps1"
    $trace = & $lab -Action vm-trace -Frames 60 | ConvertFrom-Json
    $rom = "$env:USERPROFILE\Downloads\Shin Momotarou Densetsu (J)\Shin Momotarou Densetsu (J)_original.smc"
    py -3 tools/python/audit_vm_execution_trace.py --trace $trace.path --rom "$rom"
    py -3 scripts/test_vm_execution_trace_audit.py

The local *_audit.json file is produced next to the raw trace, never
inside the Git repository.

## Next evidence frontier

Produce a deterministic event test on an isolated savestate where
actual normal VM 0x56 execution is expected (e.g. a known town exit)
and record which of 84/C4/short PC callback conventions fires.
Use saved state and bounded command-driven input, then restore
the state after the test. Do not bind a source map from a static
candidate alone. Specifically verify whether C4:9535 is invoked
after C4:9517 before promoting the CC:F4F9 deferred path.

The graph remains 149 configurations, 56 bound transitions, three
runtime-confirmed edges and official progress 51.4%. No new source
map binding was made in this work unit.
