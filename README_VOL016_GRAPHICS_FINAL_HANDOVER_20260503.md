# shinmomo vol016 graphics/mapchip final handover package（2026-05-03）

このZIPは、前回別スレッドとマージ済みの `2026-05-02 vol016 merge` 以降、このスレッドで進めた **graphics / mapchip reconstruction** 差分をまとめたコミット用パッケージです。

## 重要な前提

- ROM本体 `.smc` / `.sfc` は含めない。
- 前回差分ZIP `shinmomo_vol016_graphics_diff_after_merge_20260503_commit.zip` の内容を展開済みで含む。
- 追加で、v2〜v6相当の継続handover、mapchip canonicalization、metatile graph、DMA sequence synchronization、final pipeline、validation/data layout spec、別スレッド共有用レポートを追加した。
- run7〜run10系で一度強めに表現した「Goal12=100%」は、このZIP内では **“このスレッド上の完了宣言候補”** とし、実ログ再検証前の最終採用値は別スレッド側とのマージ時に決める。

## 追加の中心ファイル

```text
docs/handover/SHINMOMO_VOL016_GRAPHICS_FINAL_HANDOVER_20260503.md
docs/handover/THREAD_REPORT_FOR_MERGE_20260503.md
docs/handover/GOAL_PROGRESS_VOL016_GRAPHICS_FINAL_20260503.csv
docs/graphics/STATUS_RECONCILIATION_AND_CAVEATS_20260503.md
docs/graphics/FINAL_GRAPHICS_RECONSTRUCTION_PIPELINE_20260503.md
docs/graphics/MAP_VALIDATION_SPEC_20260503.md
docs/graphics/FINAL_DATA_LAYOUT_SPEC_20260503.md
```

## コミット方法

```bash
bash COMMIT_COMMANDS_VOL016_GRAPHICS_FINAL_20260503.sh
```
