# Handoff: pack 0xAE entry 0x02 structural boundary

2026-10-03 20:12 JST

Confirmed: `transition_CC_0DB8` targets `0xAE:entry02`. Selector metadata places 0xAE record0 at `CD:35D0..CD:389E` and entry01 at `CD:361C..CD:3639`, fixing entry02 start at `CD:3639`. Same-config 0xB0 independently aligns its entry02 coordinate setter with its entry01 end at `CD:4073`, yielding `(41,12)`. Do not copy coordinates.

Drive designated ROM was unavailable in this cycle. Next with canonical ROM: verify 2,097,152 bytes and SHA-256 F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98, then decode `CD:5409`, `CC:FFF7`, and `CD:3639`. Static fallback: derive exact entry02 boundaries for unresolved packs 0xBD and 0xB9, then 0x96.
