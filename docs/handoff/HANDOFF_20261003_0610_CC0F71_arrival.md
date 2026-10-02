# Handoff: CC:0F71 arrival provenance

The event-trigger crosslink backlog is now 10 rows: 9 arrival-XY-only plus CC:1160 phase-dependent destination selection.

`CC:0F71` is closed statically. Its opcode-0x53 transition targets pack 0xBC entry 0x02 / cfg_t32_l144_v1. Independent CFG-reachable opcode-0x57 route `CD:B6A1` carries the same context pack 0xBC and destination entrance 0x02 and retains final coordinates (215,40). Treat `(215,40)` as strong committed arrival provenance for this trigger.

Drive指定ROMへアクセスできなかった and no alternate ROM was used. Next static target is `CC:0BD7`; ROM-enabled priority remains CC:1160 phase/state predicate recovery.
