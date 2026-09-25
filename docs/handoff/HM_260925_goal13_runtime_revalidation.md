# Goal13 runtime revalidation handoff — 2026-09-25

## Input and runtime

- Canonical ROM source: Google Drive folder pinned in `progress/project_progress.json`.
- Expected file: `Shin Momotarou Densetsu (J)_original.smc`, 2,097,152 bytes.
- Windows analysis copy matched the known SHA-256 and was run with BizHawk/Snes9x.
- Runtime reached field gameplay. CPU callback and WRAM observation are operational.
- No ROM, savestate, raw VRAM/OAM/CGRAM dump, or copyrighted raw game data is committed here.

## Confirmed this cycle

- BizHawk bus-execute callback produced real 65816 execution samples.
- The `$0799,X` state-processing routines are inside a bank89 object-script processing chain.
- The nearby dispatcher handles multiple object-script command IDs and feeds the state-processing path.
- The existing active-list/OAM rendering findings remain useful as a separate downstream path.

## Reclassified

The older claim that `$0799` itself is the finalized visibility authority is no longer treated as confirmed.
The bit transitions are real, but a same-frame link to active-list/OAM output has not yet been demonstrated.

## Progress decision

- NPC/OAM Goal13: 99% → 96% (revalidation reopened).
- Script VM/Event: 64% → 65% (dispatcher mapping advanced).
- Weighted overall progress: approximately 69.3%.

## Next priorities

1. Trigger an NPC/event movement case and capture `$0799,X` state transitions.
2. Correlate those transitions with the known active-list/OAM path in the same frame/slot.
3. Complete the bank89 object-script dispatcher/handler semantics.
4. Resume the 0x41A10 reader hunt.
5. Continue weapon-special and WRAM-column classification.

See `docs/analysis/findings.md` and `progress/project_progress.json` for the current source of truth.
