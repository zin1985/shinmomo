# 0x39850 以降 VM命令列 再パース v2

## 結論

`0x39850` 以降は、単純な9バイト固定recordとして見るより、**9バイト周期で整列したVM命令マクロ列**として読むのがかなり自然です。

ただし前回の「`02 32` が常に opcode02 + subcode32」という見方は修正が必要です。
`02` は `0x39850` の行では opcode として読めますが、次行以降の同じ位置には `04 / 06 / 09 / 0B / ...` が並びます。

したがって、実際の構造は以下の4スロット構成に見えます。

```text
slot0: 3 bytes  = 38/37 05 01
slot1: 2 bytes  = selector/value-kind 命令候補
slot2: 2 bytes  = threshold/value 命令候補
slot3: 2 bytes  = 高位opcode pair。branch/label word候補
合計: 9 bytes
```

## 0x39850 先頭の読み

```text
83:9850 / file 0x39850:
38 05 01 02 32 10 07 9A F0
```

命令列としては、現時点では次のように置けます。

```text
38 05 01   ; slot0: op38 + operand 0x0105
02 32      ; slot1: op02 + arg 0x32
10 07      ; slot2: op10 + arg 0x07
9A F0      ; slot3: high-op pair。word 0xF09A候補
```

この見方だと、次行以降も9バイト周期で綺麗に読めます。

## サンプル

| cpu_addr | row_bytes | slot0 | slot1 | slot2 | slot3 | slot3_pair_word |
| --- | --- | --- | --- | --- | --- | --- |
| 83:9850 | 38 05 01 02 32 10 07 9A F0 | 38 05 01 | 02 32 | 10 07 | 9A F0 | 0xF09A |
| 83:9859 | 38 05 01 04 32 1A 0A 9A F0 | 38 05 01 | 04 32 | 1A 0A | 9A F0 | 0xF09A |
| 83:9862 | 38 05 01 06 32 27 10 9A F0 | 38 05 01 | 06 32 | 27 10 | 9A F0 | 0xF09A |
| 83:986B | 38 05 01 09 32 3F 17 9A F0 | 38 05 01 | 09 32 | 3F 17 | 9A F0 | 0xF09A |
| 83:9874 | 38 05 01 0B 32 51 1B 9A F0 | 38 05 01 | 0B 32 | 51 1B | 9A F0 | 0xF09A |
| 83:987D | 38 05 01 0B 32 5A 1D 9A F0 | 38 05 01 | 0B 32 | 5A 1D | 9A F0 | 0xF09A |
| 83:9886 | 38 05 01 18 32 D1 36 9A F0 | 38 05 01 | 18 32 | D1 36 | 9A F0 | 0xF09A |
| 83:988F | 38 05 01 0A 32 48 19 9A F0 | 38 05 01 | 0A 32 | 48 19 | 9A F0 | 0xF09A |
| 83:9898 | 38 05 01 14 32 AE 2F 9A F0 | 38 05 01 | 14 32 | AE 2F | 9A F0 | 0xF09A |
| 83:98A1 | 38 05 01 0C 32 63 1F 9A F0 | 38 05 01 | 0C 32 | 63 1F | 9A F0 | 0xF09A |
| 83:98AA | 38 05 01 0E 35 0E 07 9A F0 | 38 05 01 | 0E 35 | 0E 07 | 9A F0 | 0xF09A |
| 83:98B3 | 38 05 01 08 32 36 15 9A F0 | 38 05 01 | 08 32 | 36 15 | 9A F0 | 0xF09A |

## 重要な修正点

### 修正1: `02 32` は「常に opcode02 family」ではない

`0x39850` 行だけを見ると `02 32` が目立ちますが、次行は `04 32`、その次は `06 32` です。

つまり、この位置は **opcode02専用のsubhandler欄ではなく、2バイト命令slot** と見た方が自然です。

### 修正2: `9A F0 / DB F0 / C6 F0` は高位opcode pair

最後の2バイトは、以前の `target_abs = 0x30000 + word` という見方も残りますが、VM実装的には **opcode >= 0x50 の特殊命令ペア** とも読めます。

例:

```text
9A F0 -> word 0xF09A -> file 0x3F09A / CPU 83:F09A
DB F0 -> word 0xF0DB -> file 0x3F0DB / CPU 83:F0DB
C6 F0 -> word 0xF0C6 -> file 0x3F0C6 / CPU 83:F0C6
```

つまり、slot3は **分岐先/ラベルwordを兼ねた high-op命令** の可能性が高いです。

### 修正3: 9バイトrecord説は完全撤回ではない

CPU上に「9バイトrecord reader」があるわけではない、という点は前回の見立て通りです。
ただし、VM命令列としては9バイト周期に強く整列しています。

なので今後の呼称は、

```text
9-byte VM macro row
```

が一番安全です。

## A/B系の見え方

A系は主に `slot3 = 9A F0`、B系は主に `slot3 = DB F0` です。
また、対応行ではB側のslot2 wordがA側より +1 になるケースが多いです。

これは、前回の **A/B = 範囲境界/二段条件** という見立てを強めます。

## 次に攻める場所

次は `$82:8000` の **opcode >= 0x50 special VM handler** を分解するのが良いです。

特に以下を確定したいです。

```text
9A F0 が本当に 83:F09A へ分岐/ジャンプするのか
DB F0 が本当に 83:F0DB へ分岐/ジャンプするのか
C6 F0 / CD F0 / D4 F0 の意味
```

ここが固まると、`0x39850` 以降のVMマクロ列はかなり仕様書化できます。

## 出力ファイル

- `shinmomo_39850_vm_instruction_parse_v2.csv`
- `shinmomo_39850_vm_macro_rows_v2.csv`
- `shinmomo_39850_AB_pair_range_analysis_v2.csv`
- `shinmomo_39850_vm_opcode_handler_summary_v2.csv`
