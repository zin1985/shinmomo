# shinmomo dialogue/text JP tracer v2

## v1からの変更

v1は会話判定が厳しすぎて何も出ない場合がありました。  
v2では、会話判定ではなく「テキスト関連WRAM範囲の変化」を広めに拾います。

## 出力

起動時:

```text
TRACE_DIALOGUE_V2_READY
```

変化時:

```text
TRACE_DIALOGUE_V2_CHANGE
```

会話が止まったとき:

```text
TRACE_DIALOGUE_V2_LINE
```

何も変化がない場合、1回だけ:

```text
TRACE_DIALOGUE_V2_HEARTBEAT
```

## 見る場所

`jp_runs=` と `linebuf=` を見てください。  
不明文字は `?` です。

## 使い方

1. 既存Luaを停止
2. BizHawk Lua ConsoleでこのLuaを開く
3. NPC会話を出す
4. `TRACE_DIALOGUE_V2_CHANGE` を数行貼る

## ログが多い場合

Lua内の以下を調整してください。

```lua
local MIN_LOG_INTERVAL = 12
```

値を大きくすると軽くなります。
