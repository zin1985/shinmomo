# 別スレッド共有用メッセージ（2026-05-03）

こちらの script / VM / event / NPC / Goal13 core logic 側スレッドでは、前回 graphics / mapchip 成果コミット後の差分をまとめ、コミット可能なZIPを作成しました。

ZIP名:
`shinmomo_vol017_core_graphics_merged_20260503_commit.zip`

## 今回の主な成果

- `$0759/$0799` を単純な object/path pointer 本体ではなく、bank87 側の状態・slot staging・表示制御寄りとして再分類。
- bank87 周辺の `slot copy / state toggle / position update / save-restore` 断片を Goal13 core logic の材料として整理。
- `0x39850` 周辺の 9-byte macro rows と `$83:F09A / F0DB / F0C6...` blob を、VM reader / target-side blob 解析の継続対象として切り分け。
- `vm_time_slicing.md`、`npc_timing_model.csv`、`vm_full_simulator.py` を含む VM time model / scheduler / simulator 構成を同梱。
- 解析済み構造を C に落とした `recompilable_c/` scaffold を同梱。完全decompileではなく、再コンパイル可能な構造表現の初期版。
- graphics側からの runtime bridge schema、visible object / DMA / frame summary を Goal13側の観測材料として取り込む前提を固定。

## 進捗見立て

- Goal12: 82%  
  core構造、graphics構造、C scaffold が統合され、人間可読な全体構造は前進。

- Goal13: 78%  
  runtime観測基盤とbank87状態系の足場は増えたが、active list / OAM登録前制御 / culling / skip / OAM budget の安定パッチ本体は未確定。

- Goal7: 35%  
  opcode50 / token09 / CB hook / branch staging 系の材料は維持。仕様化は未完。

- Goal8: 66%  
  `41A10 -> 39850/39993` と macro row 整理は前進。reader本体は未確定。

- Goal9: 63%  
  VM reader / macro row / blob runner 仕様化材料は増えたが、会話本文一括抽出は未完。

## graphics側へ渡したい接続点

次に graphics 側で出る runtime log は、以下の形で Goal13側に渡してもらえるとそのまま合流できます。

```csv
frame,scene_tag,bg_hash,oam_hash,cgram_hash,active_object_count,oam_visible_count,notes
frame,object_slot,x,y,tile,attr,visible,spawn_or_despawn,probable_npc_group
frame,dma_sequence_id,source_bank,source_addr,vram_word_addr,size_bytes,target_region,inferred_asset_kind
```

こちらでは、これを `$0759/$0799`、active slot、OAM登録前制御、slot visibility の候補と突き合わせます。

## 次にこちらで進めること

1. `$0759/$0799` と active object / visible OAM の対応確認。
2. bank87 slot/state fragments の state machine 化。
3. `0x39850` macro rows と `$83:F09A` family blob runner の対応づけ。
4. `vm_full_simulator.py` への実ROM抽出データ投入。
5. 安定パッチ化に必要な culling / skip / OAM budget 境界の特定。
