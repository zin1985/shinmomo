# Source-family master catalog

Updated: 2026-09-25

## Confirmed architecture

The common source-family master table is at canonical FastROM HiROM `C7:0000`, file offset `0x070000`.

It contains exactly **250** monotonically increasing 24-bit entry pointers and occupies `0x070000..0x0702ED` (750 bytes).

Entry 0 is `C7:02EE`, immediately after the table. The final entry is `CA:A569`.

Every entry root begins with a source-reader mode byte:

- mode 0: raw-byte reader at `C4:9E57`
- mode 1: `80:BD28` LZ-style byte reader
- mode 2: `80:BD98` bit/tree symbol reader

Mode distribution:

- mode 0: 67 entries
- mode 1: 55 entries
- mode 2: 128 entries
- other: 0

## Resolver path

`C4:9D4D` receives the source-family index, multiplies it by 3, and long-reads the 24-bit entry pointer from literal `$C7:0000,X`.

It reads the first byte at the selected entry into `$12AA`, advances by one byte, and installs the payload cursor in `$B1/$B2/$B3`.

`C4:9D91` receives the source subindex and initializes mode 1 with `80:BCEE` or mode 2 with `80:BD87`, then calls `C4:9DBB`.

`C4:9DBB` skips zero-terminated logical records. Tokens `0x18..0x1F` consume one additional byte; that second byte is payload even when its value is `00`.

The stable selection key is therefore:

`(source_family, subindex) -> entry root -> reader mode -> selected logical record`

## Critical correction: entries are not bounded by the next master pointer

An earlier 2026-09-25 pass incorrectly used the next master pointer as the current family's end and counted 7,877 local fragments.

That boundary model is **superseded**.

Historical weapon analysis provides a direct counterexample:

- source-family / descriptor index `0x16`
- root `C7:8D13`
- payload starts at `C7:8D14`
- `$12B5=C8` is resolved by the real `9DBB` skip rule to `C7:A64D`

This crosses many later master-table entry points.

Therefore entries are overlapping source start points / checkpoints. The next master pointer is useful as a spacing hint only and is not an end boundary.

The previous `7,877` count must **not** be used as a complete source-record count.

## Special override path

`C4:AE3A` checks a 10-entry special `(subindex, family)` table before normal fallback.

On a match it installs an alternate pointer, including WRAM-backed sources, and returns Carry set. This explains why source selection cannot be modeled only as static ROM entry + sequential skip.

## Control-token recursion

The source reader's token family includes recursive source selection.

Existing token analysis shows token `02` enters the family-selection path around `C4:9F34`; on fallback it resolves through the same `C7:0000` master table and then applies `9DBB` record skipping.

Thus the master table is a shared source substrate used by dialogue and non-dialogue descriptor/script systems.

## Scope

The master table is **not** a list of player-visible dialogue lines.

Known examples:

- entry/family 79 root `C8:A7DC` has mode 02 and its payload at `C8:A7DD` matches a previously restored dialogue source.
- family/index `0x16` at `C7:8D13` is used by weapon/descriptor logic.

The next G2 task is to enumerate actual `(family, subindex)` usage provenance, then classify player-visible records.

## Canonical outputs

- `data/dialogue/source_family_catalog.csv`: 250 entry roots, modes and next-root spacing hints
- `data/dialogue/source_family_summary.json`: aggregate master-table metadata
- `tools/python/catalog_dialogue_sources.py`: deterministic root catalog + on-demand source-pair decoder

No raw ROM, unrestricted token corpus or full copyrighted dialogue dump is committed.
