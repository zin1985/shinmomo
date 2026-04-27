# shinmomo dialogue v28 mode02 BD98 decoder small-kana checked

## 目的

v27 の BD98 decoder はそのまま使い、F5〜F8 の小文字かな割当を明示チェックした版です。

## 結論

```text
F5 = っ
F6 = ゃ
F7 = ゅ
F8 = ょ
```

特に重要なのは `F8 = ょ` です。

## 根拠

銀次装備会話の末尾に対応するROM列:

```text
91 F5 9B F8
```

これは、

```text
い + っ + し + ょ = いっしょ
```

です。

そのため、v27で説明していた `いっしゅ` は誤りで、正しくは `いっしょ` です。  
現在のLua内の文字表も `F8 = ょ` になっていますが、v28では念のため明示上書きしています。

## 出力

```text
TRACE_DIALOGUE_V28_MODE02_DECODE
TRACE_DIALOGUE_V28_TOKEN
TRACE_DIALOGUE_V28_LINE
```
