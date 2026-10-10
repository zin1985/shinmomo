# Read-only hidden BizHawk VM context baseline (2026-10-11)

The separate background BizHawk lab remains running with its windows hidden.
A new noninteractive PowerShell command was added:

    & .\tools\remote_lab\capture_vm_context_readonly.ps1

It calls the existing background_lab.ps1 -Action capture-memory
four times, for WRAM ranges 0x0300..0x035F, 0x1390..0x13CF,
0x1570..0x158F and 0x15C0..0x15DF.

Each capture includes an emulator frame number. The script marks a
snapshot frame_consistent=true ONLY if all four frame numbers match.
It also retains paths to the original captures for later inspection.
A non-atomic result is clearly flagged; fields from different frames
must not be presented as one runtime state.

The script does not press buttons, step the emulator, load savestates,
show any window, reboot the lab or write any WRAM. JSON snapshot and
raw capture files are stored under the local background lab captures
directory OUTSIDE the Git repository.

## Smoke test

Read-only smoke test succeeded. All four captures were frame 660050.
At that frame the raw observed WRAM bytes were:

- $0305 map pack: F1
- $035F VM mode byte: 00
- $1398 special-dispatch byte: 00
- $13B8 destination entry byte: 04
- $1573 raw X byte: 09
- $157D raw Y byte: 04
- $15CF/$15D0 previous/new map pack bytes: 00/00

This is a **baseline observation only**. There is no execution hook
telling us that opcode 0x56, 0x25 or the related callbacks fired.
This snapshot alone cannot establish transition source/destination
or control-flow conditions. Do not interpret a zero VM mode byte as
evidence that a specific normal-mode event ran.

## Next stage

Extend the isolated BizHawk Lua bridge with bounded, optionally
activated execution hooks on the known normal VM handlers
(C4:8B6A, C4:9517/C4:9535, C4:9803, C4:8FB3), record the
actual CPU PC / normal-vs-special mode / current map WRAM on hits,
and correlate those hits with VM entry owners and snapshots.
Do not enable hooks without testing on the hidden dedicated
emulator. Save the emulator state before any deliberate replay;
do not interfere with the user's regular desktop.
