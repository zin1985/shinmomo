# shinmomo dialogue v26 reader state strict

## 目的

不足文字や「桃太郎さん」が安定して入らない原因を、文脈補完なしで追うための版です。

## 今回の静的解析で分かったこと

実際のreaderは C4:9E34 付近です。

```asm
C4:9E34  LDA $12AA
          BEQ raw_reader
          DEC A
          BNE mode02
          JSL $80:BD28
mode02:   JSL $80:BD98
raw:      JSR $9E57
```

`$12AA=02` は plain text ではなく、`$80:BD98` の bitstream/table decoder です。  
このdecoderは `$7E..$83` を内部状態として使い、source rawをそのまま文字として読めません。

## v26で追加したもの

```text
TRACE_DIALOGUE_V26_READER
```

ここに以下を出します。

```text
b1_ptr / b1_raw
mode02_ptr7E / mode02_raw7E
dp7E_83
stack1274_1287
source_state
mem12_window
```

## 出力

```text
TRACE_DIALOGUE_V26_READER
TRACE_DIALOGUE_V26_TOKEN
TRACE_DIALOGUE_V26_LINE
```

見るところ:

```text
decoded_observed=
token_events=
reader_state=
dp7E_83=
mode02_raw7E=
stack1274_1287=
mem12_window=
```

## 方針

文脈予測語は一切追加しません。  
足りない文字は、mode02 bitreader内部状態・source stack・表示stageの実測から追います。
