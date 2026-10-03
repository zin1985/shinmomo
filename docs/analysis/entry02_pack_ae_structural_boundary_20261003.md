# Pack 0xAE entry 0x02 structural boundary audit (2026-10-03)

## Confirmed facts
- `transition_CC_0DB8` targets pack `0xAE`, destination entry `0x02`, config `cfg_t11_l101_v2`.
- Selector metadata fixes pack `0xAE` record0 at `CD:35D0..CD:389E`, entry01 at `CD:361C..CD:3639` (end exclusive), so entry02 begins at `CD:3639`.
- Same-config pack `0xB0` has entry01 ending at `CD:4073`; committed transition witness independently places its entry02 coordinate setter at `CD:4073`, yielding `(41,12)`.

## Strong hypothesis
`CD:3639` contains the pack-local entry02 initializer/route needed to recover 0xAE arrival behavior. The 0xB0 witness supports aligned-boundary reuse as structural grammar, not coordinate reuse.

## Unconfirmed
Opcode/operands at `CD:3639` and 0xAE entry02 X/Y remain unconfirmed because the designated Drive ROM was unavailable. Never copy `(41,12)` from 0xB0.
