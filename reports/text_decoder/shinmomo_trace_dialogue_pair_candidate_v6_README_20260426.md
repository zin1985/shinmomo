# shinmomo dialogue pair candidate tracer v6

## 目的

v5では `$12B2` だけを積んだため、文字順が崩れました。

v4/v5ログから、以下の読み順が自然に見えます。

```text
$12C4 -> $12B2
```

例:

```text
12C4=9A(さ), 12B2=BD(ん) => さん
12C4=93(え), 12B2=B6(ら) => えら
```

v6ではこの2byte窓をpairとして出します。

## 出力

```text
TRACE_DIALOGUE_V6_PAIR
TRACE_DIALOGUE_V6_LINE
```

## 見るところ

```text
pair_jp=
linebuf=
c4_raw=
b2_raw=
```

## 注意

まだ完全な本文復元ではありません。  
ただし、v5より順序はかなり改善する見込みです。

`$12C5==02` の場合は `$12C4` を単独文字ではなく 02xx辞書候補として扱います。未知辞書は `?` です。
