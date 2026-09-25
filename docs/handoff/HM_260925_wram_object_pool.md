# WRAM object-pool handoff — 2026-09-25

## Cycle theme

Cross-bank reconstruction of the shared NPC/object WRAM pool.

## Confirmed architecture

The region `$0619..$0A18` is best modeled as a 64-slot object pool stored as 16 structure-of-arrays columns.

- 16 columns
- 0x40-byte column stride
- 64 slot indices
- total size 0x400 bytes

This explains the repeated bases:

`0619,0659,0699,06D9,0719,0759,0799,07D9,0819,0859,0899,08D9,0919,0959,0999,09D9`

## Bank89 overlay

- `$0759`: flags / dispatch-related field
- `$0799`: state flags/counter; bit7 transient latch
- `$07D9`: movement offset/work
- `$0819`: signed movement delta/work
- `$0859/$0899/$08D9`: 24-bit object-script pointer
- `$0919/$0959`: position-like pair
- `$0999/$09D9`: auxiliary work; bank89 uses them in geometry/state logic

The 24-bit pointer interpretation is confirmed by loading these three columns to DP `$B9/$BA/$BB` followed by script operand access through `[$B9],Y`.

## Cross-bank consequence

The later columns are not globally fixed-purpose. Bank85, bank87, and bank89 reuse the same slot work columns differently. Treat the structure as a shared object slot with handler-specific overlays, similar to a union.

## Progress

- WRAM structure: 62% → 67%
- Script VM/Event: 65% → 66%
- Externalization: 65% → 66%
- Whole-game reconstruction: 75% → 76%
- Goal13 NPC/OAM: 96% unchanged
- weighted overall: approximately 69.3% → 70.0%

## Next best global target

The highest expected cross-track information gain is now the `0x41A10` reader hunt because it can advance Script VM, Condition Dispatch, and Dialogue together.

Secondary targets are runtime validation of the 16-column object pool and the bank89 slot → active-list/OAM bridge.
