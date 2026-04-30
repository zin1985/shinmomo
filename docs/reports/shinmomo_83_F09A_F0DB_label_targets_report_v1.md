# $83:F09A / $83:F0DB / $83:F0C6... 確認 v1

## 結論

`0x39850` 系のslot3に出る

```text
9A F0 / DB F0 / C6 F0 / CD F0 / D4 F0
```

は、**opcode >= $50 special VM命令ではなく、$83:F000台のmini-script / record blob内ラベル** と見るのがかなり強くなりました。

特に重要なのは、各targetがnative code入口ではなく、多くが **`07` で始まるentry境界** に着地している点です。

## 確認したtarget

| label | 先頭5byte | 0x39847..0x39A75内参照数 | `07`始まり | 見立て |
|---|---|---:|---|---|
| `83:F09A` | `07 20 01 A0 00` | 23 | yes | A系主target。07始まりのmini-script/record stream入口 |
| `83:F0DB` | `07 80 FF 9E 00` | 20 | yes | F0C6 cluster内の07始まりentry。段階分岐の途中入口に見える |
| `83:F0C6` | `07 78 FF AC 00` | 1 | yes | F0C6 cluster内の07始まりentry。段階分岐の途中入口に見える |
| `83:F0CD` | `07 88 FF AC 00` | 1 | yes | F0C6 cluster内の07始まりentry。段階分岐の途中入口に見える |
| `83:F0D4` | `07 98 FF AC 00` | 1 | yes | F0C6 cluster内の07始まりentry。段階分岐の途中入口に見える |
| `83:F0B1` | `07 80 01 60 00` | 1 | yes | tail側に出る候補。F0B0直後で境界要確認 |

## slot3 wordの対応

0x39850周辺の末尾2byteを、

```text
file = 0x30000 + word
```

として読むと、以下のように $83:F000台へ入ります。

| slot3 bytes | dest | count | dest starts with 07? |
|---|---|---:|---|
| `9A F0` | `83:F09A` | 22 | yes |
| `B1 F0` | `83:F0B1` | 1 | yes |
| `C6 F0` | `83:F0C6` | 1 | yes |
| `CD F0` | `83:F0CD` | 1 | yes |
| `D4 F0` | `83:F0D4` | 1 | yes |
| `DB F0` | `83:F0DB` | 20 | yes |
| `0A F1` | `83:F10A` | 1 | yes |
| `1D F1` | `83:F11D` | 1 | yes |
| `36 F1` | `83:F136` | 1 | yes |
| `D0 F1` | `83:F1D0` | 1 | no |

これにより、slot3は **branch / label word** と見るのが最も自然です。

## $83:F0C6 cluster

`$83:F0C6..F0E2` は、段階的なbranch clusterに見えます。

```text
83:F0C6  07 78 FF AC 00
83:F0CB  33 17
83:F0CD  07 88 FF AC 00
83:F0D2  33 10
83:F0D4  07 98 FF AC 00
83:F0D9  33 09
83:F0DB  07 80 FF 9E 00
83:F0E0  35 F9 F0
```

つまり、`C6 F0 / CD F0 / D4 F0 / DB F0` は、同じ小さな分岐塊の中の入口違いです。

B系後半の `op37` 行が、

```text
C6 F0
CD F0
D4 F0
```

へ飛び、B系通常行が `DB F0` へ飛ぶ構造は、かなり意味があります。

## $83:F09A の位置づけ

`$83:F09A` はA系主targetです。

```text
83:F09A  07 20 01 A0 00
83:F09F  0B EC FF
83:F0A2  15 0A
83:F0A4  22 2F FC
...
```

ここもnative codeではなく、`07` から始まるmini-script / record streamの入口に見えます。

## native codeではない根拠

`$83:F09A` や `$83:F0DB` は、65816 native routine入口として見るにはかなり不自然です。

一方で、周辺には実際にnative helperっぽい小ルーチンも混在します。

例:

```asm
83:F0F9  DA          PHX
83:F0FA  8A          TXA
83:F0FB  29 03       AND #$03
83:F0FD  AA          TAX
83:F0FE  BD 06 F1    LDA $F106,X
83:F101  99 A7 0B    STA $0BA7,Y
83:F104  FA          PLX
83:F105  60          RTS
83:F106  48 68 88 A8 ; table
```

つまり、`$83:F000` 台は **mini-script/data と native helper が混在するblob** と考えるのが安全です。

## 0x39850系への反映

これで `0x39850` の9-byte macro rowは、より条件分岐record寄りに戻せます。

```text
38 05 01     ; 条件/predicate
02 32        ; selector / kind
10 07        ; threshold / value
9A F0        ; branch label word -> 83:F09A
```

B系なら、

```text
38 05 01 ...
... DB F0    ; branch label word -> 83:F0DB
```

B後半の特殊行なら、

```text
37 05 01 19 35 1C 0A C6 F0 ; -> 83:F0C6
37 05 01 1A 35 2B 0F CD F0 ; -> 83:F0CD
37 05 01 1B 35 34 11 D4 F0 ; -> 83:F0D4
```

と読めます。

## 今回の進捗

- `9A F0 / DB F0 / C6 F0 / CD F0 / D4 F0` はspecial opcodeではなくlabel word寄りと確定度アップ
- `$83:F09A / F0DB / F0C6 / F0CD / F0D4` はnative codeではなくmini-script/record entryに見える
- `$83:F0C6` clusterは複数入口を持つ段階分岐塊として見える
- `$83:F000` 台にはmini-script/dataとnative helperが混在している

## 次に攻める場所

次は、この `$83:F000` 台mini-script/record blobを読むreader側です。

候補としては、

```text
0x39850 macro rowのslot3 wordを受け取り、
$83:F09A / F0DB / F0C6... に制御を渡す処理
```

を探すのが本命です。

具体的には、`F09A/F0DB/C6F0` を `$98` script pointerへ入れている箇所、または `0x30000 + word` 変換している箇所を探すのが次の一手です。

## 出力ファイル

- `shinmomo_83_F09A_F0DB_region_hexdump_v1.txt`
- `shinmomo_83_F09A_label_targets_summary_v1.csv`
- `shinmomo_39850_slot3_to_83Fxxx_crossref_v1.csv`
- `shinmomo_83_F0C6_branch_cluster_v1.csv`
- `shinmomo_83_F09A_region_embedded_helpers_v1.txt`
