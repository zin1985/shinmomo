# Goal reset + full repository audit handoff — 2026-09-25

## Canonical project objective

The old numbered goals are now lower-level workstreams.

The five top-level goals are:

- **G1 47%** — Program/logic complete analysis + ROM rebuild
- **G2 54%** — complete dialogue salvage
- **G3 49%** — complete sprite salvage
- **G4 42%** — complete event analysis
- **G5 47%** — complete portable specification

Top-level overall = **47.8%**.

Legacy workstream weighted maturity remains **74.6%** only as an engineering diagnostic.

## Audit performed

A read-only clone of GitHub HEAD `0e8a2bda337cb355f5da7d014b1a4bb17d52fd4b` was scanned.

- 1,276 tracked files
- 1,027 text files
- 449 CSV files
- 143 source/script files
- 274 unique Markdown blobs read
- 0 decode failures
- 246 duplicate-content groups
- 26 source_conflict files
- 18 nested ZIP paths

Two raw VRAM dumps were removed from GitHub because they violate the current repository policy.

## Canonical documents after this cycle

Read these first:

1. `docs/project/PROJECT_GOALS_V2.md`
2. `progress/project_progress.json`
3. `docs/audit/FULL_REPOSITORY_AUDIT_20260925.md`
4. `data/audit/contradiction_register_20260925.csv`
5. `docs/audit/REUSABLE_ASSET_INDEX_20260925.md`
6. `docs/analysis/cross_track_architecture_map.md`

Older handoffs remain evidence but are not authoritative for percentages or superseded labels.

## Important recovered evidence

- 81:8D87 is already largely characterized.
- condition 0x38/0x39/0x3A family is already characterized.
- dialogue source reader is independent of 41A10.
- mode02 BD98 decoder + offline dumper already exist.
- B294/B2C1 animation/frame structures are substantially externalized.
- recompilable C scaffold exists and builds on host, but is not a ROM rebuild.

## Important corrections

- Never use `$0799 = global visibility`.
- Never use `VM/event = configuration-only` for the current Goal13 path.
- Never merge controller/work SoA with the AF33 visible-object pool without an explicit handle.
- Distinguish 41A10 selector matcher from the already-known target VM reader.
- Do not restart a generic fixed 9-byte reader hunt for 398xx.
- Treat 41A10 as segmented until proven otherwise.
- Treat `0x300D3 -> 88:9A05` as weak resource evidence only.
- Historical 95–100% thread declarations are local milestones, not top-level completion.

## Largest newly explicit gaps

- no dedicated audio/APU/SPC reverse-engineering package
- no complete save/SRAM specification
- no complete event catalog/graph
- no complete dialogue root inventory
- no complete canonical sprite inventory
- no SNES ROM rebuild pipeline
- battle core is much broader than weapon-special work

## Next analysis target

Priority 1 is **G2/G4/G5: complete dialogue root enumeration and canonical corpus** because the decoder/reader technology already exists and this is now a high-return salvage task rather than an unknown-decoder research problem.

Priority 2 is the segmented 41A10 matcher, then canonical sprite inventory/export.

## ROM policy

At every cycle start check the pinned Google Drive folder and the canonical file:

`Shin Momotarou Densetsu (J)_original.smc`, expected size 2,097,152 bytes.

Do not commit ROM, SRAM, savestate, raw VRAM/OAM/CGRAM or copyrighted raw dumps.

## Final operational status

- Repository validation on the analysis machine: **PASS**.
- Prior audited HEAD `5bae437c3f892ce092923927fad71266771291eb` completed GitHub Actions `Project CI and release` run **#64** with conclusion **success**.
- This handoff update is the final repository-content change for the audit cycle. Its own GitHub Actions run must succeed before Drive promotion.
- Mole Mall Shinmomo dashboard source now prefers formal `overall_percent` and renders G1..G5 above the legacy workstreams.
- Mole Mall dashboard JavaScript passed `node --check` at source HEAD `e116e26a26fca1e5895d79abbd29b0e277e39eb1`.
- Historical nested ZIP cleanup remains open; those ZIPs are noncanonical inputs.
