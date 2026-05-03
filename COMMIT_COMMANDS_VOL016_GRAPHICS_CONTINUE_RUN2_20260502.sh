#!/usr/bin/env bash
set -euo pipefail

git add docs/graphics/VRAM_LAYOUT_CLASSIFICATION_20260502_RUN2.md
git add docs/handover/SHINMOMO_VOL016_GRAPHICS_CONTINUE_RUN2_20260502.md
git add docs/handover/GOAL_PROGRESS_VOL016_GRAPHICS_CONTINUE_RUN2_20260502.csv
git add data/csv/current_vram_region_summary_20260502_run2.csv
git add data/csv/current_vram_tilemap_candidate_scores_20260502_run2.csv
git add graphics/battle/current_vram_4bpp_region_contact_sheet_20260502_run2.png
git add graphics/battle/current_vram_0000_7fff_4bpp_chr_atlas_20260502_run2.png
git add graphics/battle/current_vram_8000_ffff_4bpp_chr_atlas_20260502_run2.png
git add graphics/battle/current_vram_tilemap_candidate_rank*.png
git add tools/python/analyze_vram_layout_candidates_v1.py
git add manifest/MANIFEST_VOL016_GRAPHICS_CONTINUE_RUN2_20260502.csv
git add COMMIT_COMMANDS_VOL016_GRAPHICS_CONTINUE_RUN2_20260502.sh

git commit -m "vol016 graphics: classify current VRAM layout and add battle CHR analysis"
