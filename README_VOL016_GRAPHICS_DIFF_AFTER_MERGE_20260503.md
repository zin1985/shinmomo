# 新桃太郎伝説解析 vol016 graphics/mapchip 差分パック（前回マージ後）

作成日: 2026-05-03  
対象: `zin1985/shinmomo` の前回別スレッドマージ済みコミット以降、このスレッドで進めた graphics / mapchip 復元差分。

## このZIPの位置づけ

前回別スレッドとのマージ内容は既にコミット済みという前提で、そこから後にこのスレッドで発生した差分をまとめた。

中心は以下。

- run2: 現在参照できる `vram.bin` を **battle CHR型 snapshot** として分類した成果物
- run3-run10: battle側を **OAM -> CHR atlas -> sprite cluster -> PNG renderer** へ進めるための仕様・schema・補助ツール
- field/town側を **BG tilemap -> metatile -> map reconstruction** として分離する方針
- 別スレッドへ渡す bridge schema と Goal13観測材料

## ROM本体について

`.smc` / `.sfc` は含めない。`vram.bin` は実行時dump由来の解析用サンプルとして `data/runtime_logs/current_after_merge_sample/` に置く。

## 最初に読むファイル

1. `docs/handover/SHINMOMO_VOL016_GRAPHICS_DIFF_AFTER_MERGE_20260503.md`
2. `docs/handover/GOAL_PROGRESS_VOL016_GRAPHICS_DIFF_AFTER_MERGE_20260503.csv`
3. `docs/graphics/BATTLE_CHR_OAM_ATTRIBUTION_PLAN_VOL016_20260503.md`
4. `docs/graphics/SPRITE_RENDERER_SYNC_SPEC_RUN10.md`
5. `docs/mapchip/FIELD_TILEMAP_METATILE_PIPELINE_AFTER_MERGE.md`
6. `manifest/MANIFEST_VOL016_GRAPHICS_DIFF_AFTER_MERGE_20260503.csv`

## ざっくり結論

- field / town / indoor は **BG tilemap型** として進める。
- battle は **tilemap復元ではなく CHR atlas + OAM attribution型** として進める。
- 次の実作業は、OAM snapshot + OBSEL + OAM high table + VRAM + CGRAM を同一frameで揃え、sprite cluster PNGを出すこと。
