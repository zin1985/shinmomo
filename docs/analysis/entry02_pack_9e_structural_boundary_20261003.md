# Pack 0x9E entry 0x02 structural boundary audit (2026-10-03)

## Confirmed facts
- `transition_CC_0C75` targets pack `0x9E`, destination entry `0x02`, config `cfg_t24_l125_v2`.
- Selector metadata fixes pack `0x9E` record0 at `CC:FFC5..CD:00A1`, entry01 at `CC:FFDE..CC:FFF7` (end exclusive), so entry02 begins at `CC:FFF7`.
- Same-config adjacent pack `0x9F` has entry01 ending at `CD:022A`; committed transition witness independently places its entry02 coordinate setter at `CD:022A`, yielding `(56,13)`.

## Strong hypothesis
`CC:FFF7` contains the pack-local entry02 initializer/route needed to recover 0x9E arrival behavior. The adjacent 0x9F witness supports aligned-boundary reuse as a structural grammar, not coordinate reuse.

## Unconfirmed
Opcode/operands at `CC:FFF7` and 0x9E entry02 X/Y remain unconfirmed because the designated Drive ROM was unavailable. Never copy `(56,13)` from 0x9F.
