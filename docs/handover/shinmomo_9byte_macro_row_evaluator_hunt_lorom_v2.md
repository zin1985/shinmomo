# 9-byte macro row evaluator 本体探索 v2（LoROM補正版）

## 最重要修正：このROMはLoROM扱いが正しい

今回、`C0:BD98` の実ファイル位置と照合して、前回のHiROM換算ラベルを修正しました。

正しい対応は以下です。

| file PC | 正しいLoROM CPU | 備考 |
|---:|---|---|
| `0x003D98` | `$80:BD98` | BD98 bitstream decoder |
| `0x039850` | `$87:9850` | 9-byte macro row entry |
| `0x03F09A` | `$87:F09A` | slot3 target |
| `0x03F0DB` | `$87:F0DB` | slot3 target |
| `0x041A10` | `$88:9A10` | 8-byte branch/object table |
| `0x0489C7` | `$89:89C7` | opcode02 trampoline |

つまり、前回までの `$83:F09A` 表記は、CPUアドレスとしては **`$87:F09A`** に修正です。

## 今回の結論

9-byte macro rowの末尾slot3、

```text
9A F0 / DB F0 / C6 F0 / CD F0 / D4 F0
```

は、LoROM補正後は以下へ入ります。

```text
9A F0 -> file 0x03F09A -> $87:F09A
DB F0 -> file 0x03F0DB -> $87:F0DB
C6 F0 -> file 0x03F0C6 -> $87:F0C6
CD F0 -> file 0x03F0CD -> $87:F0CD
D4 F0 -> file 0x03F0D4 -> $87:F0D4
```

そして、この `$87:F09A` 系を読む受け側としては、**`$87:82C0..$87:83C7` 周辺がかなり有力**です。

## `$87:82C0` 周辺が有力な理由

`$87:82C0` 付近には、object slotから `$0759/$0799` を読み、`$2A/$2B` に入れて、`B1 $2A` でblobを読む処理が見えます。

```asm
87:82C0  BD 59 06    LDA $0659,X
87:82C3  9D 19 06    STA $0619,X
87:82C6  BD 59 07    LDA $0759,X
87:82C9  85 2A       STA $2A
87:82CB  BD 99 07    LDA $0799,X
87:82CE  85 2B       STA $2B
...
87:838F  B1 2A       LDA ($2A),Y
...
```

これは、`$0759/$0799` に入っている16bit pointerを使って、同bank内のblobを読む構造に見えます。

つまり、

```text
$0759/$0799 = F09A / F0DB / F0C6...
  ↓
$2A/$2B
  ↓
($2A),Y
  ↓
$87:F09A blob を評価
```

という流れがかなり濃いです。

## ただし、まだ未確定の部分

今回見つかったのは、**slot3 target blobのreader側**です。

未確定なのは、

```text
0x39850 の9-byte macro row末尾wordを読み、
$0759/$0799 へ入れる処理
```

です。

つまり、

```text
9-byte macro row
  ↓
slot3 word = F09A
  ↓
$0759/$0799 に設定
```

この「設定側」はまだ見つかっていません。

## 9-byte macro rowの現在の位置づけ

`0x39850` 周辺は、イベント会話VMよりも、**object/NPC/animation/path系の条件付きblob pointer table** の可能性が上がりました。

理由は、`$87:F09A` 以降のblobが、

```text
07 20 01 A0 00 ...
07 80 FF 9E 00 ...
```

のような形で、さらに近くにnative helperや座標/描画らしい処理が混ざっているためです。

これは、会話VMのbranch先というより、**NPC/objectの動き・表示・状態更新用のmini-script/path blob** に見えます。

## 以前の調査からの修正点

### 修正1：CPU bank表記

```text
誤: $83:F09A
正: $87:F09A
```

同様に、

```text
誤: $84:8078
正: $89:8078
```

です。

### 修正2：受け側の本命

前回は `$84:8078`、つまり補正後の `$89:8078` を受け側として見ていました。

ただし今回、`$87:F09A` 周辺を実際に読む処理としては、`$87:82C0` の方が近そうです。

`$89:8078` は通常script VMの受け側であり、`$87:F09A` blobの主readerではない可能性が上がりました。

## 今回の進捗

- LoROMアドレス換算を修正
- `0x39850` は `$87:9850`、slot3 targets は `$87:F09A` 系と再ラベル
- `$87:82C0..83C7` が `$87:F09A` blob reader候補として浮上
- `$0759/$0799` がblob pointer保持slotとしてかなり有力
- 未解決は「9-byte rowのslot3 wordを `$0759/$0799` に積む設定側」

## 次に攻める場所

次は `$0759/$0799` への設定箇所のうち、**即値ではなくtable/rowから値を入れる処理**を追うのが本命です。

候補は以下です。

```text
1. $87:810D / 8173 / 81DF / 824E のobject slot初期化系
2. $83:AE3B 周辺の object state save/restore
3. $85:F37D / F9F6 周辺の外部状態から $0799/$07D9 を入れる系
4. $88:9A10 8-byte table reader本体
```

特に、`$88:9A10` の8-byte tableから `0x9850` へ飛ぶ流れと、`$87:9850` の9-byte rowから `$87:F09A` へ飛ぶ流れは、**同じobject/script resource chain** として再整理する価値があります。

## 出力ファイル

- `shinmomo_lorom_address_correction_table_v1.csv`
- `shinmomo_0759_0799_pointer_xrefs_lorom_v1.csv`
- `shinmomo_slot3_reader_lorom_candidate_functions_v2.csv`
- `shinmomo_87_82C0_F09A_blob_reader_hexdump_v1.txt`
