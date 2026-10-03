# Handoff: pack 0xBD entry 0x02 structural boundary

2026-10-03 22:12 JST

Confirmed: `transition_CC_0FA9` targets `0xBD:entry02 / cfg_t36_l150_v2`. Committed selector metadata places 0xBD record0 at `CD:6C83..CD:6D78` and entry01 at `CD:6C9C..CD:6CBD`, fixing entry02 start at `CD:6CBD`. Opcode/operands/XY remain unconfirmed.

Canonical Drive ROM was unavailable. Next ROM-backed order: verify size/hash, then decode `CD:5409` (B7), `CC:FFF7` (9E), `CD:3639` (AE), `CD:6CBD` (BD). If ROM remains unavailable, derive pack `0xB9` entry02 boundary, then pack `0x96` entries 0x02..0x05.
