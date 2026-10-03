# Pack 0xB7 entry 0x02 structural boundary audit (2026-10-03)

## Confirmed facts

- `transition_CC_0F3B` targets pack `0xB7`, destination entry `0x02`, config `cfg_t47_l172_v2`.
- `primary_map_selector_catalog.csv` fixes pack `0xB7` record 0 at `CD:53AF..CD:5537`, entry `0x01` at `CD:53D4..CD:5409` (end exclusive).
- The transition catalog independently states that destination record-0 entry `0x02` exists. Therefore the next structural boundary for entry `0x02` is `CD:5409`.
- Same-config neighbor pack `0xB8` has entry `0x01` ending at `CD:56F1`; its entry `0x02` begins there with aligned opcode `0x58`, yielding `(52,16)`.

## Strong hypothesis

`CD:5409` is the exact byte boundary that must be decoded to recover pack `0xB7` entry `0x02` arrival behavior. The B8 witness suggests an aligned coordinate initializer is plausible, but B8's `(52,16)` must not be copied to B7.

## Unconfirmed

The opcode and operands at `CD:5409`, and therefore B7 entry-02 X/Y, remain unconfirmed because the designated Drive ROM was unavailable in this cycle. The next ROM-backed action is to verify canonical ROM size/hash and decode bytes beginning at `CD:5409`.
