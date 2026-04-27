# shinmomo dialogue char candidate tracer v5

## 目的

v4ログで、本文候補が `$12B2` と `$12C4` に出ていることが分かりました。  
v5は、この2箇所だけを見て、既知文字を日本語で出します。

## 出力

```text
TRACE_DIALOGUE_V5_CHAR
TRACE_DIALOGUE_V5_LINE
```

## 見るところ

```text
jp=
linebuf=
source=12B2 / 12C4
raw=
suffix=
```

## 注意

文章順はまだ完全保証しません。  
まず「どのrawがどの文字として出ているか」を低ログ量で採取する版です。

## 今回v4ログで確認できた例

- `B6 = ら`
- `93 = え`
- `A8 = の`
- `BD = ん`
- `9B = し`
- `7E = 」`

スクショの「えらいこっちゃ！」の `え / ら` が候補として取れています。
