# 別スレッド共有用メッセージ（2026-05-03）

以下を別スレッドへ共有してください。

---

こちらの graphics / mapchip 担当スレッドでは、前回マージ後の差分として、以下をコミット可能な形でまとめました。

## 1. 主な成果

- 既存の runtime Lua logging 方針を継承し、VRAM / CGRAM / OAM / PPU / DMA / BG tilemap を同一復元パイプラインに乗せる方針を整理。
- field / town / indoor は **BG tilemap → 2x2 metatile → canonical metatile → metatile graph → layout reconstruction → CGRAM適用PNG** として進める方針に固定。
- battle は **mapchipではなく、CHR atlas + OAM attribution + sprite clustering** として分離。
- run2の `vram.bin` は field mapchip型ではなく battle CHR型 snapshot として扱うのが自然と判断。
- `0xC000..0xDFFF` は battle object / UI / number / status 系候補として、OAM attributionで優先確認する領域にした。
- metatile canonicalization、metatile graph、DMA sequence synchronization、map validation、final data layout の仕様を追加。
- Goal13へ渡すための runtime bridge 列を整理。

## 2. Goal進捗の扱い

このスレッド内では一度、graphics / mapchip reconstruction の設計完了として **Goal12=100%** まで整理しました。  
ただし、別スレッドと統合する正式値としては、実ログの全scene再採取・CGRAM適用PNG・layer完全分離の再検証が残るため、**Goal12は 99.5〜99.9% の安全管理でもよい**です。

Goal13は、このスレッドでは runtime観測基盤の材料追加だけなので、**全体75%維持推奨**です。OAM/VRAM/DMAログは進展しましたが、culling / skip / OAM budget / patch本体は未確定です。

## 3. 別スレッドへ渡す重要データ

次に渡したいのは以下です。

```csv
frame,scene_tag,bg_hash,oam_hash,cgram_hash,active_object_count,oam_visible_count,notes
frame,object_slot,x,y,tile,attr,visible,spawn_or_despawn,probable_npc_group
frame,dma_sequence_id,source_bank,source_addr,vram_word_addr,size_bytes,target_region,inferred_asset_kind
```

特に Goal13 には以下が重要です。

- BG安定 + OAM変化
- active object list変化
- OAM visible count変化
- NPC大量表示場面のframe log
- sprite piece / object出現消滅タイミング

## 4. 次の分担

こちらのスレッド:

```text
CGRAM適用PNG
BG layer分離
field/town/indoor metatile graph
battle sprite clustering / atlas
runtime bridge CSV生成
```

別スレッド:

```text
Goal13本体
$0759/$0799 object/path pointer
active list / OAM登録前制御
culling / skip / OAM budget
実験パッチ / 安定パッチ
```

## 5. コミットZIP

今回のZIP名:

```text
shinmomo_vol016_graphics_final_handover_20260503_commit.zip
```

ROM本体は含めていません。
