# ShinMomo Remote Lab

A thin control layer for running repeatable Shin Momotarou Densetsu experiments from Chat through Remote Desktop Commander.

It exposes five operator commands:

1. **screen** - capture the current Windows virtual desktop to PNG.
2. **click** - click a Windows desktop coordinate.
3. **key** - send Windows keys, optionally activating a window first.
4. **gamepad** - inject SNES controller input through BizHawk for an exact number of frames.
5. **capture-memory** - capture a bounded BizHawk memory-domain range to local JSON.

The ROM, savestates, screenshots, and raw memory captures are runtime-only. Do not commit them.

## Start BizHawk with the bridge

    .\tools\remote_lab\launch_bizhawk_remote_lab.ps1 -Rom "C:\ROM\Shin Momotarou Densetsu (J)_original.smc"

The launcher sets SHINMOMO_LAB_DIR and loads shinmomo_remote_bridge.lua.
Default runtime directory: %LOCALAPPDATA%\shinmomo-lab

## Five commands

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

    # 5. Capture 0x80 bytes from SNES WRAM starting at $0799.
    .\tools\remote_lab\shinmomo_lab.ps1 capture-memory -Domain "WRAM" -Start "0x0799" -Length 128

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

## Safety and limitations

- screen/click/key require an interactive Windows desktop. A locked/disconnected desktop session can prevent useful GUI capture or input.
- gamepad/capture-memory require BizHawk to be running with shinmomo_remote_bridge.lua.
- Memory addresses passed to capture-memory are relative to the selected BizHawk memory domain. For SNES work use WRAM when possible; use the existing System Bus probes when banked CPU addresses are required.
- One command at a time is intentional. This keeps experiments deterministic and prevents mailbox races.
- Capture length is capped at 4096 bytes per call. Large raw dumps are deliberately not the default workflow.
