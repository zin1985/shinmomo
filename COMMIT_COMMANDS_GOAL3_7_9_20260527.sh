#!/usr/bin/env bash
set -euo pipefail

# Run from repository root after copying this package into zin1985/shinmomo.

git add README_GOAL3_7_9_20260527.md NOT_INCLUDED_ROM.txt   docs/analysis/goal_progress_update_20260527.md   docs/analysis/goal3_wram_struct_progress_20260527.md   docs/analysis/goal7_weapon_special_progress_20260527.md   docs/analysis/goal9_script_spec_progress_20260527.md   docs/analysis/goal13_0799x_progress_20260527.md   data/static/goal3_wram_refs_20260527.csv   data/static/goal3_wram_ref_summary_20260527.csv   data/static/goal7_weapon_script_pack_by_equipment_20260527.csv   data/static/goal7_weapon_hook_targets_20260527.csv   data/static/goal7_hook_body_windows_20260527.csv   data/static/goal9_41a10_target_records_20260527.csv   data/static/goal9_398xx_9byte_rows_20260527.csv   data/static/goal9_script_blob_windows_20260527.csv   data/static/goal13_0799x_static_scan_20260527.csv   tools/python/extract_goal3_goal7_goal9_static.py   manifest/MANIFEST.md manifest/EXCLUDED.md

git commit -m "analysis: progress Goal3 Goal7 Goal9 static findings 20260527"
