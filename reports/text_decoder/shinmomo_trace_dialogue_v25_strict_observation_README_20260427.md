# shinmomo dialogue v25 strict observation

## 目的

v24では `display_hints` や `reconstructed_candidate` を出していましたが、これは他の文章に応用しにくく、文脈依存の固定補完になってしまいます。

v25では方針を変更します。

## 方針

- 文脈から予測した単語をプログラム内に追加しない
- `display_hints` を出さない
- `reconstructed_candidate` を出さない
- 実際に観測した表示tokenだけを `decoded_observed` に積む
- 足りない分は `token_events`, `mem12_window`, `source_state`, `mode_source_raw` で後から解析する

## 出力

```text
TRACE_DIALOGUE_V25_MODE_SOURCE
TRACE_DIALOGUE_V25_TOKEN
TRACE_DIALOGUE_V25_LINE
```

見るところ:

```text
decoded_observed=
token_events=
mem12_window=
source_state=
mode_source_raw=
```

## 重要

`decoded_observed` は推定復元ではありません。  
表示作業窓から観測できた文字だけです。

不足文字・熟語は、次の追加メモリ情報から詰めます。

- `token_events`: 各文字が `$12B2/$12B3/$12C4/$12C5` のどちらから来たか
- `mem12_window`: `$12A0..$12DF` の周辺状態
- `source_state`: `$1264..$1286` のsource/stack系状態
- `mode_source_raw`: mode02など特殊sourceのraw
