# 新桃太郎伝説解析 vol013 マージ用引継ぎ情報（2026-04-30）

このフォルダは、別スレッド側の解析結果とマージするための GitHub コミット用パッケージです。  
ROM本体は含めていません。解析成果物、CSV、Lua/Python、hexdump、レポートのみを収録しています。

## 0. まず最重要：アドレス表記の補正

今回の終盤で、ROMのCPUアドレス換算は **LoROM換算**で扱うべきと確認しました。  
根拠は、既知の `C0:BD98` bitstream/tree decoder が file PC `0x003D98` に対応することです。

過去成果物には、一部 HiROM 風に読んだ旧CPUラベルが残っています。  
**マージ時は file PC を正とし、CPUラベルは以下のLoROM表で読み替えてください。**

| file PC | 正しいLoROM CPU | 内容 |
|---:|---|---|
| `0x003D98` | `$80:BD98` | mode02 `C0:BD98` bitstream/tree decoder |
| `0x039850` | `$87:9850` | `0x41A10` 系 target-side 9-byte macro row entry |
| `0x039993` | `$87:9993` | B系内部label/entry候補、実効は `$87:9994` も要注意 |
| `0x03F09A` | `$87:F09A` | A系主target blob entry |
| `0x03F0DB` | `$87:F0DB` | B系主target blob entry |
| `0x03F0C6` | `$87:F0C6` | B後半特殊target blob entry |
| `0x03F0CD` | `$87:F0CD` | B後半特殊target blob entry |
| `0x03F0D4` | `$87:F0D4` | B後半特殊target blob entry |
| `0x041A10` | `$88:9A10` | 8-byte 条件/target table 本命 |
| `0x041C30` | `$88:9C30` | `0x39850` へつながるtable row |
| `0x041D68` | `$88:9D68` | `0x39993` へつながるtable row |
| `0x0487D4` | `$89:87D4` | script VM opcode dispatch table |
| `0x0489A5` | `$89:89A5` | opcode `$02` handler |
| `0x0489C7` | `$89:89C7` | opcode `$02` trampoline: `JMP [$002A]` |
| `0x049BEE` | `$89:9BEE` | opcode `$02` long pointer table |
| `0x028000` | `$85:8000` | opcode `>= $50` special dispatcher（旧成果物の `$82:8000` は補正対象） |
| `0x028031` | `$85:8031` | special opcode table |
| `0x05990C` | `$8B:990C` | opcode `$02` subcode `$32` target（旧成果物の `$85:990C` は補正対象） |

## 1. 最新の重要成果

### 1-1. mode02 会話復元

- `$12AA=02` は plain text ではなく、`$80:BD98` の bitstream/tree decoder で復元する形式。
- v28 Luaで mode02 会話復元が可能になった。
- 小文字かなは以下で確定寄り。
  - `F5=っ`
  - `F6=ゃ`
  - `F7=ゅ`
  - `F8=ょ`
- `C8:A7DD` から銀次装備会話、おむすびころりん穴周辺会話を復元済み。
- v33 オフラインダンパで `C8:A7DD` chain の複数segmentをCSV化済み。
- 注意点：`<00>` 終端後もbyte境界とは限らず、`bitcnt` を含む chain state 管理が必要。

### 1-2. 静的解析の主成果：`0x41A10 -> 0x39850 / 0x39993` 系

当初は `0x39847..0x399E5` を9バイト固定record列と見たが、解析を進めて以下に修正。

```text
0x41A10 8-byte table
  ↓
0x39850 / 0x39993 target-side area
  ↓
9-byte VM macro row / 条件付きblob pointer row
  ↓
slot3 word = F09A / F0DB / F0C6 / F0CD / F0D4
  ↓
$87:F09A / $87:F0DB / $87:F0C6... object/path blobへ
```

代表行：

```text
file 0x39850 / $87:9850:
38 05 01 02 32 10 07 9A F0
```

現在の安全な読み：

```text
38 05 01     ; 条件/predicate入口候補
02 32        ; selector / kind 風の2byte
10 07        ; value / threshold 風の2byte
9A F0        ; branch/blob label word -> file 0x03F09A / $87:F09A
```

B系通常行では `DB F0 -> $87:F0DB`、B後半特殊行では `C6 F0 / CD F0 / D4 F0` がそれぞれ `$87:F0C6 / F0CD / F0D4` へ入る。

### 1-3. `slot3 target` の受け側

`$87:F09A` 系targetは、会話VMのbranch先というより **object / NPC / animation / path 系のmini-script/blob** に見える。

受け側reader候補として最有力なのは：

```asm
87:82C6  BD 59 07    LDA $0759,X
87:82C9  85 2A       STA $2A
87:82CB  BD 99 07    LDA $0799,X
87:82CE  85 2B       STA $2B
...
87:838F  B1 2A       LDA ($2A),Y
```

つまり、現時点の見立ては：

```text
$0759/$0799 = F09A / F0DB / F0C6...
  ↓
$2A/$2B
  ↓
($2A),Y
  ↓
$87:F09A 系 blob を評価
```

未確定なのは、`0x39850` の9-byte row末尾wordを `$0759/$0799` に設定する側。

### 1-4. opcode `$02` family / `$89:9BEE`

- file `0x0489A5` = `$89:89A5` が opcode `$02` handler。
- `opcode $02` は直後1byteをsubcodeとして読み、`$89:9BEE + (subcode - 1) * 3` から24bit pointerを取る。
- file `0x0489C7` = `$89:89C7` は `JMP [$002A]` だけの trampoline。
- ただし、LoROM補正前の成果物には `$84:89C7` 等の旧表記が残るため注意。

### 1-5. graphics / VRAM 方面

- raw 2bpp / 4bpp tile dump、候補PNG、VRAM/CGRAM/tilemap dump用Luaを作成済み。
- ただし、新桃の主要グラフィックは圧縮・実行時展開・VRAM転送が絡む可能性が高く、静的ROM rawだけでは確定しにくい。
- グラフィック復元は別スレッドやエミュdump中心で進める方がよい。

## 2. 現在の認識変更点

### 2-1. `0x39850` 系は会話分岐より object/path 系に寄った

以前：

```text
会話・店・イベント分岐scriptの可能性が高い
```

現在：

```text
object / NPC / animation / path 系の条件付きblob pointer table の可能性が高い
```

理由：

- `$87:F09A` 以降が `07 ...` で始まるmini-script/blob風。
- `$87:F000` 台にはnative helperとdata/blobが混在。
- `$87:82C0` が `$0759/$0799` をpointerとして読み、object slot内の状態更新に見える。

### 2-2. `9A F0` などは special opcode ではなく label word 寄り

`$85:8000` special dispatcherの有効tableは `$50..$92` 付近までと見える。  
そのため、`9A / DB / C6 / CD / D4 / F0` を special opcode と読む線は後退。

現在は：

```text
9A F0 = little endian word $F09A = $87:F09A へのlabel/blob pointer
```

として扱うのが安全。

## 3. 次にマージ先で攻めるべき場所

優先度順：

1. **`$0759/$0799` への設定処理のうち、即値ではなくtable/rowから値を入れる箇所**
   - `0x39850` のslot3 wordを `$0759/$0799` に積む設定側を探す。
2. **`$88:9A10` 8-byte table reader本体**
   - `0x41A10` file PCは有力だが、reader本体は未確定。
3. **`$87:810D / $87:8173 / $87:81DF / $87:824E` object slot初期化系**
   - `$0759/$0799` に即値pointerを設定する類似処理あり。
4. **`$83:AE3B` 周辺 object state save/restore**
   - object slot stateの保存・復帰層として関連する可能性。
5. **`$85:F37D / $85:F9F6` 周辺**
   - 外部状態から `$0799/$07D9` に値を入れる系として候補。
6. **mode02会話のroot pointer採集**
   - v33ダンパで大量会話化するには、runtimeからroot候補を集めるのが早い。

## 4. 13ゴール進捗（暫定）

| 目標 | 暫定進捗 | コメント |
|---|---:|---|
| 1. スクリプトVMの値の流れを確定する | 95% | `$89:87D4` dispatcher、opcode02、pointer transfer系は前進。LoROM補正が必要。 |
| 2. `89:9A44 -> 82:FD67` 系を確定する | 80% | このスレでは主対象外。過去成果維持。 |
| 3. `7E:201E..2030` / `7E:3004..303C` の正体確定 | 60% | object/path slot理解により周辺理解は微増。 |
| 4. `81:8D87` 戻り4値の意味確定 | 30% | 未着手。 |
| 5. 店・施設UIのレコード構造確定 | 78% | 直接は進まず。`0x39850` は店よりobject/path寄りへ修正。 |
| 6. 道具表・装備表を実用ダンプ | 82% | flag tripletクラスタ整理済み。 |
| 7. 武器特殊能力サブシステム整理 | 18% | 未着手。 |
| 8. 条件分岐ディスパッチ系確定 | 70% | `0x41A10 -> 0x39850/39993 -> slot3 blob` の地図が前進。readerは未確定。 |
| 9. 会話・店・イベントスクリプト仕様書 | 63% | mode02会話とVM系は前進。ただし`0x39850`は会話よりobject/path寄りへ補正。 |
| 10. 文字コード・表示系の実用化 | 97% | BD98 mode02復元、小文字かな確定寄り。 |
| 11. 外部データ化 | 70% | 会話CSV・item/equip CSV・VM macro CSVが増加。 |
| 12. 全体構造を人間が読める形で再構成 | 80% | LoROM補正とobject/path系の整理で大きく前進。 |
| 13. NPC大量表示時の処理軽減ロジック特定 | 42% | `$87:F09A` object/path blob・`$0759/$0799` pointer理解で前進。 |

## 5. マージ時の注意

- ROM本体はこのパッケージに含めていない。
- 旧成果物にはCPU bank旧表記が混在する。**file PCを正とし、LoROM換算表で読み替えること。**
- `0x39850` 系は、会話外部データ化よりもNPC/object/path制御に寄せて再分類した方が安全。
- `0x41A10` は引き続き有力だが、reader本体未発見。direct xrefが無い可能性あり。
- 生成物はGitHubコミット用に個別ファイルとして整理済み。ただしユーザー指示により今回はZIPにもまとめている。
