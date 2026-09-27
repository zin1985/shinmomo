# Structurally anchored primary map-selector family

Updated: 2026-09-28

## Confirmed

CA:C000 script-pack roots (0x14..0xF9) were used to enumerate same-bank record-pointer boundaries before map-selector recognition. Across 4,092 bounded records, the confirmed setup sequence `10 0A 10 0B 11 09 50` occurs 65 times.

All 65 commands select tileset 7 and variant 2, covering 41 distinct layout IDs and 41 distinct primary configurations.

The stable interior configuration (tileset 7, layout 15, variant 2) occurs exactly three times in this structurally bounded family:

- pack 0x2E record 0: CB:DE63..CB:DE82, command CB:DE70
- pack 0x69 record 0: CC:5382..CC:53A8, command CC:5391
- pack 0xF7 record 17: CE:0F18..CE:0F47, command CE:0F2B

This upgrades the previous three raw-search occurrences to record-bounded script evidence.

## Strong evidence

The 65-command family is a coherent shared map-setup class because tileset 7 and variant 2 are invariant while layout IDs vary.

## Unresolved

This is not yet the complete opcode-0x50 corpus. Opcode 0x51 secondary selectors, other valid 0x50 forms, human map names, collision, warp, trigger and encounter layers remain open.
