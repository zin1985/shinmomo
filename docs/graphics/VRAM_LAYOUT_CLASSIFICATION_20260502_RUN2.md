# 新桃太郎伝説 vol016 graphics 継続解析 run2: current VRAM layout classification (2026-05-02)

## このスレッドの担当範囲

本スレッドは、別スレッドとの棲み分けどおり **グラフィック／マップチップ復元系** を担当する。
今回も script / VM / object-path 本体ではなく、手元にある runtime dump と ROM/VRAM から「画面に見えるもの」を復元する側を進めた。

## 入力

- `/mnt/data/vram.bin` : 65536 bytes
- `frame_summary.csv` : frame 99282..100500 の戦闘遷移系ログ
- `visible_objects.csv` : frame 100200 の active object list
- `ppu_regs_capture.csv` / `bg_summary.csv` : register値はゼロ寄りで、BGMODE/BGSCは今回も信頼しない

## 今回の結論

現在の `vram.bin` は **フィールドmapchip型ではなく、戦闘CHR型のスナップショット** と判定する。

理由:

- VRAM `0x0000..0x7FFF` の各 0x1000 region が、4bpp tile としてほぼ全タイル非ゼロ。
- `0x0000..0x7FFF` の 4bpp CHR-likeness 平均は `0.9854`。
- field解析時のような `02 00 03 00 ...` 系の規則的 tilemap entry より、戦闘背景・UI・glyph の linear CHR atlas として読む方が自然。
- `frame_summary.csv` でも `vram_hash` と `oam_visible_count` が戦闘遷移中に変化しており、戦闘画面構築中の snapshot と合う。

## VRAM region summary

| range | nonzero | 4bpp nonblank | 4bpp unique | chr_likeness |
|---|---:|---:|---:|---:|
| 0000-0FFF | 0.9844 | 128 | 120 | 0.9375 |
| 1000-1FFF | 1.0000 | 128 | 128 | 1.0000 |
| 2000-2FFF | 1.0000 | 128 | 127 | 0.9922 |
| 3000-3FFF | 1.0000 | 128 | 127 | 0.9922 |
| 4000-4FFF | 1.0000 | 128 | 127 | 0.9922 |
| 5000-5FFF | 1.0000 | 128 | 127 | 0.9922 |
| 6000-6FFF | 1.0000 | 128 | 126 | 0.9844 |
| 7000-7FFF | 1.0000 | 128 | 127 | 0.9922 |
| 8000-8FFF | 0.2856 | 49 | 50 | 0.1495 |
| 9000-9FFF | 0.4241 | 69 | 58 | 0.2443 |
| A000-AFFF | 0.1587 | 48 | 49 | 0.1436 |
| B000-BFFF | 0.0000 | 0 | 1 | 0.0000 |
| C000-CFFF | 0.6968 | 122 | 122 | 0.9084 |
| D000-DFFF | 0.2473 | 58 | 54 | 0.1912 |
| E000-EFFF | 0.0000 | 0 | 1 | 0.0000 |
| F000-FFFF | 0.9165 | 128 | 25 | 0.1953 |


## tilemap候補ランキングについて

今回、tilemap候補も機械的に採点したが、上位候補は「本物のBG tilemap確定」ではなく、**CHR領域をtilemapとして誤読した場合の副産物** と扱う。
戦闘画面では、今回のスナップショットについては `0x0000..0x7FFF` をまず 4bpp CHR 本体として扱うのが安全。

### top 8 candidates

| rank | map_base | char_base | bpp | score | nonblank_ref | top_attrs |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 8000 | 0000 | 2 | 7.4964 | 1.0 | p0r0h0v0:1024 |
| 2 | 8000 | 0000 | 4 | 7.4964 | 1.0 | p0r0h0v0:1024 |
| 3 | 8000 | 2000 | 2 | 7.4964 | 1.0 | p0r0h0v0:1024 |
| 4 | 8000 | 2000 | 4 | 7.4964 | 1.0 | p0r0h0v0:1024 |
| 5 | 8000 | 4000 | 2 | 7.4964 | 1.0 | p0r0h0v0:1024 |
| 6 | 8000 | 4000 | 4 | 7.4964 | 1.0 | p0r0h0v0:1024 |
| 7 | 8000 | 6000 | 2 | 7.4964 | 1.0 | p0r0h0v0:1024 |
| 8 | 8000 | 6000 | 4 | 7.4964 | 1.0 | p0r0h0v0:1024 |


## 生成物

- `data/csv/current_vram_region_summary_20260502_run2.csv`
- `data/csv/current_vram_tilemap_candidate_scores_20260502_run2.csv`
- `graphics/battle/current_vram_4bpp_region_contact_sheet_20260502_run2.png`
- `graphics/battle/current_vram_0000_7fff_4bpp_chr_atlas_20260502_run2.png`
- `graphics/battle/current_vram_8000_ffff_4bpp_chr_atlas_20260502_run2.png`
- `graphics/battle/current_vram_tilemap_candidate_rank*.png`
- `tools/python/analyze_vram_layout_candidates_v1.py`

## 次の実作業

1. `shinmomo_trace_graphics_mapchip_oam_unified_polling_v1_20260502.lua` の出力を、今回の `region_summary` に接続する。
2. 戦闘では `0x0000..0x7FFF` を CHR atlas として扱い、BG tilemapは別snapshotまたはPPU/BGSC正規取得で探す。
3. field/townでは `map_base=0x0000`, `char_base=0x8000`, `4bpp` の既存仮説を維持し、戦闘とは別schemaに分ける。
4. CGRAM実体が未取得なので、次回Luaでは `cgram.bin` を必ず保存する。疑似色から実色PNGへ進めるにはここが鍵。
5. 別スレッドへ渡すCSVは `frame,bg_hash,oam_hash,cgram_hash,obj_count,oam_visible_count` を最低列として維持する。

## 13ゴールへの反映

このスレッドの担当は graphics/mapchip 復元なので、13ゴール本体値は別スレッド統合値を尊重する。
ただし、Goal 12/13/11 の観測基盤側には以下の前進がある。

- Goal 12: 戦闘VRAMについて、field型tilemapではなくCHR型snapshotとして分類できた。
- Goal 13: OAM visible count と戦闘CHR更新の同時変化を見る橋が増えた。culling本体解析は別スレッドへ渡す。
- Goal 11: VRAM layout summary / tilemap candidate score / CHR atlas を外部CSV/PNG化した。
