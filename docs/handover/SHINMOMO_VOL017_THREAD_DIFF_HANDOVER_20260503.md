# 新桃太郎伝説解析 vol017 差分引継ぎ（2026-05-03）

## 0. このパッケージの位置づけ

前回、別スレッドのグラフィック系成果とこのスレッドのvol015/vol016成果をマージした内容はコミット済み。
本パッケージは、その後このスレッドで積み上げた **script / VM / event / NPC behavior pointer / Goal13本体側** の差分のみをGitHubへ追加するためのもの。

グラフィック復元・mapchip・OAM/VRAM/DMA logging本体は別スレッド担当のため、本差分には含めない。

## 1. このスレッドの担当範囲

- Goal 8: 条件分岐ディスパッチ系
- Goal 9: 会話・店・イベントスクリプト仕様
- Goal 7: 武器特殊能力サブシステムは前回コミット済み。今回はVM一般構造の補助のみ
- Goal 12: 全体構造再構成
- Goal 13: NPC大量表示時の処理軽減ロジック本体側

## 2. 追加解析の最大の補正

### 2-1. `$0759/$0799` は固定pointerではない

前回まで一時的に、`$0759/$0799` をobject/path pointer low/highとして強く扱っていた。
しかしbank87内のstore/readを改めて切ると、用途がobject type / routine依存で切り替わることが分かった。

確認した用途:

- `$87:82C0` 系: `$0759/$0799 -> $2A/$2B` としてpointer reader候補
- `$87:810D / 8173 / 81DF / 824E`: `$87E0/$89E0` 即値初期化系
- `$87:8459`: `$0759` を 0/1 state toggle として使用
- `$87:8528`: `$70/$71` 由来のslot componentとして使用、`$0799` はindex/counter初期化
- `$87:86E5`: `$1128/$1129` 由来の初期値、`$0799 = #$20` timer風
- `$87:E579`: position/velocity風の加算更新
- `$87:E79A`: `$0377..$0386` とのsave/restore

結論:

```text
$0759/$0799 = object slot汎用フィールド
pointer / timer / state / coordinate / copy buffer としてobject typeごとに意味が変わる
```

## 3. `$87:82C0` reader候補

`$87:82C0` 周辺は、引き続きVM/mini-script reader候補として重要。
実バイト上は以下の流れが見える。

```asm
$87:82C6  LDA $0759,X
$87:82C9  STA $2A
$87:82CB  LDA $0799,X
$87:82CE  STA $2B
...
$87:838F  LDA ($2A),Y   ; 候補
```

ただし、このreaderは全object共通ではなく、`$0759/$0799` をpointerとして使うobject typeに限定される。

## 4. `0x39850 / 0x39993` と F09A系

9-byte row末尾には以下のようなwordが出る。

```text
9A F0 -> $F09A
DB F0 -> $F0DB
C6 F0 -> $F0C6
CD F0 -> $F0CD
D4 F0 -> $F0D4
```

今回の補正:

```text
旧仮説: row末尾wordが直接 $0759/$0799 に入る
新仮説: row末尾wordは、その場でevaluator/interpreterが読む target-side blob label
```

bank87内の明示的な `$0759/$0799` storeからは、`F09A/F0DB/F0C6...` を直接slotへ入れる経路は未発見。
そのため、`0x39850/39993` 系は `object slot pointer assignment table` ではなく、条件/イベント/施設blobのlabel table寄りとして扱う。

## 5. VM / command / AIモデルの扱い

このスレッド後半では、`$87:82C0` を起点に、以下のモデルを作った。

```text
object active list
  -> object slot
  -> state / timer
  -> 条件成立時にreader/interpreter
  -> blob/mini-scriptを1ステップ実行
```

ただし、以下はまだ実コードで完全確定していない。

- opcode 0x07 = command dispatch
- Table A = opcode -> behavior/category map
- command_table 実アドレス
- `$0799` が全VM対象でwait counterとして固定されること
- NPC軽減 = command実行頻度制御で完全説明できること

本パッケージではこれらを **作業仮説** として収録し、確定事項とは分ける。

## 6. Goal13本体側の現在モデル

安全な現在モデル:

```text
Goal13本体側は、$0759/$0799固定追跡ではなく、
active object list -> object type/routine -> slot field meaning -> OAM/VM/通常更新
の順で追うべき。
```

別スレッドのOAM/VRAM/DMA logging結果は、こちらでは以下の照合材料として使う。

- active object count
- OAM visible count
- BG stable + OAM changed frame
- object出現/消滅タイミング

## 7. 今回追加したファイル

- `data/csv/bank87_0759_0799_xrefs_vol017.csv`
- `data/csv/key_contexts_vol017.csv`
- `data/csv/macro_9byte_rows_vol017.csv`
- `docs/reports/bank87_object_slot_0759_0799_reclassification_20260503.md`
- `docs/reports/vm_reader_and_f09a_blob_model_20260503.md`
- `docs/reports/goal13_core_logic_model_20260503.md`
- `docs/notes/THREAD_ASSERTION_CONFIDENCE_MAP_20260503.md`
- `docs/notes/NEXT_TASKS_VOL017_20260503.md`
- `tools/python/scan_bank87_object_slots.py`
- `tools/python/extract_macro_rows.py`
- `tools/python/find_vm_like_tables.py`

## 8. 次に攻めるべき箇所

最短は以下。

```text
1. $87:82C0 readerに入るobject type / caller を特定
2. $87:838F の ($2A),Y reader周辺を命令単位で切る
3. F09A/F0DB/F0C6系blobが native/data混在か、VM scriptかを分離
4. 0x41A10 reader huntへ戻り、0x39850/39993 row evaluator本体を探す
5. Goal13は $0A61 active list / object routine dispatch / C0:B100 / B294 table と接続
```

## 9. コミットメッセージ案

```text
Add vol017 thread diff: reclassify bank87 object slots and refine VM/NPC model
```

