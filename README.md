# shinmomo commit package 2026-04-27

このZIPは、新桃太郎伝説解析の今回スレッド成果をGitHubへコミットしやすい形に整理したものです。

## 重要

- ROM本体 `.smc/.sfc` は含めていません。
- 生成Lua、Markdown、CSV、IPS、過去の生成ZIPを含めています。
- キー成果は `docs/permanent_reference/` に永久保存版としてまとめています。

## 主要ファイル

### 文字・会話

```text
docs/permanent_reference/text_decoder/20260427_text_decoder_permanent_reference.md
scripts/lua/dialogue/shinmomo_trace_dialogue_v28_mode02_bd98_decoder_smallkana_checked_snes9x_20260427.lua
reports/restored_logs/shinmomo_past_logs_restored_with_v28_rules_20260427.md
reports/restored_logs/shinmomo_older_logs_restored_v28_scan_20260427.md
```

### パッチ・処理軽減

```text
docs/permanent_reference/movement_patch/20260427_movement_patch_permanent_reference.md
patches/ips/shinmomo_apply_depth_reorder_skip_v2_ONLY_recommended_20260427.ips
scripts/lua/movement/shinmomo_move_opt_profile_v2_snes9x_20260427.lua
```

### 進捗

```text
docs/permanent_reference/goals/20260427_goals_progress.md
docs/handover/20260427_session_handover.md
```

## 推奨コミット

```bash
git add docs scripts patches data reports archives manifest reference
git commit -m "docs: add 20260427 dialogue decoder and movement optimization handover"
```
