# $82:8000 の opcode >= $50 special VM handler 解析 v1

## 結論

`$82:8000` は、通常VM dispatcher `$84:87A2` から呼ばれる **opcode >= $50 用の二次dispatcher** です。

ただし重要なのは、`$82:8031` のspecial tableは無制限ではなく、静的には **opcode `$50..$92` まで** が有効範囲に見えることです。

```text
special table start : $82:8031
first handler start : $82:80B7
entry size          : 2 bytes
entry count         : 67
valid opcode range  : $50..$92
```

## dispatcher の流れ

`$84:87A2` 側では、opcodeが `$50` 以上で、かつ `$1398 != 0` のときだけ `$82:8000` に入ります。

```asm
84:87A7  CMP #$50
84:87A9  BCC normal_dispatch
84:87AB  LDY $1398
84:87AE  BEQ normal_dispatch
84:87B0  JSL $82:8000
```

`$82:8000` 側は、

```asm
82:8009  SBC #$0050
82:8015  LDA $8031,Y
82:8018  STA $06
82:8021  LDY #$01
82:8023  JMP ($0006)
```

という形で、`opcode - $50` をindexにして `$82:8031` からhandlerを選びます。

## 有効なspecial opcode範囲

最初のhandlerが `$82:80B7` から始まるため、`$82:8031..$82:80B6` がテーブルと見るのが自然です。

つまり有効範囲は、

```text
$50..$92
```

です。

先頭20件はこうです。

| opcode | handler | handler先頭 |
|---:|---|---|
| `50` | `82:80B7` | `B7 98 AA 20 4B 9F 22 C5 9B 84 60 B7 98 AA 20 94` |
| `51` | `82:80C2` | `B7 98 AA 20 94 9F 22 C5 9B 84 60 B7 98 20 CA A0` |
| `52` | `82:80CD` | `B7 98 20 CA A0 AD C8 1F AE C9 1F 22 D2 9B 84 22` |
| `53` | `82:80E1` | `C2 20 A9 0C 81 85 0F E2 20 22 14 AC 80 AE 68 00` |
| `54` | `82:81E0` | `A9 01 AE 8F 19 E0 04 B0 02 A9 00 22 CE 9B 84 22` |
| `55` | `82:81F4` | `C2 20 A9 11 82 85 0F E2 20 22 14 AC 80 AE 68 00` |
| `56` | `82:8278` | `C2 20 A9 95 82 85 0F E2 20 22 14 AC 80 AE 68 00` |
| `57` | `82:8326` | `20 26 80 B2 06 AA BD E5 19 22 CE 9B 84 A9 03 22` |
| `58` | `82:833A` | `20 26 80 B2 06 AA 20 36 96 A9 03 22 C7 9B 84 60` |
| `59` | `82:834A` | `B7 98 22 A4 BB 80 22 CE 9B 84 22 C5 9B 84 60 20` |
| `5A` | `82:8359` | `20 26 80 B2 06 AA BD D5 19 22 CE 9B 84 A9 03 22` |
| `5B` | `82:836D` | `64 AA 22 C1 9B 84 60 B7 98 8D 87 19 C8 B7 98 C9` |
| `5C` | `82:8374` | `B7 98 8D 87 19 C8 B7 98 C9 FF F0 0D 8D 88 19 C8` |
| `5D` | `82:8395` | `B7 98 20 54 BA AD 87 1D F0 0C AE 77 1D 8E 8B 19` |
| `5E` | `82:83B7` | `C2 20 A9 C8 83 85 0F E2 20 22 14 AC 80 EE 68 12` |
| `5F` | `82:83F7` | `C2 20 B7 98 85 06 E2 20 C8 C8 B7 98 22 7B 89 86` |
| `60` | `82:8423` | `C2 20 B7 98 30 07 E2 20 CD 87 19 D0 24 C8 C8 C2` |
| `61` | `82:8461` | `20 26 80 A0 03 B7 98 AA C8 A5 06 05 07 F0 02 B2` |
| `62` | `82:84B1` | `20 26 80 B2 06 8D 89 1D A0 03 B7 98 8D 8A 1D C2` |
| `63` | `82:8527` | `9C 89 12 9C 96 12 B7 98 08 C8 28 F0 6D 48 20 26` |

## 0x39850 の slot3 への影響

前回、`0x39850` の末尾2バイト、

```text
9A F0
DB F0
C6 F0
CD F0
D4 F0
```

などを **opcode >= $50 の特殊VM命令ペア** とも読めるか検討しました。

しかし、今回の `$82:8000` table範囲確認により、この見方はかなり後退です。

理由は、これらの first byte が `$92` を超えており、`$82:8031` の有効テーブル範囲外だからです。

slot3 wordの要約は以下です。

| bytes | count | file+word | CPU addr | first byte special valid? | second byte special valid? |
|---|---:|---|---|---|---|
| `22 E8` | 3 | `0x03E822` | `83:E822` | no | no |
| `9A F0` | 22 | `0x03F09A` | `83:F09A` | no | no |
| `B1 F0` | 1 | `0x03F0B1` | `83:F0B1` | no | no |
| `C6 F0` | 1 | `0x03F0C6` | `83:F0C6` | no | no |
| `CD F0` | 1 | `0x03F0CD` | `83:F0CD` | no | no |
| `D4 F0` | 1 | `0x03F0D4` | `83:F0D4` | no | no |
| `DB F0` | 20 | `0x03F0DB` | `83:F0DB` | no | no |
| `0A F1` | 1 | `0x03F10A` | `83:F10A` | no | no |
| `1D F1` | 1 | `0x03F11D` | `83:F11D` | no | no |
| `36 F1` | 1 | `0x03F136` | `83:F136` | no | no |
| `D0 F1` | 1 | `0x03F1D0` | `83:F1D0` | no | no |
| `2B F2` | 1 | `0x03F22B` | `83:F22B` | no | no |
| `E7 F2` | 1 | `0x03F2E7` | `83:F2E7` | no | no |
| `A3 F3` | 1 | `0x03F3A3` | `83:F3A3` | no | no |
| `B6 F3` | 1 | `0x03F3B6` | `83:F3B6` | no | no |
| `D0 F3` | 1 | `0x03F3D0` | `83:F3D0` | no | no |
| `D9 F3` | 1 | `0x03F3D9` | `83:F3D9` | no | no |
| `72 F4` | 1 | `0x03F472` | `83:F472` | yes | no |
| `41 F5` | 1 | `0x03F541` | `83:F541` | no | no |

## 修正後の見立て

`0x39850` 系の末尾2バイトは、special opcode pairではなく、

```text
16-bit branch/label word
```

として見る方が強くなりました。

例:

```text
9A F0 -> word $F09A -> file $03F09A / CPU $83:F09A
DB F0 -> word $F0DB -> file $03F0DB / CPU $83:F0DB
C6 F0 -> word $F0C6 -> file $03F0C6 / CPU $83:F0C6
```

つまり、前回の「high-op命令 兼 branch/label word候補」から、今回は **branch/label word寄り** に認識を戻します。

## 0x39850 再パースへの反映

現時点の読みはこうです。

```text
38 05 01 02 32 10 07 9A F0
```

これを完全に逐次opcode列として読むのではなく、

```text
38 05 01     ; 条件/predicate入口
02 32        ; selector / kind 風の2バイト
10 07        ; value / threshold 風の2バイト
9A F0        ; branch/label word
```

という **9-byte VM macro row / 条件分岐recordに近い構造** として扱うのが、今のところ一番安全です。

「CPU上の9バイト専用reader」はまだ見つかっていませんが、`$82:8000` の確認によって、少なくとも `9A F0` をspecial opcode列として読む線は薄くなりました。

## 次に攻める場所

次は、`9A F0 / DB F0 / C6 F0 / CD F0 / D4 F0` が指す先、

```text
$83:F09A
$83:F0DB
$83:F0C6
$83:F0CD
$83:F0D4
```

を実際のVM entry / native code / data labelとして確認するのが良いです。

ここがコードまたはVM streamの入口なら、slot3はbranch/labelでかなり確定に近づきます。

## 出力ファイル

- `shinmomo_82_8000_special_vm_handler_disasm_v1.txt`
- `shinmomo_82_8000_special_opcode_table_v1.csv`
- `shinmomo_39850_slot3_word_special_table_check_v1.csv`
- `shinmomo_39850_slot3_word_summary_v1.csv`
