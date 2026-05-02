# 新桃太郎伝説解析 vol016 merge handover package（2026-05-02）

このパッケージは、別スレッドで並行している解析とマージするための GitHub コミット用差分です。

## 最初に読むファイル

1. `docs/handover/SHINMOMO_VOL016_MERGE_HANDOVER_20260502.md`
2. `docs/handover/GOAL_PROGRESS_VOL016_MERGE_20260502.csv`
3. `docs/graphics/MAPCHIP_GRAPHICS_RECONSTRUCTION_STATUS_VOL016_20260502.md`
4. `manifest/MANIFEST.csv`
5. `manifest/EXCLUDED_FILES.csv`

## 重要

ROM本体（`.smc` / `.sfc`）は含めていません。`rom/README_ROM_NOT_INCLUDED.md` を参照してください。

## 主な追加内容

- vol016 の graphics / mapchip / OAM / DMA / VRAM 解析成果
- 現在の Lua logging 方針（Snes9x/BizHawk 互換の polling 型）
- field / battle / static probe のPNG・CSV・handover
- current character color / DA:3800 stream 系の候補画像
- tile adjacency → tilemap 推定 → ASCII/PNG可視化用 Python 補助スクリプト
- 13ゴール進捗の更新CSV
- 旧引継ぎ資料と過去ZIPの展開済みアーカイブ

## 推奨コミット

```bash
git add .
git commit -m "vol016: merge graphics mapchip reconstruction handover"
```
