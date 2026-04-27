# shinmomo dialogue token observation tracer v12

## v12の目的

v11で方針は正しくなりましたが、観測tokenをTTLで消していたため、`TRACE_DIALOGUE_V11_LINE` の時点で `桃` や `北` が消えていました。  
v12では次の2系統を出します。

```text
observed_tokens_recent  TTL付きの直近token
observed_tokens_all     会話中に一度でも観測したtoken
```

## 改善点

- `$12BA=1900:賊` は背景ノイズとして除外
- `02D7 = 入れ` を暫定追加
- `compound_candidates` を `observed_tokens_all` から作る
- `1800=桃 + direct_line内の さん` なら `桃太郎さん?` 候補を出す
- `02D7 + direct_line内の ません` なら `入れません` 候補を出す

## 出力

```text
TRACE_DIALOGUE_V12_TOKEN
TRACE_DIALOGUE_V12_LINE
```

見るところ:

```text
direct_general=
observed_tokens_all=
compound_candidates=
```

## 注意

`compound_candidates` は候補です。  
固定文章置換ではなく、実測されたtokenから作った候補として扱ってください。
