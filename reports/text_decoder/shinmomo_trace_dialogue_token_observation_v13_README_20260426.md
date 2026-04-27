# shinmomo dialogue token observation tracer v13

## v13の目的

v12で以下のエラーが出ました。

```text
NLua.Exceptions.LuaScriptException: bad argument #1 to 'find' (string expected, got nil)
```

原因は Lua のスコープです。`make_compound_candidates()` の定義時点で `direct_line` がまだ local 宣言されておらず、関数内では nil のグローバルとして参照されていました。

v13ではこのスコープバグを修正しました。

## 追加修正

- `direct_line` を `_G.direct_line` として明示的に共有
- `string.find()` は `(_G.direct_line or "")` に対して実行
- `$12BA=1900:賊` に加え、明らかにwindow内偶然結合っぽい `$12B3=1850:銀` などを観測候補から除外
- 固定文章置換はしない方針を維持

## 出力

```text
TRACE_DIALOGUE_V13_TOKEN
TRACE_DIALOGUE_V13_LINE
```

見るところ:

```text
direct_general=
observed_tokens_all=
compound_candidates=
window_tokens=
```

## 注意

`window_tokens` はまだノイズを含みます。  
`observed_tokens_all` と `compound_candidates` のほうを優先して見てください。
