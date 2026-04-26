# shinmomo dialogue-only JP tracer

## 目的

ログが流れすぎる問題を避けるため、会話っぽい状態のときだけ日本語推定ログを出します。

## 出力

基本はこの行だけです。

```text
TRACE_DIALOGUE_JP_LINE
```

`jp=` に日本語推定が出ます。不明コードは `?` です。

## 使い方

1. 既存Luaを停止
2. BizHawk Lua Consoleで `shinmomo_trace_dialogue_only_jp_snes9x_20260426.lua` を開く
3. NPCに話しかける
4. 会話が止まると `TRACE_DIALOGUE_JP_LINE` が出ます

## 軽量化設定

Lua末尾付近の設定です。

```lua
local PRINT_CHAR_LOG = false
local PRINT_LINE_LOG = true
```

1文字ずつ見たい場合だけ `PRINT_CHAR_LOG = true` にしてください。

## 注意

Snes9xではexecute hookが使えないためpolling方式です。取り逃がしはあります。
今回の目的は、本文復元の材料として「会話時だけ軽めにログを残す」ことです。
