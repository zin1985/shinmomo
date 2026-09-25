# Current goal progress — five-goal model

Updated: 2026-09-25

The historical Goal1..Goal20 percentages are no longer the top-level project metric. They remain useful as lower-level workstreams and evidence history.

Formal goal definitions live in `docs/project/PROJECT_GOALS_V2.md`.

## Current top-level baseline

| Goal | Progress | Current limiting factor |
|---|---:|---|
| G1 Program / logic complete analysis + ROM rebuild | **47%** | no full routine classification, real SNES ROM rebuild, complete save or audio subsystem spec |
| G2 complete dialogue salvage | **54%** | root enumeration, full corpus coverage, context/event linkage |
| G3 complete sprite salvage | **49%** | full entity inventory, canonical palette/asset export, all-scene validation |
| G4 complete event analysis | **42%** | selector matcher, complete event inventory, event graph |
| G5 complete portable specification | **47%** | missing subsystem specs, verification suite, save/audio/battle completeness |

Top-level overall: **47.8%**

Legacy workstream weighted maturity: **74.6%**.

These values intentionally measure different things.

## Recovered historical work included in this baseline

- `81:8D87` four return fields are largely characterized.
- condition `0x38/0x39/0x3A` set/clear/test-clear family is known.
- dialogue source reader at `C9:9E10/9E57`, dictionary/nested context handling and BD98 mode02 decoder are known.
- B294 sprite-frame groups and B2C1 animation scripts are already substantially externalized.
- visible-object active-list/OAM renderer and controller/work SoA are both well studied, but are separate layers.
- host-side recompilable C scaffold exists and builds.

These are **recovered evidence**, not equivalent amounts of new reverse engineering performed on 2026-09-25.

## Canonical corrections

- `$0799` is not a globally fixed visibility field.
- bank89 VM/object-script processing is directly relevant to the `$0799` path; it is not configuration-only.
- “41A10 selector matcher” and “target script VM reader” are different problems.
- the target VM reader at `89:87A2/87BD/87CF/87D4` is known.
- 398xx rows do not justify hunting a generic dedicated 9-byte reader.
- 41A10 currently has a segmented-resource interpretation, not a safely flat 160-record interpretation.
- dialogue extraction does not need to wait for the 41A10 matcher.
- controller/work SoA and AF33 visible-object pool must not be merged without an explicit handle mapping.

For details see:

- `data/audit/contradiction_register_20260925.csv`
- `docs/audit/FULL_REPOSITORY_AUDIT_20260925.md`
- `docs/analysis/cross_track_architecture_map.md`

## Current priorities

1. enumerate all dialogue roots and generate a canonical text corpus;
2. identify the segmented 41A10 selector matcher;
3. build the canonical sprite inventory/exporter;
4. generate the all-event catalog skeleton;
5. create a ROM rebuild gap manifest;
6. establish save/SRAM format;
7. establish audio/APU/SPC baseline;
8. expand weapon-special results into the full battle core.
