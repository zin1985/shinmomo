# ShinMomo Remote Lab

A thin control layer for running repeatable Shin Momotarou Densetsu experiments from Chat through Remote Desktop Commander or Mole Remote.

It exposes nine operator commands:

1. **screen** - capture the current Windows virtual desktop to PNG.
2. **click** - click a Windows desktop coordinate.
3. **key** - send Windows keys, optionally activating a window first.
4. **gamepad** - inject SNES controller input through BizHawk for an exact number of frames.
5. **capture-memory** - capture a bounded BizHawk memory-domain range to local JSON.
6. **map-capture** - capture map-render artifacts plus a small derived map-state manifest.
7. **write-memory** - write a bounded WRAM/memory-domain byte range with before/after verification.
8. **save-state** - save a BizHawk savestate into the local-only lab state directory.
9. **load-state** - restore a named BizHawk savestate from the local-only lab state directory.

The ROM, savestates, screenshots, and raw memory captures are runtime-only. Do not commit them.

## Start BizHawk with the bridge

    .\tools\remote_lab\launch_bizhawk_remote_lab.ps1 -Rom "C:\ROM\Shin Momotarou Densetsu (J)_original.smc"

The launcher sets SHINMOMO_LAB_DIR and loads shinmomo_remote_bridge.lua.
Default runtime directory: %LOCALAPPDATA%\shinmomo-lab

## Commands

    # 1. Capture the whole Windows desktop.
    .\tools\remote_lab\shinmomo_lab.ps1 screen

    # 2. Click the GUI.
    .\tools\remote_lab\shinmomo_lab.ps1 click -X 840 -Y 620

    # 3. Send a Windows key. SendKeys syntax is accepted.
    .\tools\remote_lab\shinmomo_lab.ps1 key -WindowTitle "EmuHawk" -Keys "{ENTER}"

    # 4. Hold SNES Right for 12 emulated frames.
    .\tools\remote_lab\shinmomo_lab.ps1 gamepad -Buttons "Right" -Frames 12

    # Press multiple buttons for one frame.
    .\tools\remote_lab\shinmomo_lab.ps1 gamepad -Buttons "A,Right" -Frames 1

    # Atomic experiment: capture WRAM immediately before input, after each
    # input frame, and for two neutral post-input frames. The bridge performs
    # the whole sequence without host/RDC round trips between snapshots.
    .\tools\remote_lab\shinmomo_lab.ps1 gamepad `
      -Buttons "A" -Frames 1 -AtomicCapture `
      -Domain "WRAM" -Start "0x0799" -Length 128 -PostFrames 2

    # 5. Capture 0x80 bytes from SNES WRAM starting at $0799.
    .\tools\remote_lab\shinmomo_lab.ps1 capture-memory -Domain "WRAM" -Start "0x0799" -Length 128

    # 6. Capture map artifacts. manifest.json stores only small derived WRAM
    # selectors/pack state alongside local-only VRAM/CGRAM/OAM/screenshot files.
    .\tools\remote_lab\shinmomo_lab.ps1 map-capture -SceneTag "visited_location"

    # 7. Write a bounded memory range. Values are comma-separated bytes.
    .\tools\remote_lab\shinmomo_lab.ps1 write-memory -Domain "WRAM" -Start "0x1623" -Data "0x3C"

    # 8. Save a local-only BizHawk state without depending on GUI hotkeys.
    .\tools\remote_lab\shinmomo_lab.ps1 save-state -StateName "mole_remote"

    # 9. Restore the same local-only BizHawk state.
    .\tools\remote_lab\shinmomo_lab.ps1 load-state -StateName "mole_remote"

The map manifest includes current pack $0305, VM/resolved pack context $126E/$12B4,
mode $1398/$1399, and map selectors $139B..$139F. These values are intended to
join a visited screen to the confirmed ROM selector catalog without committing a
raw WRAM dump.

Each command emits compact JSON. screen returns the PNG path; RDC can then read that PNG so Chat can inspect the current GUI. capture-memory returns the local JSON path so the result can be analyzed without putting raw memory into Git.

## Intended Chat/RDC loop

    screen
      -> Chat inspects PNG
      -> click / key if GUI interaction is needed
      -> gamepad for frame-accurate in-game movement
      -> capture-memory around the event of interest
      -> analyze local JSON
      -> commit only derived findings / summaries

For game logic experiments, prefer gamepad over Windows key injection. It is deterministic at the emulator-frame level and does not depend on window focus.

When exact input-to-memory timing matters, use `gamepad -AtomicCapture`. The Lua bridge records a `before` snapshot, advances the requested input frame(s) itself, records each resulting frame, then optionally records neutral post-input frames. This avoids the hundreds or thousands of uncontrolled frames that can pass between separate RDC calls.

## Safety and limitations

- screen/click/key require an interactive Windows desktop. A locked/disconnected desktop session can prevent useful GUI capture or input.
- gamepad/capture-memory require BizHawk to be running with shinmomo_remote_bridge.lua.
- Memory addresses passed to capture-memory are relative to the selected BizHawk memory domain. For SNES work use WRAM when possible; use the existing System Bus probes when banked CPU addresses are required.
- One command at a time is intentional. This keeps experiments deterministic and prevents mailbox races.
- Capture length is capped at 4096 bytes per call. Large raw dumps are deliberately not the default workflow.
## Analysis cheat savestate

For reverse-engineering sessions that do not need to preserve normal progression, create a local-only analysis savestate from an existing base state:

    .\tools\remote_lab\create_analysis_save.ps1 -BaseState mole_remote -OutputState analysis_lv60_hien -Level 60

The first profile intentionally prioritizes fast navigation: Momotaro level is set through WRAM $1623, all Hien destinations are enabled through $1931..$1934, and Hien (spell id $33) is inserted into the first empty Momotaro spell slot at $44DA..$44E5. The script verifies every write before saving. Raw savestates remain under the local lab directory and are never committed.

This is an analysis profile, not a claim about canonical story progression. Additional party/items/castle unlocks should be added only after their WRAM/SRAM fields are independently verified.


## Background / hidden BizHawk analysis mode

Use the dedicated wrapper to keep the emulator and Lua Console hidden from the Windows desktop while invoking the bridge directly. This was validated on 2026-10-10 using the canonical ROM, an isolated runtime directory, and a running BizHawk 2.11 instance. Command controls and captures do not activate the emulator window.

```powershell
$bg = ".\tools\remote_lab\shinmomo_background_lab.ps1"

& $bg -Action start
& $bg -Action status
& $bg -Action step -Frames 180
& $bg -Action gamepad -Buttons "A" -Frames 2
& $bg -Action screenshot
& $bg -Action capture-memory -Domain WRAM -Start "0x0305" -Length 16
& $bg -Action map-capture -SceneTag "interior"
& $bg -Action save-state -StateName "before_event"
& $bg -Action load-state -StateName "before_event"
& $bg -Action hide
# Only when interactive inspection is deliberately requested:
& $bg -Action show
# Only stops the dedicated process that matches its PID registration:
& $bg -Action stop
```

The dedicated runtime root is `%LOCALAPPDATA%\shinmomo-bg-lab`. The launcher copies the existing BizHawk config to an isolated config path and verifies the canonical ROM size and SHA-256 before startup. The original BizHawk config and other emulator processes are not modified or stopped.

The `game-screen` command uses BizHawk `client.screenshot`, not Windows desktop screenshot. The bridge's `step` / `gamepad` advances exactly the requested frames, and `capture-memory` can inspect memory while BizHawk and the Lua Console remain hidden. Screenshot and raw state files remain local-only and must not be committed.

At the end of the 2026-10-10 test, a dedicated BizHawk instance remained running, with both windows hidden; `step`, `gamepad`, `screenshot`, `capture-memory`, `load-state`, and `save-state` all returned successfully. A captured intro/logo frame contained actual pixels, not just an empty PNG. A fully rendered gameplay view under a disconnected RDP session has not been verified yet.

This is hidden GUI emulation, not a true headless core. It still needs a live Windows user session and may behave differently if the session is logged out, RDP-disconnected, or the graphics device is reset. Do not use generic desktop `screen`, `click`, or `key` for unattended in-game experiments; use deterministic bridge commands. If screenshot becomes black, verify the current emulated frame and `client.screenshot` first before considering any desktop-based fallback.


## Read-only VM context capture (2026-10-11)

Run the isolated background lab as usual. While it is running, execute
tools/remote_lab/capture_vm_context_readonly.ps1 from PowerShell. It only
requests WRAM captures, checks that all four requests observed the same
emulator frame and stores a consolidated JSON snapshot in the LOCAL
background lab captures folder. It NEVER sends input, steps frames or
brings BizHawk to the foreground. If frame_consistent is false, values
are not co-temporal and must not be used as one executed event state.

Baseline evidence and caveats:
docs/analysis/vm_runtime_context_snapshot_20261011.md.


## Bounded VM execution trace (2026-10-11)

The **dedicated hidden** BizHawk lab now accepts:

    & .	ools
emote_lab\shinmomo_background_lab.ps1 -Action vm-trace -Frames 60

It advances 1..120 **neutral, no-input** frames and saves up to 256
CPU execution hook observations in the local lab captures directory.
Supported hooks: VM56 C4:8B6A, VM25 C4:9517/C4:9535,
VM39 C4:9803, VM40 C4:8FB3, pointer C4:895E.
System Bus 84/C4 and short-PC variants are registered. CPU hits
record script pointer, $0305 pack and $035F/$1398 mode. No hook is
considered proven to fire from registration alone.

Audit any local trace with:

    py -3 tools/python/audit_vm_execution_trace.py --trace LOCAL_JSON --rom CANONICAL_ROM

The audit writes a local sibling *_audit.json. It never upgrades a
source map to a confirmed graph link. Read
docs/analysis/vm_runtime_trace_hooks_20261011.md for evidence, caveats
and dedicated-emulator savestate rollback steps.


### Optional controlled in-emulator input

After saving a dedicated state for restoration, the isolated bridge
also accepts:

    & .\tools\remote_lab\shinmomo_background_lab.ps1 -Action vm-trace-gamepad -Buttons Down -Player 1 -Frames 8

This sends exact-frame SNES joypad commands to the hidden dedicated
emulator only; it does NOT use desktop keyboard/mouse focus. A valid
capture has input_device=isolated_snes_gamepad and the chosen
buttons/player, and can be audited with the same Python verifier.
Revert to the protected savestate afterwards; the trace itself
does not auto-restore state.


### Frame-exact native map-exit replay

The dedicated hidden lab can load the protected interior savestate
vmtrace_tabidachi_pack2e_interior_20261011.State (LOCAL only)
and step one Down frame at a time using vm-trace-gamepad.
The tools/python/verify_native_south_exit_replay.py script validates
the individual local input traces and produces metadata-only
data/maps/transitions/pack2e_exact_south_exit_20261011.json.
See docs/analysis/native_pack2e_south_exit_frame_exact_20261011.md.
Restore the original protected savestate after every experiment.

WARNING: 34 registered BizHawk VM/native execution and WRAM-write
hooks logged zero events even during a confirmed native map switch.
Their callback delivery is not validated on this core. Exact
per-frame WRAM samples, not zero-hit hooks, prove this return.


## Single-command contiguous frame-end WRAM traces (2026-10-11)

Use the isolated, hidden BizHawk for one-command captures:

    & .	ools
emote_lab\shinmomo_background_lab.ps1 -Action vm-frames -Frames 60
    & .	ools
emote_lab\shinmomo_background_lab.ps1 -Action vm-frames-gamepad -Buttons Down -Player 1 -Frames 23

One to 120 frames each. Per-frame data includes $0305 map pack,
$035F/$1398 VM mode, pointer $98-$9A, x/y, entry and saved map bytes.
All raw samples remain in the LOCAL captures directory, not Git.
Audit with:

    py -3 tools/python/audit_vm_frame_series.py --trace LOCAL_VMFRAMES_JSON

This uses the *working* frame-end hook, not the unverified
execution/write hooks. 35 registered execution/write hooks still
captured zero events on a confirmed native map switch. The recorded
WRAM changes are frame-exact but do NOT prove VM opcode execution.

Details, timing, and reproduction in
docs/analysis/hidden_frame_series_fallback_20261011.md.
Restore the originally protected dedicated emulator state after tests.


## Safe, reusable event-phase map transition probes

A parameterized hidden-lab runner captures input, VM state, map pack,
raw script pointer and post-load settled arrival as one local event.
It saves the current emulator state, loads a known source savestate,
records <=120 input frames and <=120 neutral frames, then **always
restores** the prior state before returning:

    & .\tools\remote_lab\probe_map_transition.ps1 -StateName vmtrace_world_pack4c_x55_y236_preentry_20261011 -Buttons Down -InputFrames 18 -SettleFrames 120

Verified outcome: world pack4C->village pack50 switch 663064, then
settled arrival x29,y55 at frame 663169. A negative replay that
does not produce a proven transition returns ok=false with
rollback_state_loaded=true. Failures never auto-create map links.
This only touches the *dedicated hidden* BizHawk and uses the
isolated SNES joypad; no foreground desktop input.

The audit is tools/python/audit_transition_phases.py, contract
tests scripts/test_transition_phases.py. See
docs/analysis/world_entry_event_phase_capture_20261011.md for
provenance and opcode/VM-pointer limitations.


## Raw selector tracking and verified spatial entrance examples

New hidden-lab vm-frames output uses schema_version=2 and records
WRAM 0x0306, 0x126E, 0x12B4, 0x12B5 alongside pack, script pointer,
event entry, player XY and saved pack bytes. Legacy schema1 logs
remain valid in the Python audit. Selector convergence is distinct
from pack-change and settled-coordinate frames; neither proves
CPU opcode address execution.

Proven repeatable examples:
- Tabidachi village (29,17) -> interior pack0x2E (9,12),
  pack switch frame 661935, selector frame 661966, stable frame 662010
- World (52,233) -> pack0x4D (17,37),
  pack switch frame 663189, selector frame 663218, stable frame 663271

See tools/python/verify_spatial_event_transition.py and
docs/analysis/runtime_spatial_two_entrances_20261011.md.
Raw trace files and local savestates stay outside Git.


## Pack4D native return verified in the hidden lab

Save state: vmtrace_pack4d_south_ready_x17_y37_20261011.State
(LOCAL-only after waiting until game input is accepted). Execute
25 frames Down, then 120 frames neutral with frame-series v2.
At frame 663382 the character steps outside the ROM-confirmed
native bound y37 into y38; frame 663387 switches pack4D to world
pack4C at (52,233); context converges at 663414.
Verify LOCAL captures with:
tools/python/verify_native_pack4d_world_return.py.

No ROM, screenshots, SaveRAM, savestates or raw trace JSONs are
uploaded to Git. Restore the protected hidden emulator savestate.


## Hien-enabled hidden world coordinate warp to known dungeon entrance

The existing analysis cheat profile unlocks Hien spell 0x33,
all four destination flags FF, and Momotaro LV60. To apply this
profile to an actual playable world save and shift the in-game
coordinates WITHOUT changing the desktop:

    & .\tools\remote_lab\create_hidden_hien_warp_state.ps1 -BaseState vmtrace_world_pack4c_x55_y236_preentry_20261011 -OutputState my_unique_world_warp_state -X 47 -Y 200 -Level 60 -NeutralFrames 16

The command checks it is using the hidden dedicated emulator,
backs up the original savestate, writes only a verified bounded
set of WRAM gameplay fields, checks readback, saves a new uniquely
named local cheat state and always restores the prior session.
Normal walking route to the coordinate is not proven by the warp.

From world (47,200) the actual controller Up crosses (47,199) to
pack0x91 dungeon おむすびころりん, arrival (71,59) after loader.
The original Hien destination name menu and actual spell casting
are still not verified even though the flags are unlocked.
See docs/analysis/hien_cheat_warp_omusubi_kororin_20261011.md.


## Reusable hidden scene warp and Omusubi cave floor transitions

Use the protected helper to inspect a known *loaded map* scene
without changing ROM/normal saves or the visible desktop:

    & .\tools\remote_lab\create_hidden_scene_warp_state.ps1 -BaseState analysis_pack91_arrival_71_59_20261011 -OutputState unique_scene_analysis_state -ExpectedPack 145 -X 75 -Y 54 -NeutralFrames 16

It checks the exact map-pack and hidden BizHawk, changes only
WRAM $1573/$157D, verifies the readback and restores the previously
loaded emulator state. The new local analysis save is never overwritten.
DO NOT mistake the cheat positioning for proof of walkable source route.

Verified route: Up from pack91 (75,54) -> hole (75,53), scripted
jump (70,8), automatic no-input shaft descent to (70,26), real Right
-> pack95 (22,8). Pack91 stair (71,59) also returns to world (47,199)
in this specific saved origin, requiring a second 120-frame neutral
window to prove settled coordinates. Full documentation:
docs/analysis/omusubi_cave_return_hole_and_pack95_20261011.md.


## Reverse cave stair pack95->pack91 (2026-10-11)

From the protected local analysis pack95 arrival at (22,8), execute
11 frames of actual SNES Down followed by 20 frames actual Up,
then two 120-frame neutral windows. Expected pack switch from 0x95
to 0x91 at frame664110 and stable cave(71,26) after frame664196.
Use tools/python/verify_pack95_reverse_stair.py against the raw,
continuous local frame captures to validate. The original world
entrance was prepared with a cheat, but no WRAM coordinate edits
were performed during this reverse controller event.
The second ladder tile (22,31) had no switch under both local
direction probes and is NOT universally ruled out as a trigger.


## Multi-world-hotspot hidden-lab probe

Use the ROM-derived target plan:
data/maps/transitions/world_hotspot_30scene_probe_plan_20261011.json

For isolated, bounded groups, run:

    & .\tools\remote_lab\batch_world_hotspot_probe.ps1 -Start 0 -Count 4 -Approach south

Only one process may control the hidden emulator at a time. The script
backs up the old state, reloads a playable world state per ROM hotspot,
cheat-positions the player one step south and uses real SNES Up.
Local records contain map-switch observations, destination XY and SHA
hashes of the original traces/screenshots, which remain local.
It restores the original save on normal exit. If a host process is
killed forcibly, manually restore the newest
world_hotspot_bulk_protect_*.State before any other interaction.
37/40 expected pack switches were observed in six restored batches.


## Recheck scene arrivals for actual reverse map switches (2026-10-11)

The protected batch script tools/remote_lab/batch_scene_reverse_exits.ps1
loads the exact prior local world-entry arrival state for each pack,
observes 12 neutral frames, presses actual SNES Down for 72 frames,
then records neutral windows. It never writes WRAM XY inside
the reverse test. Source world entry originally required an analysis
coordinate cheat. Resume only one isolated hidden instance at a time.

Three batches of 20 scenes yielded 14 world-return switches and
six inconclusive trials, with original dedicated emulator restored.
Raw frame logs, screenshots and savestates stay private/local.
Run tools/python/audit_scene_14_world_returns.py on the local
capture set to reconstruct exact SHA256-linked metadata, and
scripts/test_scene_14_world_returns.py for committed regression tests.


## Test unresolved pack returns with opposite SNES input

After the Down scene exit batch, the helper
tools/remote_lab/probe_six_unconfirmed_reverse_up.ps1 sequentially
rechecks the six pack states 0x96, 0xBD, 0xB9, 0xAB, 0x82, 0x60
using original analysis save states and normal SNES Up controls.
Each run saves and restores the prior isolated emulator state.
No WRAM XY writes occur during the reverse scene experiments.
The source's earlier world entrance was originally cheat-positioned.
Use tools/python/audit_six_scene_up_probes.py and
tools/python/verify_pack96_forced_motion.py to audit local raw frame
captures by SHA256. No original frame images or savestates are committed.


## Pack0x96 auto-descent, blocked title modal and verified escape

From the preserved arrival at (39,17) run the local only
tools/remote_lab/verify_pack96_neutral_no_buttons.ps1 to record neutral
204 frame control. The earlier saved Down/Up captures and Left/Right
probes agree frame by frame. After descending to (39,24), a game
location title modal blocks directional movement until a normal SNES
A/B/Start button dismisses it. The strict evidence uses A8+neutral64,
then real Up96 plus four consecutive neutral120 windows. Pack switches
0x96->0x4C at663807, first world XY(39,7) is transient, then
saved world(50,129) at663897 remains stable through664216.
The reproducible source fixtures, screenshots and raw frames are
local/private and restored to original hidden emulator state.
Commit only the derived SHA256-bearing JSON created by
tools/python/verify_pack96_fiveway_world_return.py.


## Five-scene modal / dialogue exploration

Run tools/remote_lab/probe_five_scene_modal_unlock_exits.ps1 in
bounded, nonoverlapping groups. It protects the original dedicated
emulator state, loads saved world-entered scene packs BD/B9/AB/82/60,
sends a genuine SNES A press and then each direction, recording raw
frame SHA256. tools/remote_lab/probe_village_dialogue_modal_A.ps1
replays multiple real A presses for packs82/60; pack82's verified
saved-world return requires twelve A interactions then Down96.
tools/remote_lab/verify_pack82_dialogue_world_return.ps1 checks a
further 360 stable world frames. All original save/screens/ROM/traces
stay local. Strict compiler:
tools/python/compile_five_scene_A_and_pack82_return.py.


## Pack0x60 long NPC sequence and transformed village
Load the research fixture village_dialogue_60_after_12_A_20261011
on the dedicated hidden BizHawk instance. The protected script
tools/remote_lab/probe_pack60_more_dialogue.ps1 executes a further
24 genuine A8+neutral20 cycles, records frame and screenshot SHA256
and four directional probes. Black cutscene, then a brown/withered
village were witnessed. Down96 from preserved after-A36 state
returns to world0x4C (59,155). Verify at least 360 stable neutral
frames via tools/remote_lab/verify_pack60_event_return_stability.ps1
and strict local forensic compiler
tools/python/audit_pack60_dialogue_event_return.py.
Never commit original ROM, raw captures, screenshots or savestates.


## Branching real gamepad dungeon routes

The safe bounded script tools/remote_lab/probe_three_dungeon_branch_routes.ps1
starts each of 24 routes from one of three independently validated
post-A scene savestates (BD/B9/AB), protects and restores the original
hidden emulator state, presses three real SNES directions 72 frames
each, then records 120 neutral frames and an actual screenshot. Raw
frame captures and snapshots remain local. After a successful run,
tools/python/audit_dungeon_three_pack_controller_routes.py rechecks
the exact raw SHA256, source packs, continuous WRAM samples, real
gamepad buttons, intermediate tile continuity and screenshot hashes.
This only proves traversed local corridors; none of those 24
experiments transitioned to a different scene pack.
