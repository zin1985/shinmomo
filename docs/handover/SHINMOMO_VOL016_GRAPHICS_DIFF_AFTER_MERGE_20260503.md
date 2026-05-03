# 新桃太郎伝説 vol016 graphics/mapchip 差分引継ぎ（前回マージ後, 2026-05-03）

## 0. 前提

前回別スレッドとマージした内容は既にGitHubへコミット済み。  
このパックは、そこから後にこのスレッドで進めた **グラフィック / マップチップ復元担当領域** の差分をまとめる。

このスレッドの担当は「画面にどう出ているか」を復元すること。  
別スレッド側は「なぜそれが出るか」を script / VM / object-path / Goal13本体 / weapon special 側で読む。

## 1. 差分の大枠

### run2

現在参照できる `vram.bin` を再解析し、field mapchip型ではなく **battle CHR型 snapshot** と判定。

暫定VRAM分類:

```text
0x0000..0x7FFF : 戦闘背景/戦闘UI/文字グリフの4bpp CHR本体候補
0x8000..0xAFFF : UI/glyph/補助タイル候補
0xB000..0xBFFF : ほぼ空き
0xC000..0xDFFF : キャラ/数字/状態表示/UI素材候補
0xE000..0xEFFF : ほぼ空き
0xF000..0xFFFF : stripe/fill/special pattern候補
```

### run3-run4

battle側は tilemap candidate scoring を深追いせず、**OAM tile index -> VRAM CHR region -> palette** の attribution を主戦場に変更。

field/town/indoor側は従来通り:

```text
BG tilemap entry decode -> tile usage -> 2x2 metatile -> layer-separated color PNG
```

battle側は:

```text
4bpp CHR atlas -> OAM attribution -> backdrop / UI / glyph / object sheet separation
```

### run5-run7

battle sprite PNG生成のための実装仕様を固定。

必要情報:

```text
OAM snapshot
OAM high table
OBSEL ($2101)
VRAM snapshot
CGRAM snapshot
visible_objects.csv / active object bridge
```

重要ルール:

```text
- tile順ではなく OAM (x,y) で配置する
- visible_object_id一致を最優先にcluster化する
- stable frame（DMA最小, OAM/BG hash安定）を選ぶ
- CGRAMは同一frame固定でpalette適用する
```

### run8-run10

生成された sprite cluster を assetとして再利用するため、atlas metadata / renderer / sync仕様へ拡張。

最終的なrenderer要素:

```text
OAM index
priority
hflip / vflip
8x8 / 16x16 size
9bit X座標
OBSEL / name select
palette
```

## 2. 現時点の正しい分岐

```text
FIELD/TOWN/INDOOR:
  VRAM -> BG tilemap decode -> metatile -> map preview PNG

BATTLE:
  VRAM -> CHR atlas -> OAM attribution -> sprite/UI/glyph separation -> sprite PNG
```

battleをfieldと同じmapchip/tilemap問題として扱うと迷う。  
battleはまず **OAM主導のsprite attribution問題** として扱う。

## 3. 次の最優先タスク

1. `shinmomo_trace_graphics_mapchip_oam_unified_polling_v1_20260502.lua` を拡張して OBSEL `$2101` と OAM high table を明示出力する。
2. `data/runtime_logs/current_after_merge_sample/` のログ形式を `runtime bridge schema` に正規化する。
3. `tools/python/oam_chr_mapper_v1.py` で OAM tile -> CHR VRAM byte address を作る。
4. `tools/python/sprite_clusterer_v1.py` で object/palette/座標ベースの cluster を作る。
5. `tools/python/render_sprite_clusters_v1.py` で sprite PNG を出す。
6. field側は `tools/python/build_field_metatiles_from_tilemap_v1.py` で2x2 metatile候補を継続抽出する。

## 4. 別スレッド連携

別スレッドへ渡すべきCSV:

```text
data/csv/runtime_bridge_from_graphics_unified_schema_20260503.csv
data/csv/oam_chr_mapping_schema_20260503.csv
data/csv/sprite_cluster_schema_20260503.csv
```

Goal13本体側では、以下を使って culling / skip / OAM budget / object-path pointer へ接続する。

```text
frame,scene_tag,bg_hash,oam_hash,cgram_hash,active_object_count,oam_visible_count
frame,object_slot,x,y,tile,attr,visible,spawn_or_despawn,probable_npc_group
```

## 5. 進捗更新

この差分パックでは、過去の run7-run10 の楽観値をそのまま正式進捗にせず、**実ファイル生成済みのrun2成果 + 実装可能なrun3-run10仕様** として保守的に管理する。

- GFX: 60 -> 68
- Goal 3: 61 -> 64
- Goal 11: 98.5 -> 99.0
- Goal 12: 99.5 -> 99.6
- Goal 13: 正式全体値は別スレッド合意の 75% を維持。ただしこのスレッド担当の runtime観測基盤サブ項目は前進。

## 6. 注意

- ROM本体は入れない。
- `vram.bin` は derived runtime dump として入れる。
- battle側の `0xC000..0xDFFF = sprite本体` は「強い運用仮説」であり、OBSEL/OAM high table 取得後に確定値へ上げる。
- 13ゴールの Goal13 は 99%に戻さない。全体75%、object/path pointer系51%、runtime観測基盤は大進展、安定パッチreadiness未達という別スレッド合意を優先する。
