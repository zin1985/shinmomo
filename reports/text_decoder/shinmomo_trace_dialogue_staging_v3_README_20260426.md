# shinmomo dialogue staging capture v3

## 目的

v2は `$12B2` を1文字としてlinebufへ積んだため、本文以外の状態値が混ざって崩れました。

v3では、1文字ずつ拾わず、会話中に変化している `$718B` / `$7197` 周辺の staging buffer をそのまま出します。

## 出力

貼ってほしい行はこれです。

```text
TRACE_DIALOGUE_V3_CAPTURE
```

## 見るところ

- `jp_runs=`
- `focus_718B_jp=`
- `focus_718B_raw=`
- `focus_7197_jp=`
- `focus_7197_raw=`

既知文字は日本語、不明は `?` です。rawも同時に出すので、後で文字表を更新できます。

## 使い方

1. 既存Luaを止める
2. このLuaを開く
3. NPC会話を出す
4. `TRACE_DIALOGUE_V3_CAPTURE` を数行貼る

## v2より軽い理由

- periodicなし
- 行バッファ積みなし
- `$718B/$7197`中心
- 変化時のみ出力
