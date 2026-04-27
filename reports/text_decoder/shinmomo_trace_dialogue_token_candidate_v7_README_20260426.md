# shinmomo dialogue token candidate tracer v7

## v6からの改善

v6では通常pairの読み方は当たりでしたが、以下が問題でした。

- `c4 == b2` のとき同じ文字を二重に出していた
- `$12C5 == 02` のとき、02xx辞書/熟語トークンなのに `$12B2` まで続けて読んで崩れていた
- `桃太郎` / `オニ` / `旅の人` のような辞書トークンを見落としていた

v7では以下に変更します。

```text
通常: $12C4 -> $12B2
同値: 1文字だけ
$12C5=02: $12C4を02xx辞書トークンとして読む。$12B2は原則読まない。
```

## 暫定追加辞書

```text
029B = 旅の人   # 今回スクショとログ位置からの暫定
```

既存辞書:

```text
02A0 = 桃太郎
02AC = オニ
02B0 = きんたん
02B9 = ゆうき
02C0 = おにぎり
02CD = ちから
02CE = あしゅら
```

## 出力

```text
TRACE_DIALOGUE_V7_TOKEN
TRACE_DIALOGUE_V7_LINE
```

## 見るところ

```text
token_jp=
linebuf=
window_tokens=
mode=
```

`window_tokens` には `$12AA..$12CE` 内に見つかった `02xx` や既知漢字候補も出します。
