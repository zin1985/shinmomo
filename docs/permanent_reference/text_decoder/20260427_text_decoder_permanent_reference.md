# 永久保存版: 文字・会話復元関係まとめ 2026-04-27

## 1. 会話readerの構造

### `$12AA` mode

```text
$12AA=00 : plain source
$12AA=01 : 別source展開。JSL $80:BD28 系
$12AA=02 : C0:BD98 bitstream/tree decoder
```

静的解析上の分岐:

```asm
C4:9E34  LDA $12AA
          BEQ raw_reader
          DEC A
          BNE mode02
          JSL $80:BD28
mode02:   JSL $80:BD98
raw:      JSR $9E57
```

## 2. C0:BD98 bitstream/tree decoder

`$12AA=02` は、raw byteを1byte文字として読んではいけません。  
`C0:BD98` のtree decoderで1 symbolずつ復元します。

疑似コード:

```text
node = 0
loop:
  old = node
  low  = old & 7
  high = old >> 3

  bit = next_bit(source)

  if bit == 0:
      node = table0[old]       # C0:BDEC
      mask = mask0[high]       # C0:BEEB
  else:
      node = table1[old]       # C0:BF0B
      mask = mask1[high]       # C0:C00A

  term = term_mask[low]        # C0:BDE4
  if mask & term != 0:
      continue

  return node
```

関連テーブル:

```text
C0:BDE4  terminal bit mask 8 bytes
C0:BDEC  branch0 next-node table 255 bytes
C0:BEEB  branch0 continue-mask 32 bytes
C0:BF0B  branch1 next-node table 255 bytes
C0:C00A  branch1 continue-mask 32 bytes
```

## 3. 小文字かな

```text
F5 = っ
F6 = ゃ
F7 = ゅ
F8 = ょ
```

根拠:

```text
9B F6 F5 96 BD = しゃっきん
91 F5 9B F8    = いっしょ
```

## 4. 実際に復元できたmode02会話

source:

```text
C8:A7DD / ROM offset 0x08A7DD
```

復元:

```text
「桃太郎！ 銀次の そうびを
 ととのえたか?
 銀次は 刀も そうびできる！」
「銀次の そうびは 着流しだ！
 はちまきと わらじは
 桃太郎と いっしょだがな！」
```

## 5. 重要token

| token | decoded |
|---|---|
| `02A0` | 桃太郎 |
| `18 50 18 51` | 銀次 |
| `18 4C` | 刀 |
| `1A 59 1A 5F 9B` | 着流し |
| `A9 A0 AE 96` | はちまき |
| `BB B6 D6` | わらじ |
| `91 F5 9B F8` | いっしょ |

## 6. なぜ以前の表示ログが崩れたか

`$12B2/$12B3/$12C4/$12C5` は本文ではなく表示stageです。  
ここだけをpollingすると、複合tokenの途中だけ見えます。

例:

```text
display_decode=   のそうび !!!はちまと わじははは いっゅが!」」
```

これは表示stageの断片であり、BD98から復元すると、

```text
「銀次の そうびは 着流しだ！
 はちまきと わらじは
 桃太郎と いっしょだがな！」
```

になります。

## 7. 実装ファイル

主力:

```text
scripts/lua/dialogue/shinmomo_trace_dialogue_v28_mode02_bd98_decoder_smallkana_checked_snes9x_20260427.lua
```

復元結果:

```text
reports/restored_logs/shinmomo_past_logs_restored_with_v28_rules_20260427.md
reports/restored_logs/shinmomo_older_logs_restored_v28_scan_20260427.md
```
