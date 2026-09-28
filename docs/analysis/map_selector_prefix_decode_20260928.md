# Record0 / entry1 selector prefix decode

Updated: 2026-09-28

## Scope

The current unresolved primary-selector backlog contains 137 rows. Of those,
118 are record 0 / entry_id 0x01 rows that are explicitly seeded by state 0.

This pass decodes the prefix from each proven entry1 substream start to its
unresolved opcode 0x50 candidate.

The decoder is deliberately conservative. It advances only across normal-mode
opcodes whose byte length is independently established from C4 handler logic.
Unknown handlers, unresolved prior 0x50, 0x51, overrun, or misalignment stop
the walk immediately.

## Proven fixed lengths currently admitted

- 0x04 -> 2 bytes
- 0x08 -> 4 bytes
- 0x10 -> 2 bytes
- 0x11 -> 2 bytes
- 0x13 -> 2 bytes
- 0x15 -> 3 bytes
- 0x2D -> 2 bytes
- 0x33 -> 4 bytes
- 0x96 -> 2 bytes

No other opcode is guessed.

## Result

Targets analyzed: **118**

Exactly **56** prefixes reach the target 0x50 with no unknown byte boundary.
They occupy 56 distinct packs.

The seven fully aligned opcode-prefix forms are:

- `96 10 10 10 11`: 16
- `96 33 10 11`: 13
- `96 10 10 11`: 11
- `96 10 11`: 8
- `10 10 11`: 4
- `96 33 11`: 3
- `96 10 10 11 15`: 1

The remaining 62 stop conservatively at the first not-yet-approved opcode:

- A3: 23
- B3: 22
- E8: 6
- 3D: 4
- A0: 2
- E1: 2
- D0: 1
- B4: 1
- 64: 1

## Important non-promotion rule

`reached_target` proves instruction-boundary alignment only.

It does **not** yet prove that state 0 remains active until the candidate 0x50.
Before promotion, every decoded handler and relevant callee must be cleared for:

- writes to $1398;
- writes to $1399;
- direct or indirect transition through C0:C9E7.

Therefore the canonical confirmed-normal primary count remains **126** at this
checkpoint.

## Immediate next step

Fifty-five of the 56 aligned prefixes use only:

- 0x96
- 0x10
- 0x11
- 0x33

The remaining one additionally uses 0x15.

This sharply reduces the mode-persistence problem. The next static pass should
complete the call graph for those four common handlers first, then evaluate the
single 0x15 case separately.

## Reproducible outputs

- `tools/python/analyze_map_selector_prefixes.py`
- `data/maps/selectors/record0_entry1_prefix_analysis.csv`
- `data/maps/selectors/record0_entry1_prefix_summary.json`
