# Handoff: pack 0x9E entry 0x02 structural boundary

2026-10-03 19:12 JST

Confirmed: `transition_CC_0C75` targets `0x9E:entry02`. Selector metadata places 0x9E record0 at `CC:FFC5..CD:00A1` and entry01 at `CC:FFDE..CC:FFF7`, fixing entry02 start at `CC:FFF7`. Adjacent same-config 0x9F independently aligns its entry02 coordinate setter with its entry01 end at `CD:022A`, yielding `(56,13)`. Do not copy coordinates.

Next: designated Drive ROM only: verify size/hash and decode `CD:5409`, then `CC:FFF7`. If unavailable, derive the 0xAE/0xB0 structural boundary.
