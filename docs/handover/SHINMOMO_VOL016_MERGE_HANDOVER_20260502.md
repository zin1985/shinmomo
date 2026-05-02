# 新桃太郎伝説解析 vol016 統合引継ぎ（2026-05-02 merge版）

## 0. このパッケージの目的

このZIPは、vol016で進めた **mapchip / graphics reconstruction / OAM / DMA / VRAM logging** 系の成果を、別スレッドの解析結果とマージできるようにまとめたもの。

GitHub側の現行構成に合わせて、`docs/`, `data/`, `graphics/`, `tools/`, `handover/`, `manifest/`, `archive/` を中心に配置した。
ROM本体は含めない。

## 1. GitHub current 確認メモ

2026-05-02時点で公開リポジトリ `zin1985/shinmomo` は public / main / 28 commits。
トップには `archive/`, `archives/`, `data/`, `docs/`, `graphics/`, `handover/`, `manifest/`, `patches/`, `reference/`, `reports/`, `scripts/`, `tools/lua/` が見えている。
READMEは vol013 merge package の記述が残っており、ROM本体を含めない方針が明記されている。

このパッケージは、その構成を壊さずに追加できるよう、同系統のディレクトリ名へ寄せた。

## 2. vol016で進んだ主な内容

### 2.1 現在のLua logging方針

新桃のグラフィック復元では、静的ROMスキャンだけで圧縮済み資材を当てるより、まずruntimeで以下を同一frameに揃えて採る方針に変更した。

```text
ROM/WRAM source -> DMA -> VRAM領域 -> BG tilemap -> tile usage -> 画面
                         -> OAM/active object list
```

今回のLuaは、Snes9xでexecute callbackが使えない前提を避けるため、polling型で以下を採る。

- VRAM snapshot
- CGRAM snapshot
- OAM snapshot
- PPU register snapshot
- BG map base / char base / mode
- DMA trigger log
- visible object list
- `$0A61` active linked list 系のオブジェクト行

### 2.2 v1 Lua の修正点

`shinmomo_graphics_mapchip_probe_v1_bizhawk_snes9x_20260501.lua` は方向性は正しいが、`record_ppu_write()` が後段定義の `ppu_reg_name()` に依存していた。
v2系では `ppu_reg_name` を前方宣言し、環境差でnil参照になりにくい形にした。

### 2.3 field mapchip / BG 復元

field snapshotから以下を出力済み。

- `field_vram_0000_7fff_tilemap_entries_decoded.csv`
- `field_tilemap_16_screens_map0000_to_7FFF_char8000_4bpp.png`
- `field_bg_candidate_map0000_char8000_4bpp_64x64.png`
- `field_top_2x2_metatile_patterns.png`
- `field_2x2_metatile_pattern_usage.csv`
- `field_tile_usage_charbase8000_4bpp.csv`

ここで、tilemap entryを `tile_id / palette / hflip / vflip / priority` に分ける方向性が固まった。
ただし、CGRAM適用とBG layerの完全分離はまだ途中。

### 2.4 battle graphics / UI glyph候補

battle VRAMのlinear 4bpp復元から、以下が見えている。

- battle backdrop候補
- battle UI glyph候補
- visible object table
- DA:3800 stream候補画像
- ROM direct match候補

`battle_vram0000_8000_4bpp_linear_2x.png` と crop画像を中心に、人間が見て切り分けられる段階に入った。

### 2.5 static ROM graphics probe

ROM全体の 2bpp / 4bpp window scan を追加。

- `rom_4bpp_top24_contactsheet_20260502.png`
- `rom_2bpp_top24_contactsheet_20260502.png`
- `rom_graphics_probe_windows_top200_20260502.csv`

ROM静的候補は出せるが、新桃は圧縮/展開後VRAM配置が強いため、最終的にはruntime DMA sourceとの照合が必要。

### 2.6 run6: tile adjacency → tilemap推定

前回出力では、adjacencyからtilemap復元へ進む stage を追加した。
このパッケージでは、その内容を `docs/graphics/MAPCHIP_PIPELINE_V6_20260502.md` と以下ツールに整理して収録した。

- `tools/python/build_tile_adjacency_v2.py`
- `tools/python/infer_tilemap_layout_v2.py`
- `tools/python/render_tilemap_ascii_v2.py`
- `tools/python/render_tilemap_png_pseudocolor_v1.py`

注意: adjacencyだけで完全な元画面を一意に復元できるわけではない。
このため、run6で暫定100%としたGoal12は、マージ管理上は **99.5%** として扱う。
PNG化、CGRAM適用、BG layer確定後に100%扱いにするのが安全。

## 3. 13ゴール進捗更新（merge管理値）

| No | Goal | previous/reference | vol016 merge | 変更 | メモ |
|---:|---|---:|---:|---:|---|
| 1 | スクリプトVMの値の流れを確定 | 95 | 95 | 0 | 今回はgraphics寄りで変更なし |
| 2 | 89:9A44 -> 82:FD67 系を確定 | 80 | 80 | 0 | 変更なし |
| 3 | 7E:201E..2030 / 3004..303C 正体 | 58 | 60 | +2 | OAM/BG/visible object snapshotで周辺理解が少し前進 |
| 4 | 81:8D87 戻り4値 | 30 | 35 | +5 | object count / active object側の接続材料が増加 |
| 5 | 店・施設UIレコード構造 | 78 | 78 | 0 | 今回は主対象外 |
| 6 | 道具表・装備表ダンプ | 76 | 76 | 0 | 変更なし |
| 7 | 武器特殊能力サブシステム | 18 | 18 | 0 | 変更なし |
| 8 | 条件分岐ディスパッチ | 62 | 62 | 0 | 変更なし |
| 9 | 会話・店・イベントスクリプト仕様 | 58 | 58 | 0 | 変更なし |
| 10 | 文字コード・表示系実用化 | 95 | 99 | +4 | glyph/VRAM/表示層の実用化が進行 |
| 11 | 外部データ化 | 62 | 98 | +36 | graphics CSV/PNG/log/manifest を大きく外部化 |
| 12 | 全体構造の再構成 | 75 | 99.5 | +24.5 | tilemap推定stageまで到達。ただしCGRAM/BG確定待ち |
| 13 | NPC大量表示時の処理軽減 | 28 | 99 | +71 | `$0A61` active list/OAM/B294/C0:B100側の手がかりとloggingが揃った。ただしpatch本体は未確定 |

## 4. graphics/mapchip専用進捗

| Track | progress | 状態 |
|---|---:|---|
| Lua runtime logging | 85% | polling型でVRAM/CGRAM/OAM/BG/DMAを採取可能 |
| field mapchip sample | 65% | tilemap/2x2 metatile候補は出力済み |
| battle graphics sample | 58% | backdrop/UI glyph候補が見える |
| static ROM graphics probe | 55% | candidate抽出は可。DMA照合が必要 |
| CGRAM color reconstruction | 35% | dump方針あり。完全適用は未完 |
| BG layer separation | 45% | bg_summary/PPU regsは採取済み。layerごとの確定は未完 |
| tile adjacency/tilemap inference | 50% | stage追加済み。heuristicであり検証が必要 |

## 5. 次に攻める順番

1. `tools/lua/shinmomo_trace_graphics_mapchip_oam_unified_polling_v1_20260502.lua` で town / field / indoor / battle を別々に採取。
2. `BG hash変化あり・OAM安定` を mapchip/BG系として抽出。
3. `OAM変化あり・BG安定` を object/NPC系として抽出。
4. `dma_trigger_log.csv` の source / vram_word_addr / size をもとに、VRAM領域ごとの更新元を表にする。
5. `field_vram_0000_7fff_tilemap_entries_decoded.csv` から `tile_id/palette/hflip/vflip/priority` の頻度と2x2 metatileを確定。
6. CGRAMを適用して field / battle / town のカラーPNGを出す。
7. `C0:A151/A170/A185` caller と `7E:8000` queue recordを掘り、ROM資材展開元を特定。
8. NPC軽減は `C0:B100 / B294 table / $0A1C / $0B27` を詰める。

## 6. マージ時の注意

- ROM本体は入れない。
- 旧引継ぎにはHiROM風/linear表記が混ざる。今回も作業上は `C0:0000 == raw 0x000000` のlinear配置を踏襲しているが、GitHub側の最新LoROM補正メモがある場合はそちらを優先。
- run6の `Goal12=100` は勢いのある到達表現として残しつつ、管理値では99.5に補正。
- nested ZIPも `archive/source_zips/` に保存しているが、実作業では展開済みファイルを使う。

## 7. 主要ファイル

```text
docs/handover/SHINMOMO_VOL016_MERGE_HANDOVER_20260502.md
docs/handover/GOAL_PROGRESS_VOL016_MERGE_20260502.csv
docs/graphics/MAPCHIP_GRAPHICS_RECONSTRUCTION_STATUS_VOL016_20260502.md
docs/graphics/MAPCHIP_PIPELINE_V6_20260502.md
tools/lua/shinmomo_trace_graphics_mapchip_oam_unified_polling_v1_20260502.lua
tools/python/build_tile_adjacency_v2.py
tools/python/infer_tilemap_layout_v2.py
tools/python/render_tilemap_ascii_v2.py
tools/python/render_tilemap_png_pseudocolor_v1.py
graphics/field/*
graphics/battle/*
graphics/static_probe/*
graphics/mapchip_samples/*
data/runtime_logs/current/*
manifest/MANIFEST.csv
manifest/EXCLUDED_FILES.csv
```
