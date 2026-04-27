# shinmomo JP text decode polling tracer README

## 目的

既知の新桃文字表をLuaに埋め込み、会話表示中のログに日本語を併記します。

- 既知コード: 日本語へ変換
- 不明コード: `?`
- `02xx`辞書: 既知分のみ展開。未知は `?`
- `18xx/19xx/1Axx/1Bxx`漢字: 既知分のみ展開。未知は `?`

## 使い方

1. BizHawk Lua Consoleで `shinmomo_trace_text_jp_decode_snes9x_20260426.lua` を開く
2. NPCに話しかける
3. `TRACE_TEXT_JP_CHAR` / `TRACE_TEXT_JP_LINE` / `TRACE_TEXT_JP_RANGE` を見る

## 注意

Snes9x coreでは execute hook が使えないため polling 方式です。

そのため、以下は取り逃がす可能性があります。

- 1フレーム内に複数文字が流れる場合
- 同じ文字が連続する場合
- `$12B2` に最終表示コードが十分長く残らない場合

ただし、`TRACE_TEXT_JP_RANGE` で `$7180..$72FF` の日本語推定も出すので、会話復元の材料として使えます。

## 見るべき行

```text
TRACE_TEXT_JP_CHAR
TRACE_TEXT_JP_LINE
TRACE_TEXT_JP_RANGE
```

`jp=` に日本語推定が出ます。不明は `?` です。
