# shinmomo source reader context tracer v21

## v20で起きていたこと

v20はROMを読めるようになりましたが、出力がまだ読みにくい状態でした。

理由は2つあります。

1. `$12AA=02` の source pointer は plain text ではなく、辞書/特殊sourceらしいため、そのまま読むと `EB 8D FC...` のような謎列になる
2. `$B1/$B2/$B3` は reader が進んだ後の位置を指すため、`C7:02F3` では `18 02 = 郎` から始まり、直前の `桃太` が欠けていた

v21では、plain source modeだけを対象にし、source pointerの少し前から読んで文脈を復元します。

## 改善点

- `$12AA != 00` は `TRACE_DIALOGUE_V21_SKIP` にして読まない
- `$12AA == 00` のとき、`src_ptr - 24` から `+72` まで読む
- `00`, `01`, `50`, `51`, `52`, `7D`, `7E` などの制御/空白/括弧を見やすく表示
- `桃太郎`, `銀次`, `そうび`, `刀`, `たき火` などの static hit を優先出力
- 出力行をかなり減らす

## 出力

```text
TRACE_DIALOGUE_V21_SOURCE
TRACE_DIALOGUE_V21_SKIP
```

見るところ:

```text
src_decode_context=
static_hits=
context_candidates=
```

## 期待

v20で

```text
src_ptr=C7:02F3
src_decode=郎...
```

になっていたものが、v21では pointer前方も含めるため、

```text
src_decode_context=...桃太郎...「...
static_hits=桃太郎...
```

のように出る可能性が高いです。

## 注意

`$12AA=02` 側はまだ未解決です。  
これはplain textではなく、辞書/特殊source/圧縮風sourceの可能性があるため、別系統として解析します。
