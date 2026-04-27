# shinmomo dialogue v27 mode02 BD98 decoder

## 目的

元YouTube Luaが手元になくても、ROM静的解析から `$12AA=02` の mode02 を展開できるようにした版です。

v26までは mode02 raw を「特殊source」として記録していましたが、v27では C0:BD98 のbitstream decoderをLua側に実装しています。

## 静的解析で確定した構造

```asm
C0:BD98  STZ $83
loop:
  X = $83
  low = $83 & 7
  high = $83 >> 3
  bit = next_bit([$7E], $81/$82)
  if bit == 0:
      $83 = table0[$83]      ; C0:BDEC
      mask = mask0[high]     ; C0:BEEB
  else:
      $83 = table1[$83]      ; C0:BF0B
      mask = mask1[high]     ; C0:C00A
  if mask & term_mask[low] != 0:
      loop
  return $83
```

関連テーブル:

```text
C0:BDE4  terminal bit mask 8 bytes
C0:BDEC  branch0 next-node table 255 bytes
C0:BEEB  branch0 continue-mask 32 bytes
C0:BF0B  branch1 next-node table 255 bytes
C0:C00A  branch1 continue-mask 32 bytes
```

## 出力

```text
TRACE_DIALOGUE_V27_MODE02_DECODE
TRACE_DIALOGUE_V27_TOKEN
TRACE_DIALOGUE_V27_LINE
```

見るところ:

```text
decoded_from_b1=
events_b1=
decoded_from_7E=
events_7E=
```

## 重要

`decoded_from_b1` / `decoded_from_7E` は、文脈補完ではなく、BD98 bitstreamを実際に展開した結果です。  
固定置換や `reconstructed_candidate` は入れていません。

## 期待例

銀次装備会話では、BD98展開により以下のように読めるはずです。

```text
「桃太郎! 銀次の そうびを
 ととのえたか?
 銀次は 刀も そうびできる!」
「銀次の そうびは 着流しだ!
 はちまきと わらじは
 桃太郎と いっしょだがな!」
```
