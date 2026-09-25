# Handoff: dialogue/source-family catalog + HiROM correction

Date: 2026-09-25
Priority: G2 / G4 / G5, rolling schedule priority 1

## Canonical input

- Drive canonical ROM folder was checked at cycle start.
- Canonical filename: `Shin Momotarou Densetsu (J)_original.smc`
- Expected size: 2,097,152 bytes.
- Windows analysis copy used in this cycle:
  `C:\Users\zin\Downloads\Shin Momotarou Densetsu (J)\Shin Momotarou Densetsu (J)_original.smc`
- SHA-256:
  `F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98`

No ROM, savestate, SRAM, raw VRAM/OAM/CGRAM, raw token corpus or full dialogue dump is committed.
## Critical addressing correction

The canonical ROM header at file `0xFFC0` contains:
- title `NEW MOMOTARO DENSETSU`
- map mode `0x31`

This confirms FastROM HiROM. The LoROM correction rule introduced during the earlier 2026-09-25 reconciliation is superseded.

New canonical labels use the high HiROM mirror:
- `0x039850 = C3:9850`
- `0x03F09A = C3:F09A`
- `0x041A10 = C4:1A10`
- `0x0487A2 = C4:87A2`
- `0x049D4D = C4:9D4D`
- `0x049E10 = C4:9E10`
- `0x070000 = C7:0000`

Historical file offsets remain valid evidence.
## Confirmed source-family architecture

`C7:0000` / file `0x070000` is a 250-entry 24-bit source-family master pointer table.

The table is exactly 750 bytes:
`0x070000..0x0702ED`

Entry 0 is `C7:02EE`, immediately after the table.
The last entry is `CA:A569`.

Every family begins with one reader-mode byte:
- mode 0 raw: 67 families
- mode 1 BD28: 55 families
- mode 2 BD98: 128 families
- other modes: 0
`C4:9D4D`:
- receives family id
- computes `id * 3`
- long-reads the 24-bit pointer from literal `$C7:0000,X`
- loads the first family byte into `$12AA`
- advances the pointer by one byte
- installs the payload pointer into `$B1/$B2/$B3`

`C4:9D91` initializes mode1 or mode2 reader state and calls `C4:9DBB`.
`C4:9DBB` skips zero-terminated source records; tokens `18..1F` consume one additional byte even when that byte is `00`.
## Offline extraction result

New deterministic extractor:
`tools/python/catalog_dialogue_sources.py`

Metadata outputs:
- `data/dialogue/source_family_catalog.csv`
- `data/dialogue/source_record_index.csv`
- `data/dialogue/source_family_summary.json`

Confirmed counts:
- 250/250 families decode to a clean boundary
- 45 mode-only empty placeholders
- mode0 records: 3,219
- mode1 records: 2,261
- mode2 records: 2,397
- total source records: **7,877**

All record index rows store token statistics and SHA-256, not full copyrighted text.
## Boundary and cross-checks

Families 0..248 end at the next master-table pointer and all have zero unterminated tail.

Family 249 begins at `CA:A569`. Its real compressed stream ends when a continuous `FF` padding run starts at file `0x0AA5B4`; the run is 6,732 bytes long through `0x0AC000`, the next known `CA:C000` table. This boundary is evidence-backed but remains marked as padding-derived rather than next-pointer-derived.

Positive dialogue cross-check:
- family 79 root `C8:A7DC`, mode 02
- payload `C8:A7DD`
- matches the previously restored Ginji-equipment dialogue source

Non-dialogue cross-check:
- family 22 `C7:8D13`
- already used by weapon/descriptor analysis

Therefore 7,877 source records are a shared source corpus, not 7,877 visible dialogue lines.
## Progress impact

Top-level:
- overall: **47.8% -> 50.2%**
- G2 complete dialogue salvage: **54% -> 66%**

G2 component changes:
- source readers/decoders: 85 -> 96
- root enumeration: 40 -> 70
- full corpus extraction: 30 -> 45
- encoding/display remains 95
- context linkage remains 35

Legacy workstreams:
- dialogue: 64 -> 76
- script-vm: 67 -> 68
- externalization: 68 -> 71
- weighted legacy maturity: 74.6 -> 76.0
## Next target

Priority 1 remains G2, but its shape changes.

Next cycle:
1. trace `$12B4` family-id producers and `C4:9D4D` usage provenance
2. classify the 7,877 records into player-visible text vs descriptor/non-dialogue resources
3. render only the player-visible canonical corpus
4. attach event / speaker / location provenance
5. validate coverage against runtime-observed dialogue roots

The canonical corpus must remain reproducible from the ROM and tools without committing the raw ROM or an unrestricted full copyrighted text dump.
