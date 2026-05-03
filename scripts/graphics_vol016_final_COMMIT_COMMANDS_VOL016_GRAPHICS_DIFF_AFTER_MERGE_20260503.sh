#!/usr/bin/env bash
set -euo pipefail

git add \
  README_VOL016_GRAPHICS_DIFF_AFTER_MERGE_20260503.md \
  docs/handover/SHINMOMO_VOL016_GRAPHICS_DIFF_AFTER_MERGE_20260503.md \
  docs/handover/GOAL_PROGRESS_VOL016_GRAPHICS_DIFF_AFTER_MERGE_20260503.csv \
  docs/graphics/BATTLE_CHR_OAM_ATTRIBUTION_PLAN_VOL016_20260503.md \
  docs/graphics/SPRITE_CLUSTERING_AND_CHR_RECONSTRUCTION_PLAN_20260503.md \
  docs/graphics/SPRITE_PNG_RECONSTRUCTION_PIPELINE_20260503.md \
  docs/graphics/STABLE_SPRITE_PNG_PIPELINE_RUN7.md \
  docs/graphics/SPRITE_ATLAS_PIPELINE_RUN8.md \
  docs/graphics/SPRITE_RENDERER_SYNC_SPEC_RUN10.md \
  docs/mapchip/FIELD_TILEMAP_METATILE_PIPELINE_AFTER_MERGE.md \
  data/csv/battle_oam_chr_region_schema_20260503.csv \
  data/csv/sprite_cluster_schema_20260503.csv \
  data/csv/oam_chr_mapping_schema_20260503.csv \
  data/csv/runtime_bridge_from_graphics_unified_schema_20260503.csv \
  data/csv/field_metatile_schema_20260503.csv \
  data/runtime_logs/current_after_merge_sample \
  tools/python/convert_graphics_unified_to_runtime_bridge_v1.py \
  tools/python/oam_chr_mapper_v1.py \
  tools/python/sprite_clusterer_v1.py \
  tools/python/render_sprite_clusters_v1.py \
  tools/python/build_field_metatiles_from_tilemap_v1.py \
  tools/lua/shinmomo_trace_graphics_runtime_bridge_v4_snes9x_20260503.lua \
  manifest/MANIFEST_VOL016_GRAPHICS_DIFF_AFTER_MERGE_20260503.csv \
  manifest/EXCLUDED_FILES_VOL016_GRAPHICS_DIFF_AFTER_MERGE_20260503.csv

git commit -m "vol016: add graphics diff after merge runtime reconstruction pack"
