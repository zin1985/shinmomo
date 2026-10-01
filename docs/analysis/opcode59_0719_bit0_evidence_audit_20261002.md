# opcode59 $0719 bit0 evidence audit (2026-10-02)

## Scope
Audit the previously proposed opcode59 `$0719` bit0 -> `$0759` execution-state connection against the current repository evidence. This note intentionally does not include ROM/raw copyrighted data.

## Confirmed
- `docs/analysis/event_controller_pointer_bridge.md` establishes opcode `0x59` staging five operands and `81:ADBD` storing the fifth operand into `$0719,X`.
- Current repository evidence documents several handler-specific meanings for `$0759`; these must not be merged across routines without a proven call/data-flow bridge.
- Existing derived documents do not establish a `C1:B309` bridge from opcode59-seeded `$0719` bit0 into `$0759`.
- The documented C1 keyed-dispatch path reloads `$0799/$07D9/$0819` and reaches `84:867D/8699`; it is not evidence for `$0759`.

## Correction
The earlier working claim that opcode59 `$0719` bit0 is confirmed to flow into `$0759` low execution-state bits is withdrawn. On current committed evidence that connection is **unverified**.

## Strong hypothesis
If a future ROM-backed disassembly proves that `C1:B309` reads the opcode59-seeded `$0719,X` low bit and transfers/tests it through `$0759`, the fifth operand may participate in a downstream execution-state gate. Until that bridge is reproduced, this remains a hypothesis only.

## Next evidence needed
1. Reproduce the exact `C1:B309` instruction window from the designated canonical ROM.
2. Establish controller ancestry from opcode59 allocation/setup to that code path.
3. Follow the first `$0759` consumer reached from the same path and separate it from unrelated WRAM overlay meanings.
4. Only then assign a game-facing bit0 label.

## Provenance / safety
This audit uses committed repository evidence only. No ROM, savestate, raw VRAM/OAM/CGRAM dump, dialogue body, or other copyrighted raw data is committed here.
