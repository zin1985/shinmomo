# 2026-10-04 02:10 JST - CI recovery / pack96 frontier

## Confirmed
- Canonical Drive ROM was not accessible; no substitute ROM was used.
- Previous Project CI failures terminate in `scripts/ci_validate.py` while parsing `progress/project_progress.json`.
- Restored the last parseable progress snapshot and rolled forward B9/pack96 evidence and schedule without changing percentages.
- Pack 0x96 entry02 structural start remains `CC:DBF2`.

## Strong hypothesis
- `CC:DBF2..CC:DC5C` is the highest-information bounded interval for resolving pack 0x96 entries 0x02..0x05 once the canonical ROM is available.

## Unconfirmed
- pack 0x96 entry02..05 opcodes, operands and arrival XY.

## Next
1. Canonical ROM available: verify 2,097,152 bytes and SHA-256 F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98, then decode `CC:DBF2..CC:DC5C`.
2. ROM unavailable: continue static boundary/xref work for entry03..05.
3. Then decode pinned B7/9E/AE/BD/B9 boundaries.
