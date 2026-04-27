# shinmomo dialogue token candidate tracer v10

## v10の目的

v9では `raw_linebuf` と `corrected_context` を分けましたが、補正が「たき火会話」「おむすびころりん会話」に偏っていました。

v10では、次の会話も補正候補に追加します。

```text
「その体で　鬼たいじに　行くのか?
　無理を　するな　と言っても
　桃太郎のことじゃ　むだじゃろうな…」
```

## 出力

```text
TRACE_DIALOGUE_V10_TOKEN
TRACE_DIALOGUE_V10_LINE
```

見るところ:

```text
raw_jp_tokens=
corrected_general=
corrected_context=
window_tokens=
```

## 今回追加した暫定辞書

```text
0284 = 行く
```

## 今回追加したcontext補正

```text
ぢたいじ -> 体で 鬼たいじに
くのか??ぅを -> 行くのか? 無理を
とっも -> と言っても
もももことじ -> 桃太郎のことじゃ
むだじゃな -> むだじゃろうな…
```

## 注意

`corrected_context` は確定デコードではなく、スクショ照合補正です。  
`raw_jp_tokens` と分けて保存してください。
