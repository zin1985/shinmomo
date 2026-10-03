# Handoff: pack 0xB7 entry 0x02 structural boundary

2026-10-03 17:14 JST

Confirmed: `transition_CC_0F3B` targets `0xB7:entry02`. Selector metadata places B7 record0 at `CD:53AF..CD:5537` and entry01 at `CD:53D4..CD:5409`, so the exact entry02 boundary is `CD:5409`. Same-config pack B8 independently demonstrates the analogous boundary at `CD:56F1` is an aligned opcode `0x58` coordinate setter producing `(52,16)`. Do not copy B8 coordinates.

Next: with the designated Drive ROM only, verify size/SHA-256 and decode from `CD:5409`; if ROM remains unavailable, repeat the boundary derivation for `0x9E/0x9F`, then `0xAE/0xB0`.
