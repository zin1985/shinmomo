# $84:89C7 の正体確認 v1

## 結論

`$84:89C7` は **opcode $02 family の動的 long-call trampoline** です。

中身は1命令だけです。

```asm
84:89C7  DC 2A 00    JMP [$002A]
```

つまり、`$2A-$2C` に積まれた24bitアドレスへ飛ぶための間接ジャンプです。

## なぜ JSL $84:89C7 なのか

opcode `$02` handler は `$84:9BEE` の3バイト表から long pointer を取り出し、`$2A-$2C` に入れています。

```asm
84:89B3  LDA $9BEE,X
84:89B6  STA $2A
84:89B8  LDA $9BEF,X
84:89BB  STA $2B
84:89C2  JSL $84:89C7
```

`$84:89C7` はその直後に、

```asm
84:89C7  JMP [$002A]
```

で実際の subhandler へ飛びます。

この形にしている理由は、65816には **JSL [indirect long]** がないためです。
先に `JSL` で戻り先をstackへ積み、trampoline内で `JMP [$002A]` して、飛び先subhandlerが `RTL` で戻る構造です。

流れはこうです。

```text
opcode $02 handler
  ↓
subcodeを読む
  ↓
$84:9BEE + (subcode - 1) * 3 から 24bit pointerを取得
  ↓
$2A-$2Cへ格納
  ↓
JSL $84:89C7
  ↓
84:89C7: JMP [$002A]
  ↓
subhandler本体
  ↓
RTL
  ↓
84:89C6: RTS
```

## 重要なラベル修正

前回まで、VM coreを旧表記で `89:89A5` などと書いていましたが、CPU long addressとしては **bank $84** 側です。

修正後の重要ラベルは以下です。

```text
$84:87D4 = opcode dispatch table
$84:89A5 = opcode $02 handler
$84:89C7 = indirect long-call trampoline
$84:9BEE = opcode $02 subhandler long-pointer table
```

この修正はかなり重要です。
`JSL $84:89C7` の実アドレスを追うと、file PC `0x489C7` に対応し、ここに `DC 2A 00` が存在します。

## $84:9BEE table の再評価

これで `$84:9BEE` は、前回の「subresource / subscript pointer table」より踏み込んで、**opcode $02 の subhandler long-pointer table** と見てよいです。

`0x39847..0x399E5` で使われる subcode は以下です。

| subcode | 使用回数 | target | target file pc | 96byte以内の最初のRTL位置 | target先頭16byte |
|---:|---:|---|---|---:|---|
| `32` | 2 | `85:990C` | `0x05990C` | `23` | `EE 68 12 9C 65 03 C2 20 A9 24 99 85 0F E2 20 A9` |

## 0x39850 の読み直し

`0x39850` はHiROM CPUアドレスでは `83:9850` です。

```text
83:9850 / file 0x39850:
38 05 01 02 32 10 07 9A F0
```

これは引き続き、

```text
38 05 01        ; opcode38 + operand 0x0105
02 32           ; opcode02 + subcode32
10 07 9A F0     ; subhandler側が読むtail候補
```

と見るのが自然です。

ただし今回の確認により、`02 32` の先は、

```text
$84:9BEE[subcode32] = $85:990C
```

への **実行可能native routine呼び出し** であることが確定寄りになりました。

## 今回の進捗

- `$84:89C7` はparserではなく、3byteの間接long-call trampolineと確認
- `$84:9BEE` はopcode `$02` のsubhandler long-pointer tableと再評価
- 旧 `89:` ラベルはCPU long addressとしては `$84:` へ修正が必要
- `0x398xx` の `02 xx` はsubhandler native routine呼び出しとして読める
- 次は `$85:990C` subhandler、特に `02 32 10 07 9A F0` のtail消費を追うのが本命

## 出力ファイル

- `shinmomo_84_89C7_trampoline_disasm_v1.txt`
- `shinmomo_opcode02_9BEE_subtable_hirom_v2.csv`
- `shinmomo_opcode02_9BEE_used_by_398xx_hirom_v2.csv`
- `shinmomo_39847_399E5_macro_parse_hirom_v2.csv`
