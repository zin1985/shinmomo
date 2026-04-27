# shinmomo text polling tracer README

## 目的

Snes9x coreでは `event.onmemoryexecute` が使えないため、WRAMの候補範囲を毎フレーム監視して、会話・店・UI表示時の raw text/display token を採取するLuaです。

## 重要

このLuaは、日本語本文をその場で完全デコードするものではありません。

新桃太郎伝説は独自文字コードを使っているため、まず以下をログに残します。

- `$7180..$72FF` の表示コード staging / operand stack 候補
- `$1900..$197F` のscript/event/text work候補
- `$1F90..$1FFF` の店/施設/UI phase work候補

ログを後でROM側の文字表・既知台詞・runtime差分と照合して、本文復元に使います。

## 使い方

1. BizHawk Lua Consoleで `shinmomo_trace_text_polling_snes9x_20260426.lua` を開く
2. NPC会話や店会話を出す
3. `TRACE_TEXT_CHANGE` と `TRACE_TEXT_RANGE` を保存する
4. ログをこちらに貼る

## ログが多すぎる場合

Lua冒頭の値を変更してください。

```lua
local DUMP_INTERVAL = 60
local MIN_CHANGE_INTERVAL = 6
local WATCH_7A00 = false
```

## 見たい行

- `TRACE_TEXT_CHANGE`
- `TRACE_TEXT_RANGE`

特に `name=display_7180` の行が重要です。
