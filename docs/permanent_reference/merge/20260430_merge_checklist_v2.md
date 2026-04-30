# 20260430 v2 マージチェックリスト

## 取り込み推奨

- `docs/handover/20260430_vol014_merge_handover_v2.md`
- `docs/permanent_reference/weapon_special/20260430_weapon_special_goal7_goal8_thread_findings_v2.md`
- `docs/permanent_reference/weapon_special/20260430_weapon_special_raw_byte_anchors.md`
- `docs/permanent_reference/goals/20260430_goals_progress_v2.md`
- `data/rom_anchor_checks/20260430_weapon_special_anchor_bytes.csv`
- `scripts/analysis/extract_weapon_special_anchor_bytes.py`

## 注意して取り込む

- `reference/imported_handover/` は過去資料の再同梱。既にGitHubにある場合は重複注意。
- `data/disassembly/` は大きめのTXT。既に同名がある場合は差分確認。
- `reference/previous_package_20260430/` は前回ZIPからの文書再展開。必要なければ除外可。

## 除外済み

- `.smc`
- `.sfc`
- `*_original.smc`
