#!/usr/bin/env bash
set -euo pipefail

git add \
  README_VOL016_GRAPHICS_FINAL_HANDOVER_20260503.md \
  COMMIT_COMMANDS_VOL016_GRAPHICS_FINAL_20260503.sh \
  docs/handover/SHINMOMO_VOL016_GRAPHICS_FINAL_HANDOVER_20260503.md \
  docs/handover/THREAD_REPORT_FOR_MERGE_20260503.md \
  docs/handover/GOAL_PROGRESS_VOL016_GRAPHICS_FINAL_20260503.csv \
  docs/graphics/STATUS_RECONCILIATION_AND_CAVEATS_20260503.md \
  docs/graphics/FINAL_GRAPHICS_RECONSTRUCTION_PIPELINE_20260503.md \
  docs/graphics/MAP_VALIDATION_SPEC_20260503.md \
  docs/graphics/FINAL_DATA_LAYOUT_SPEC_20260503.md \
  docs/graphics/MAPCHIP_CANONICALIZATION_SPEC_20260503.md \
  docs/graphics/DMA_SEQUENCE_SYNCHRONIZATION_SPEC_20260503.md \
  docs/graphics/MAPCHIP_METATILE_GRAPH_SPEC_20260503.md \
  docs/graphics/MAP_LAYOUT_RECONSTRUCTION_SPEC_20260503.md \
  docs/graphics/METATILE_SEMANTICS_SPEC_20260503.md \
  docs/graphics/BATTLE_CHR_OAM_ATTRIBUTION_PLAN_VOL016_20260503.md \
  docs/graphics/SPRITE_CLUSTERING_AND_CHR_RECONSTRUCTION_PLAN_20260503.md \
  docs/graphics/SPRITE_PNG_RECONSTRUCTION_PIPELINE_20260503.md \
  docs/graphics/STABLE_SPRITE_PNG_PIPELINE_RUN7.md \
  docs/graphics/SPRITE_ATLAS_PIPELINE_RUN8.md \
  docs/graphics/SPRITE_RENDERER_SYNC_SPEC_RUN10.md \
  docs/graphics/VRAM_LAYOUT_CLASSIFICATION_20260502_RUN2.md \
  docs/mapchip/FIELD_TILEMAP_METATILE_PIPELINE_AFTER_MERGE.md \
  data/csv/*.csv \
  data/runtime_logs/current_after_merge_sample/* \
  graphics/battle/*.png \
  tools/lua/*.lua \
  tools/python/*.py \
  manifest/*.csv

git commit -m "vol016: finalize graphics mapchip handover after merge"
