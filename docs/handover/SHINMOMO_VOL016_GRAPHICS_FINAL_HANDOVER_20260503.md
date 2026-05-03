# 新桃太郎伝説解析 vol016 graphics/mapchip final handover（2026-05-03）

## 0. このhandoverの位置づけ

この文書は、前回別スレッドとマージ済みの `2026-05-02 vol016 merge` 後、このスレッドで進めた graphics / mapchip reconstruction 系の差分をまとめたもの。

このスレッドの主担当は以下。

```text
画面にどう出るかを復元する解析
BG / mapchip / sprite / palette / OAM / VRAM / DMA / PNG / CSV
```

別スレッド側の主担当は以下。

```text
なぜそれが出るかを読む解析
script / VM / event / object-path pointer / NPC軽減ロジック / weapon special / patch候補
```

## 1. ここまでの成果

### 1-1. runtime logging 基盤

既存の graphics probe / unified polling 方針を継承し、以下を同一frameまたは近接frameで採る方針を維持する。

```text
VRAM
CGRAM
OAM
PPU register writes
DMA trigger
BG tilemap
visible object list
active object list
```

既存Luaは `VRAM / CGRAM / OAM / PPU register writes / DMA trigger / BG tilemap / tile sheet preview` をまとめて採る設計で、graphics / mapchip 復元の足場として妥当。

### 1-2. field / town / indoor と battle の分離

このスレッドでは、field系とbattle系を明確に分けた。

```text
field / town / indoor:
  BG tilemap entry decode
  -> tile usage
  -> 2x2 metatile
  -> canonical metatile
  -> metatile graph
  -> map layout reconstruction
  -> CGRAM適用PNG

battle:
  4bpp CHR atlas
  -> OAM tile / attr / palette attribution
  -> sprite clustering
  -> sprite PNG / atlas / renderer spec
```

### 1-3. battle VRAMの扱い

run2の実ログサンプル `vram.bin` は、field mapchip型ではなく battle CHR型 snapshot として扱うのが自然と判断。

暫定VRAM領域ラベル:

```text
0x0000..0x7FFF : battle_chr_0000_7fff          : backdrop / battle UI / glyph CHR候補
0x8000..0xAFFF : battle_ui_glyph_8000_afff     : UI/glyph/補助タイル候補
0xB000..0xBFFF : empty_b000_bfff               : ほぼ空き
0xC000..0xDFFF : battle_object_ui_c000_dfff    : character/object/number/status候補
0xE000..0xEFFF : empty_e000_efff               : ほぼ空き
0xF000..0xFFFF : special_f000_ffff             : stripe/fill/special pattern候補
```

## 2. 追加した仕様群

### 2-1. canonical metatile

2x2 metatile候補を、完全一致だけでなく構造一致でまとめる。

```text
shape_key  = tile id only
render_key = tile id + palette + hflip + vflip + priority
canonical_key = tile set + adjacency signature + optional palette grouping
```

### 2-2. metatile graph

```text
node = canonical metatile
edge = adjacency frequency
```

出力候補:

```csv
scene,from_metatile_id,to_metatile_id,direction,frequency,confidence
```

用途:

- 地形構造推定
- edge / corner / transition tile 検出
- layout reconstruction

### 2-3. DMA sequence synchronization

VRAM / tilemap / CGRAM / OAM を機械的に結合する際、frame単位だけではズレる可能性があるため、dma_sequence_idを導入。

```text
new sequence if:
  DMA source address changed
  DMA size changed
  >1 frame gap
```

原則:

```text
VRAM + tilemap + CGRAM + OAM は同じ dma_sequence_id でjoinする
```

### 2-4. final graphics reconstruction pipeline

```text
1. Lua runtime logging
2. dma_sequence segmentation
3. VRAM grouping
4. BG tilemap decode
5. 2x2 metatile extraction
6. canonicalization
7. metatile graph build
8. deterministic layout reconstruction
9. CGRAM apply
10. BG/OAM layer separation
11. PNG / CSV / JSON export
```

## 3. 進捗管理

このスレッド上では一度 `Goal12 = 100%` と完了宣言する流れまで整理したが、実運用上は以下の2値管理を推奨する。

```text
Goal12_thread_declaration: 100%
  このスレッド内の graphics/mapchip設計・復元仕様としては完了扱い。

Goal12_merge_safe_value: 99.5%〜99.9%
  実ログの全scene再採取、CGRAM適用PNG、layer完全分離の再検証をマージ側で行うなら安全値。
```

Goal13は、このスレッドでは上げすぎない。

```text
Goal13_thread_value: 78% までの材料増扱い
Goal13_merge_safe_value: 75%維持推奨
```

理由: OAM / VRAM / DMA runtime観測基盤は強化されたが、culling / skip / OAM budget / patch本体は別スレッド担当で未確定。

## 4. 次に別スレッドへ渡すべきもの

別スレッド側へ渡す最重要CSV/ログは以下。

```text
frame,scene_tag,bg_hash,oam_hash,cgram_hash,active_object_count,oam_visible_count,notes
frame,object_slot,x,y,tile,attr,visible,spawn_or_despawn,probable_npc_group
frame,dma_sequence_id,source_bank,source_addr,vram_word_addr,size_bytes,target_region,inferred_asset_kind
```

Goal13本体解析へ渡す観点:

```text
BG安定 + OAM変化
active object list変化
OAM visible count変化
NPC大量表示場面のframe log
sprite piece / object出現消滅タイミング
```

## 5. 残タスク

### graphics/mapchip側

1. field / town / indoor / battle を同一Lua loggerで再採取。
2. `dma_sequence_id` 付きで VRAM / CGRAM / OAM / BG tilemap をjoin。
3. field/town/indoor の canonical metatile辞書を横比較。
4. CGRAM適用PNGをfieldから再確認。
5. battle sprite cluster PNG / atlas を実ログで確認。
6. final map validation report を出す。

### 別スレッド側

1. Goal13本体、特に culling / skip / OAM budget を継続。
2. `$0759/$0799` object/path pointer 系と OAM変化を同期検証。
3. 実験パッチ / 安定パッチ検証。

## 6. ROM本体除外

このパッケージにROM本体は含めない。

```text
*.smc
*.sfc
*.fig
```
