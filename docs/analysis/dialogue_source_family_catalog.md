# Dialogue/source-family master catalog

Updated: 2026-09-25

## Confirmed source-family architecture

The common source-family master table is at canonical HiROM `C7:0000`, file offset `0x070000`.
It contains exactly 250 monotonically increasing 24-bit source pointers and occupies `0x070000..0x0702ED` (750 bytes).

Entry 0 is `C7:02EE`, which points immediately after the master table.
The final entry is `CA:A569`.

The first byte at every family root is a source-reader mode:
- mode 0: raw-byte reader at `C4:9E57`
- mode 1: `80:BD28` LZ-style byte reader
- mode 2: `80:BD98` bit/tree symbol reader

Mode distribution across all 250 families:
- mode 0: 67 families
- mode 1: 55 families
- mode 2: 128 families
- other modes: 0

## Resolver path

`C4:9D4D` receives a family index, multiplies it by 3, and reads the 24-bit pointer from `$C7:0000,X`.
It reads the first byte at that root into `$12AA`, advances the source pointer by one byte, and installs the payload pointer in `$B1/$B2/$B3`.

`C4:9D91` receives the record/subindex. It initializes mode 1 with `80:BCEE` or mode 2 with `80:BD87`, then calls `C4:9DBB`.
`C4:9DBB` skips zero-terminated records and treats tokens `0x18..0x1F` as two-byte kanji tokens, so a low byte of `0x00` is data rather than a record terminator.

This establishes the chain:

`family id -> C7:0000 master pointer -> mode byte -> source reader -> record index -> token stream`.

## Complete source-record inventory

The standalone extractor `tools/python/catalog_dialogue_sources.py` reproduces all three reader modes from the canonical ROM and emits metadata only.

Results:
- 250/250 families close at a defined boundary
- 45 families are one-byte mode-only placeholders with zero records
- mode 0 records: 3,219
- mode 1 records: 2,261
- mode 2 records: 2,397
- total zero-terminated source records: **7,877**
- all 250 families decode without an unterminated tail

The last family boundary is inferred at file `0x0AA5B4`, where a continuous 6,732-byte `FF` padding run begins and continues to the next known `CA:C000` table at file `0x0AC000`.

## Scope warning

The 7,877 records are **not equivalent to 7,877 player-visible dialogue lines**.
The same source framework is reused by non-dialogue resources. For example, family 22 at `C7:8D13` is already known from weapon/descriptor analysis.

A positive cross-check is family 79 at `C8:A7DC`: its mode byte is `02`, and the payload begins at `C8:A7DD`, matching the previously restored Ginji-equipment dialogue example.

Therefore the next G2 task is usage classification: determine which family/record references reach the player-visible text path, then attach event, speaker and location provenance.

## Canonical outputs

- `data/dialogue/source_family_catalog.csv`: one row per family, no dialogue text
- `data/dialogue/source_record_index.csv`: one row per source record with token statistics and SHA-256 only
- `data/dialogue/source_family_summary.json`: aggregate counts
- `tools/python/catalog_dialogue_sources.py`: deterministic extractor

ROM bytes, raw token dumps and full copyrighted dialogue text are intentionally not committed.
