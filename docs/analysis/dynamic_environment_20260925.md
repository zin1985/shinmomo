# SNES dynamic-analysis environment survey (2026-09-25)

## Work host

- OS: Windows 11 Pro 64-bit, build 10.0.26200
- CPU: 16 logical processors
- Git: installed (`C:\Program Files\Git\cmd\git.exe`)
- Python: 3.10 (`C:\Users\zin\AppData\Local\Programs\Python\Python310\python.exe`)
- .NET: installed (`C:\Program Files\dotnet\dotnet.exe`)
- Docker: installed (`C:\Program Files\Docker\Docker\resources\bin\docker.exe`)
- CMake/Ninja/MSVC: not found in PATH
- GCC: not found; clang/make from Embarcadero are present but are not a verified Mesen build toolchain
- X11/Wayland/`xvfb-run`: not applicable/not found on this Windows host
- GUI: Windows desktop apps are available through remote desktop, but this Work
  terminal session cannot launch and supervise a new GUI process directly.
- AppImage/apt: not applicable to the host OS

## Existing emulator traces

The previous “no emulator” conclusion was incomplete. A recursive user-area
search found:

- `C:\Users\zin\Downloads\BizHawk-2.11-win-x64\EmuHawk.exe`
- `...\dll\snes9x.wbx.zst`
- `...\dll\bsnes.wbx.zst`
- `...\MesenCore.dll`
- Existing SNES Lua probes in Downloads and Documents.

BizHawk accepts `[rom]`, `--lua`, and `--chromeless`. The official Mesen2 2.1.1
Windows archive was also downloaded for evaluation, but its GUI process could
not be launched from this terminal session; it is not copied to the repository.

## Reusable path

`tools/dynamic/launch_bizhawk_goal13.ps1` accepts a ROM path and starts EmuHawk
with `bizhawk_goal13_probe.lua`. The probe emits JSON-lines summaries for frame
progress, CPU registers, WRAM, the four Goal13 execution targets, and `$0799`
writes. It never embeds a ROM path or emits a raw dump by design.

## Current limitation

The environment survey and launcher are complete, but the minimum runtime test
(CPU/frame/register/WRAM observation) could not be completed from this Work
terminal because GUI process creation is blocked by the remote execution
policy. The next operator action is to run the launcher on the connected
Windows desktop (or grant a GUI execution session), then inspect the JSONL.
This is an execution-channel limitation, not evidence that the ROM fails to boot.
