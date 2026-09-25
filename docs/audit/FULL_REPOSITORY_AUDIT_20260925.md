# Full repository audit and goal reset — 2026-09-25

> **Post-audit addressing correction (2026-09-25):** canonical ROM map mode is \`0x31\` FastROM HiROM. Any LoROM-corrected CPU labels in this audit are superseded; file offsets and byte evidence remain valid. See \`docs/analysis/rom_addressing_hirom.md\`.

## Scope and method

This audit was run against GitHub HEAD `0e8a2bda337cb355f5da7d014b1a4bb17d52fd4b` using a read-only temporary clone on the analysis machine.

The audit covered every tracked file, not only the current handoff:

- tracked files scanned: **1,276**
- text files scanned: **1,027**
- CSV files scanned: **449**
- scripts/source files scanned: **143**
- unique Markdown blobs read: **274**
- decode errors: **0**
- duplicate-content groups: **246**
- paths contained in duplicate groups: **643**
- `source_conflicts/` files: **26**
- nested ZIP paths still tracked: **18**
- raw `vram.bin` files found and removed during this audit: **2**

All Markdown content was read after deduplicating identical blobs. CSV/script files were scanned for schema/header, size, domain terms, stale-claim patterns and unresolved markers. High-impact tables/readers were additionally inspected directly.

## New top-level progress model

The old numbered Goals are retained as historical/local workstreams only. Project completion is now measured against five top-level outcomes.

| Goal | Formal baseline | Meaning |
|---|---:|---|
| G1 Program / logic complete analysis + ROM rebuild | **47%** | Significant reverse engineering exists, but complete 65816 classification, save/audio coverage and a real SNES ROM rebuild pipeline are missing. |
| G2 Complete dialogue salvage | **54%** | Text encoding/readers/decoders are strong; complete root enumeration, corpus coverage and context linkage are incomplete. |
| G3 Complete sprite salvage | **49%** | OAM/animation/frame structures are strong; canonical all-entity asset inventory/export/validation is incomplete. |
| G4 Complete event analysis | **42%** | VM/conditions are fairly mature, but the complete event inventory and graph are not built. |
| G5 Complete portable specification | **47%** | Architecture/schema work is useful, but several full-system specs and verification fixtures are missing. |

**Top-level overall: 47.8%**

The old weighted workstream maturity remains **74.6%** and is retained only as a local-analysis diagnostic. It must not be presented as whole-project completion.

## Why the formal overall moved below the old workstream score

The audit found that many historical percentages measured the maturity of a narrow question, not the final rebuild/salvage objective.

Examples:

- Goal12/GFX reached 99.5–100% in a graphics-thread sense, but that did not mean the whole game or all sprite assets were reconstructed.
- Goal13 reached 98–99% in several 2026-04 documents, but later runtime/static revalidation reopened the global interpretation of `$0799`.
- Weapon-special documents contain values from 18% through 98% as the local scope changed.
- text/display was near 99% while complete dialogue corpus salvage was still far from complete.

The new model credits the concrete evidence and discards incompatible historical denominators.

## Recovered progress that had been underrepresented

### 1. 81:8D87

Older rolling state still carried 30% in places, but the 2026-04-26 analysis already characterized:

- `$09`: available normal actors
- `$0A`: normal actors
- `$0C`: total logical objects
- `$0D`: special objects

Current workstream maturity of 85% is justified.

### 2. Condition dispatch

Historical work already showed the generic condition evaluator and a matched operation family:

- `0x38`: set selected bits
- `0x39`: clear selected bits
- `0x3A`: test selected bits clear

The common `$180A[entity-1] bit7` path is therefore much further along than the old 62% baseline implied.

### 3. Dialogue reader

Dialogue is not blocked on the 41A10 selector matcher.

Known source-side elements include:

- `C9:9E10` main source/control reader
- `C9:9E57` raw source byte reader
- `$B1/$B2/$B3` 24-bit source pointer
- dictionary handling
- nested source contexts
- `C0:BD98` mode02 bitstream/tree decoder
- offline mode02 chain dumper

The committed `C8:A7D0-A960` scan contains **760 logical CSV records**. This is valuable evidence, but it is a limited candidate scan rather than proof of whole-ROM corpus completion.

### 4. Sprite / animation structures

Previously the top-level tracker emphasized OAM rendering but underrepresented the reusable animation data already extracted:

- B294 sprite frame groups
- B2C1 animation group/state pointer tables
- 1,601 animation-state script records
- `$0E27` state
- `$0EA7` cursor
- `$0AE7` current frame
- `$0E67` duration
- OAM/CHR/palette reconstruction schemas

This materially raises G3 enabling capability, while still leaving complete asset enumeration unfinished.

### 5. Recompilable scaffold

The repository already contains a buildable host-side C99 scaffold:

- 165 item records
- 234 equipment records
- 160 branch records
- 64 + 64 macro rows
- 6 VM blob previews
- a host VM/runtime skeleton

This is important G1/G5 evidence, but it is explicitly **not** a full ROM rebuild.

## Canonical contradictions and stale interpretations

The machine audit found recurring stale-pattern families. Pattern hits are not all errors because corrective documents quote old statements, so the canonical resolution is kept in `data/audit/contradiction_register_20260925.csv`.

The most important resolved conflicts are:

1. **`$0799` is not a universal visibility authority.**
   It is a handler-dependent field/overlay. Bank89 bit7 processing is real, but direct OAM visibility authority is not proven.

2. **VM/script/event is not merely configuration-only for the `$0799` path.**
   Bank89 object-script handling participates directly.

3. **controller/work SoA and visible-object pool are different layers.**
   `$0619..$0A18` and the AF33 active-list pool must not be identified merely because both are around 64 slots.

4. **“41A10 reader” was ambiguous.**
   The selector matcher for `88:9A10` is unresolved; the target script VM reader at `89:87A2/87BD/87CF/87D4` is already known.

5. **398xx is not evidence of a dedicated 9-byte reader.**
   The rows are a macro grouping over normal VM instructions. The remaining problem is high-op semantics.

6. **41A10 is not safely modeled as one flat 160-record selector table.**
   Current evidence supports selector block A records 0..97, a 32-byte grammar break/control area, then selector-like block B from record 102.

7. **`0x39993` must not be promoted solely from old flat record numbering.**
   It requires revalidation inside the segmented-resource model.

8. **`0x300D3 -> 88:9A05` is a weak clue, not a confirmed matcher bridge.**
   The bytes exist, but descriptor +3..+5 is not universally a valid LoROM pointer.

9. **Old thread-local 95–100% values are not project completion values.**
   They remain historical evidence only.

10. **Legacy address labels mix file offsets and old CPU-bank conventions.**
    New work must record both file offset and corrected LoROM CPU address.

## Repository hygiene findings

### Resolved in this audit

Two tracked raw VRAM dumps violated the current exclusion rule:

- `data/runtime_logs/current/vram.bin`
- `data/runtime_logs/current_after_merge_sample/vram.bin`

Both were removed. Derived CSV/PNG documentation remains.

### Still open

There are **18 tracked ZIP files** despite the repository README saying nested ZIPs should not be committed. Many have expanded equivalents, but several packages need uniqueness verification before deletion. They are noncanonical and must not be used as the preferred source.

There are also 26 files under `source_conflicts/time_model_vol028/`. They deliberately preserve an alternate historical model and differ from their current counterparts. They are quarantine/reference material, not canonical state.

Opaque `graphics/fNNNNNN.*` aliases duplicate many named files. Named semantic paths should be preferred.

## Major coverage gaps exposed by the audit

### Audio/APU/SPC

The audit found **no dedicated audio subsystem analysis package**.

Keyword hits came from disassembly listings or from the new goal/audit documents, not a real audio reverse-engineering body.

G1/G5 must therefore explicitly include:

- CPU↔APU port protocol
- SPC upload/bootstrap
- audio driver
- music/SFX command format
- sequence/instrument/sample data regions

### Save/SRAM

There is no complete save/SRAM format specification.

The existing `data/hexdumps/save_restore_state.hex.txt` is object-state save/restore working code, not proof of the cartridge SRAM/save-file format.

Required work includes:

- SRAM mapping
- save slot structure
- checksum
- party/world/event persistence
- restore entrypoints and validation

### Battle core

Weapon-special analysis is deep but does not equal a full battle specification. Damage, target selection, enemy AI, status processing, turn resolution and battle state transitions still need an integrated model.

## Highest-value reusable data

Canonical starting points are indexed in `docs/audit/REUSABLE_ASSET_INDEX_20260925.md`.

Particularly valuable reusable datasets include:

- ROM/block/exact address maps and LoROM correction table
- 41A10 selector extraction and segmented-boundary evidence
- 398xx VM parsing and handler summaries
- condition/candidate/logical-actor xrefs
- B294/B2C1 animation/frame tables
- AF33/AFEC/active-list/OAM analyses
- mode02 dialogue decoder and chain dumper
- item/equipment table dumps
- weapon-special pack/target tables
- graphics/metatile/OAM/CHR schemas
- host-side recompilable C scaffold

## New rolling priorities

1. Complete dialogue root enumeration and canonical text corpus.
2. Identify the segmented 41A10 selector matcher.
3. Build canonical sprite inventory/exporter by joining B294/B2C1/OAM/CHR/palette.
4. Generate complete event catalog skeleton.
5. Build a ROM rebuild gap manifest for code/data/asset/unknown ranges.
6. Establish real save/SRAM format.
7. Establish audio/APU/SPC baseline.
8. Expand weapon-special work into the full battle engine.

## Audit rule going forward

At the start of each analysis cycle:

1. verify the canonical Drive ROM;
2. read the current top goals and latest handoff;
3. consult the reusable-asset index before writing new scans;
4. check the contradiction register before accepting historical labels;
5. distinguish recovered evidence, new analysis and reclassification;
6. update G1..G5 only when the corresponding completion criterion actually improves.

Historical thread percentages are never copied directly into top-level progress.
