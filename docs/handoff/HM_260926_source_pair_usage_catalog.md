# Source-pair usage catalog handoff — 2026-09-26

## Scope

This cycle continued Priority 1 for G2/G4/G5: usage-driven text/source salvage.

Canonical ROM was checked from the pinned Drive folder. The Windows analysis copy used in this cycle is the canonical 2 MiB ROM and matches SHA-256:

F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98

The ROM header confirms FastROM HiROM map mode 0x31.

## Keep the overlapping-entry correction

Do not restore the old 7,877 complete-record model.

C7:0000 contains 250 increasing source entry points, but the next master pointer is not the current entry's end.

Historical weapon evidence proves family 0x16 / subindex 0xC8 reaches C7:A64D across later master roots.

The current inventory must therefore be driven by actual (family, subindex) selections.

## New cross-track bridge

For real CA:C000 script packs:

- indices 0x00..0x13 are reserved
- real pack intervals are 0x14..0xF9
- 0xFA is the final boundary/sentinel
- the CA pack index equals the C7 source-family index

Historical A4 analysis already proves:

A4 operand
-> C4:876D
-> C4:8554 resolves current CA:C000 pack index to $12B4
-> C4:A0C3 stores the A4 operand in $12B5
-> source resolver uses (family=$12B4, subindex=$12B5)

This is now externalized as a deterministic crosswalk.

## Usage catalog result

Reproducible tool:

tools/python/catalog_source_pair_usage.py

Canonical outputs:

- data/dialogue/source_pair_usage_catalog.csv
- data/dialogue/source_pair_usage_summary.json
- data/dialogue/source_family_script_pack_crosswalk.csv
- data/dialogue/source_family_script_pack_crosswalk_summary.json
- docs/analysis/source_pair_usage_catalog.md

Current counts:

- 2,238 unique evidence-backed source pairs
- 162 source families represented
- 2,202 high-confidence A4 script pairs
- 2,563 accepted A4 pattern hits
- 2,202 unique accepted A4 callsites
- 10 AE3A special-override pairs
- 7 historically confirmed static pairs
- 19 exact direct source calls
- 5 exact pairs enter the C4:A02D -> C4:9DE5 display-token pipeline
- 4 of those display-pipeline pairs select non-empty records
- 1 selects an empty record
- 1 confirmed dialogue pair
- 1 strong dialogue pair
- 6 confirmed non-dialogue pairs
- 2,225 pairs still have unknown visibility/context

The tool rejects source candidates that match A4-like byte patterns but cannot be reached through the actual source reader. This removes 88 false-positive candidates from families 0xF2 and 0xF7.

## Visibility warning

Do not treat all 2,238 pairs as dialogue.

The source system is shared by dialogue, UI/system text, descriptors and weapon/script resources.

C4:A02D is useful because it consumes records through C4:9DE5, previously identified as the next display token reader. Its exact pairs are strong visible-text-source evidence, but they are not automatically spoken dialogue.

## Progress impact

Top-level:

- G1: 47% unchanged
- G2: 60% -> 62%
- G3: 49% unchanged
- G4: 42% -> 44%
- G5: 47% -> 48%
- overall: 49.0% -> 50.0%

Legacy workstreams:

- Script VM/Event: 68% -> 70%
- Dialogue: 71% -> 74%
- Externalization: 70% -> 72%
- Whole-game reconstruction: 77% -> 78%
- weighted local maturity: 75.4% -> 76.2%

These increases reflect usage enumeration and cross-system linkage. They do not claim a complete rendered dialogue corpus.

## Next target

Priority 1:

Classify the 2,225 visibility-unknown source pairs.

Recommended order:

1. enumerate callers that enter display-window/token rendering paths;
2. map source pairs back to event/script pack and event conditions;
3. use runtime-observed dialogue roots to validate reachable visible pairs;
4. render only the player-visible subset through the existing dictionary/control decoder;
5. attach speaker, location and event provenance;
6. preserve descriptor/internal pairs as a separate resource class.

## Repository / artifact locations

GitHub source of truth:

zin1985/shinmomo

Primary outputs:

- docs/analysis/source_pair_usage_catalog.md
- data/dialogue/source_pair_usage_catalog.csv
- data/dialogue/source_pair_usage_summary.json
- data/dialogue/source_family_script_pack_crosswalk.csv
- data/dialogue/source_family_script_pack_crosswalk_summary.json
- tools/python/catalog_source_pair_usage.py
- docs/analysis/dialogue_source_family_catalog.md
- docs/analysis/rom_addressing_hirom.md
- progress/project_progress.json

Drive promotion must only happen after the final commit's GitHub Actions run succeeds.
