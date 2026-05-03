# 新桃太郎伝説 解析統合引継ぎ vol017 core + vol016 graphics merge（2026-05-03）

## 0. このZIPの位置づけ

このZIPは、前回の別スレッド graphics / mapchip 成果がコミット済みである前提で、その後のこちらのスレッド成果を中心に、必要な参照ファイルを展開済みでまとめたコミット用パッケージです。
ZIP内ZIPは含めず、ROM本体も含めていません。

主担当範囲は次の通りです。

- script / VM / event / NPC behavior pointer
- Goal 8: 条件分岐ディスパッチ
- Goal 9: 会話・店・イベントスクリプト仕様化
- Goal 7: 武器特殊能力サブシステム
- Goal 12: 全体構造の人間可読化
- Goal 13: NPC大量表示時の処理軽減ロジック本体

別スレッド主担当である graphics / mapchip reconstruction は、成果物と bridge schema を同梱していますが、このスレッドでの正式進捗評価では「観測材料」として扱います。

## 1. 今回まとめた主要成果

### 1-1. Goal13 core logic 周辺

- `$0759/$0799` は、単純な object/path pointer 本体ではなく、bank87 側の状態・表示・slot staging 系の影響を受ける領域として再分類。
- bank87 周辺に、slot copy / state toggle / position update / save-restore 系の断片がまとまって見えることを整理。
- Goal13 の本丸は、BG/VRAM側ではなく active list / OAM登録前制御 / object slot visibility / budget 周辺に寄せるのが妥当と再確認。
- graphics側から渡される `frame_summary / visible_objects / dma_trigger_log / runtime_bridge` を、Goal13側の active object / visible OAM 差分分析に接続する前提を固定。

### 1-2. VM reader / F09A blob / macro row

- `0x39850` 周辺の 9-byte macro rows を別管理し、target-side blob として扱う整理を継続。
- `$83:F09A / F0DB / F0C6...` 系 blob は、slot3 word を受けて制御を渡す reader 側探索の材料として再整理。
- `bank87_vm_reader_candidate` と `vm_blob_f09a` の hexdump、`macro_9byte_rows_vol017.csv` を作成。

### 1-3. VM time model / scheduler / simulator

- `vm_time_slicing.md` と `npc_timing_model.csv` を追加済み。
- `vm_full_simulator.py` を追加し、完全再現に向けた Python 側モデルを用意。
- `vm_execution_model / vm_scheduler / vm_command_dispatch / vm_two_stage_dispatch / vm_behavior_layer` などを `shinmomo-analysis/` 配下に整理。

### 1-4. 再コンパイル可能な言語への落とし込み

- `recompilable_c/` 配下に、C言語の再構成雛形を追加。
- `item_records / equipment_records / branch_records / macro_rows / vm_blob_catalog` を generated C/H として出力。
- `src/vm_runtime.c` と `src/main.c` を置き、ビルドテストログとデモ出力を同梱。
- ただしこれはまだ「ROMを完全に再ビルドできる decompilation」ではなく、解析済み構造を再コンパイル可能なC表現へ落とした scaffold です。

### 1-5. graphics側との統合ポイント

別スレッドからの成果として、以下を同梱しました。

- VRAM / CGRAM / OAM / PPU / DMA / BG tilemap logging 方針
- field / town / indoor の metatile graph / map reconstruction schema
- battle の CHR atlas + OAM attribution + sprite clustering 方針
- runtime bridge CSV schema
- `run2 vram.bin` を battle CHR 型 snapshot として扱う判断

このスレッド側では、graphics復元そのものではなく、Goal13に渡す runtime観測材料として使います。

## 2. 13ゴール進捗の統合見立て

| Goal | 進捗 | 今回の扱い |
|---|---:|---|
| 1. スクリプトVMの値の流れ | 96% | time model / two-stage dispatch / simulatorで微増。完全確定には実行trace追加が必要。 |
| 2. 89:9A44 -> 82:FD67 系 | 81% | 大きな新規進展は限定的。schema実例の追加待ち。 |
| 3. 7E:201E..2030 / 3004..303C | 60% | slot/state系理解がGoal13側から少し前進。 |
| 4. 81:8D87 戻り4値 | 30% | 今回ほぼ未着手。 |
| 5. 店・施設UI構造 | 79% | ledger/choiceの既存成果維持。今回主対象外。 |
| 6. 道具表・装備表 | 77% | C scaffold化で外部データ化は進んだが、内部フラグ辞書は未完。 |
| 7. 武器特殊能力 | 35% | opcode50 / token09 / CB hook / branch staging を成果として保持。最終仕様化は未完。 |
| 8. 条件分岐ディスパッチ | 66% | `41A10 -> 39850/39993` と macro row整理を維持。reader本体未確定。 |
| 9. 会話・店・イベントスクリプト仕様 | 63% | F09A blob / macro row / VM modelで仕様化材料が増加。本文一括抽出は未完。 |
| 10. 文字コード・表示系 | 95% | 既存成果維持。今回主対象外。 |
| 11. 外部データ化 | 70% | C scaffold / generated tables / CSV追加で前進。 |
| 12. 全体構造の再構成 | 82% | core + graphics + decomp scaffold を統合し、人間可読モデルが前進。 |
| 13. NPC大量表示処理軽減 | 78% | runtime観測材料とbank87状態系の足場が増えたが、安定パッチ化は未完。 |

## 3. 次に攻めるべき箇所

1. `$0759/$0799` を active object / OAM登録直前制御 / slot visibility のどこに置くか、runtime logと合わせて確定する。
2. `bank87` の slot copy / state toggle / save-restore / position update 断片を、1つの state machine としてつなぐ。
3. `0x39850` の 9-byte macro rows を、`$83:F09A / F0DB / F0C6` 側の blob runner と対応づける。
4. `vm_full_simulator.py` に、実ROMから抽出した macro row / command slot / state values を流し込んで、再現可能な単位テストを増やす。
5. graphics側の `visible_objects.csv` と `frame_summary.csv` を、Goal13の active object count / OAM visible count 差分に接続する。

## 4. 同梱物の見方

- `docs/handover/` : 引継ぎ・進捗表・別スレッド報告用文面
- `docs/reports/` : Goal13、bank87、VM reader系レポート
- `docs/graphics/` : graphics/mapchip側からの統合資料
- `data/csv/` : 今回抽出・整理したCSV
- `data/hexdumps/` : bank87 / macro rows / F09A blob などのhexdump
- `data/runtime_logs/` : graphics側runtime sample log
- `tools/python/` : 解析スクリプト
- `tools/lua/` : runtime logger
- `shinmomo-analysis/` : VM/time/scheduler/Goal13設計資料
- `recompilable_c/` : 再コンパイル可能なC scaffold
- `reference/` : 過去引継ぎ・表ダンプ
- `rom/README_ROM_NOT_INCLUDED.md` : ROM非同梱メモ

## 5. 注意点

- ZIP内ZIPは入れていません。
- ROM本体は入れていません。
- graphics側成果は「別スレッドでコミット済み」の前提ですが、bridge確認と再開性のため展開済みで同梱しています。
- Goal13=78% は、core logic特定の足場込みの見立てです。安定パッチが完成した値ではありません。
