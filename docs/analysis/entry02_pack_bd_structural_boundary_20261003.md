# Pack 0xBD entry 0x02 structural boundary audit (2026-10-03)

## Confirmed facts
- `transition_CC_0FA9` targets pack `0xBD`, destination entry `0x02`, config `cfg_t36_l150_v2`.
- The committed `primary_map_selector_catalog.csv` blob is `c27078a99823838bb3fdc61c8cac77958f0a0cbe`; its pack `0xBD` row fixes record0 at `CD:6C83..CD:6D78` and entry01 at `CD:6C9C..CD:6CBD` (end exclusive).
- Because the destination entry is independently confirmed as `0x02`, the exact structural decode start is `CD:6CBD`.

## Strong hypothesis
`CD:6CBD` contains or immediately enters the pack-local entry02 initializer/route needed to recover the 0xBD arrival behavior. This is the same structural grammar already observed for 0xB7, 0x9E and 0xAE, but no coordinate value is inferred from that grammar.

## Unconfirmed
Opcode/operands at `CD:6CBD` and 0xBD entry02 X/Y remain unconfirmed because the designated Drive ROM was unavailable.
