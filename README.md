# Shin Momotarou Densetsu reverse-engineering project

GitHub `zin1985/shinmomo` is the single source of truth for the analysis project.

## Start here

Use the current audited documents in this order:

1. `docs/project/PROJECT_GOALS_V2.md`
2. `progress/project_progress.json`
3. `docs/handoff/HM_260925_goal_reset_full_audit.md`
4. `docs/audit/FULL_REPOSITORY_AUDIT_20260925.md`
5. `data/audit/contradiction_register_20260925.csv`
6. `docs/audit/REUSABLE_ASSET_INDEX_20260925.md`
7. `docs/analysis/cross_track_architecture_map.md`

Older handoffs remain historical evidence. Do not use their percentages or superseded labels as current truth without checking the contradiction register.

## Top-level goals

Project completion is measured by five outcomes:

- G1 Program / logic complete analysis + ROM rebuild
- G2 complete dialogue salvage
- G3 complete sprite salvage
- G4 complete event analysis
- G5 complete portable specification

The old Goal1..Goal20 labels are lower-level historical/workstream labels only.

## Progress

The machine-readable source is:

`progress/project_progress.json`

Top-level overall is computed from G1..G5. The old weighted track score is retained as a local maturity diagnostic and is not whole-project completion.

The public presentation layer is maintained separately in `zin1985/mole-mall` at:

`https://mole-mall.com/shinmomo/`

## Canonical ROM

The ROM itself is not stored in GitHub. Each analysis cycle checks the pinned Google Drive source recorded in `progress/project_progress.json`.

Do not substitute another ROM.

## Repository exclusions

Never add:

- ROM images
- SRAM or savestates
- raw VRAM/OAM/CGRAM dumps
- secrets
- new nested archive packages when expanded source/data can be committed instead

Two historical raw VRAM dumps were removed during the 2026-09-25 audit. Historical ZIP packages still tracked under archive paths are cleanup debt and are not canonical sources.

## Development workflow

```text
ChatGPT
→ GitHub (single source of truth)
→ GitHub Actions (validation / package generation)
→ Google Drive (deployment / review / distribution)
```

Only promote to Drive `Projects/shinmomo/latest` after the corresponding GitHub Actions run succeeds.
