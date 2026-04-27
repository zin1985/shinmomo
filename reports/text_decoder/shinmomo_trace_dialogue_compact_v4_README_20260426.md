# shinmomo dialogue compact raw tracer v4

## 目的

v3は `$1204/$1205` 近辺の毎フレームカウンタ変化を拾いすぎてログが大量化し、さらに `$718B/$7197` の日本語推定も本文ではなく `????` になっていました。

v4では方針を変えます。

- 日本語推定をしない
- `$1204/$1205` を監視しない
- `$718B/$7197` を本文候補から外す
- `$1260..$12CF` の会話処理ワークだけをrawで取る
- 同じ内容は重複出力しない

## 出力

貼ってほしい行はこれだけです。

```text
TRACE_DIALOGUE_V4_EVENT
```

## 見るところ

```text
raw_runs=
words_le=
state=12AD/12B2/12B4/12B5/12B6
```

## 使い方

1. 既存Luaを停止
2. BizHawk Lua Consoleで `shinmomo_trace_dialogue_compact_v4_raw_snes9x_20260426.lua` を開く
3. NPCに話しかける
4. `TRACE_DIALOGUE_V4_EVENT` だけ貼る

## 方針

日本語化は、まずrawの対応が固まってから再開します。  
今は「翻訳の見た目」より「使える材料を少なく取る」ことを優先します。
