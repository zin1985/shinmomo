# 新桃太郎伝説 vol016 グラフィック復元 引継ぎ（2026-05-02）

## 目的
グラフィック復元を、ROM静的スキャン・VRAM仮復元・runtime polling の3段階に整理した。

## 最新GitHub確認
公開repoは `zin1985/shinmomo` main、28 commits。READMEは vol013 merge package 表記で、ROM本体を含めない方針が明記されている。

## 根拠
既存引継ぎでは、`80:A216` が WRAM -> VRAM DMA 本体、`80:A474` は HDMA更新要求flag setter、`80:A151/A170/A185` は `7E:8000` 転送キュー作成側、`DA:3800` は asset pointer table 入口と整理されている。
また `0x26A60..0x26C3F` はビットマップ本体説が後退し、DMA/HDMA/表示定義寄りとされる。

## 今回の成果
- `graphics/static_probe/rom_4bpp_top24_contactsheet_20260502.png`
- `graphics/static_probe/rom_2bpp_top24_contactsheet_20260502.png`
- `data/csv/rom_graphics_probe_windows_top200_20260502.csv`
- 既存 field / battle VRAM復元サンプルの整理
- `tools/lua/shinmomo_trace_graphics_mapchip_oam_unified_polling_v1_20260502.lua`

## 現状評価
- field mapchip: VRAM snapshotからの白黒/疑似濃淡復元は可能。
- battle graphics: VRAM 4bpp linearで背景・UI glyph候補が見えている。
- ROM static probe: 候補抽出は可能だが、圧縮/展開後VRAM配置の照合が必要。

## 次の一手
1. Luaで field / town / indoor / battle を採取。
2. `BG hash変化あり・OAM安定` を mapchip/BG系として抽出。
3. `OAM変化あり・BG安定` を object/NPC系として抽出。
4. CGRAM dumpを追加してカラー復元。
5. tilemap entryから `tile_id/palette/hflip/vflip/priority` をCSV化。

## 進捗更新
| Track | previous | updated |
|---|---:|---:|
| Goal10 display/text | 99% | 99% |
| Goal11 external data | 98% | 98% |
| Goal12 structure reconstruction | 99.2% | 99.3% |
| Goal13 NPC/OAM | 99% | 99% |
| GFX graphics/mapchip | 45% | 52% |
