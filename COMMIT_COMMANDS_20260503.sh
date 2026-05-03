#!/usr/bin/env bash
set -euo pipefail

# From repository root:
# unzip shinmomo_vol017_core_graphics_merged_20260503_commit.zip
# cp -R shinmomo_vol017_core_graphics_merged_20260503_commit/* .

git status
git add   docs/handover   docs/reports   docs/graphics   docs/mapchip   data/csv   data/hexdumps   data/runtime_logs   graphics   tools/python   tools/lua   shinmomo-analysis   recompilable_c   dsl   reference   rom   manifest   build   scripts   COMMIT_COMMANDS_20260503.sh   README.md

git commit -m "Add vol017 core VM Goal13 handoff with graphics bridge"
