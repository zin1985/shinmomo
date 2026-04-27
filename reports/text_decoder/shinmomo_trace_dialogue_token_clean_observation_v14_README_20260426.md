# shinmomo dialogue token clean observation tracer v14

## 目的

v13は固定置換をやめた点は良かったものの、今回の「鋼のそうび」会話では、本文の前に `0す田さべ` のような表示準備ノイズも `direct_line` に混ざりました。

v14では次を行います。

- `$12B4 == 0x50` かつ `$12AD == 0x00` の active text phase だけ `direct_line` に積む
- `$12C5 != 0x00` かつ `$12C5 != 0x02` の通常外 staging は direct から除外
- 連続する同一tokenを短時間で重複抑制
- `$1264..$1286` の source_state を毎行併記

## 出力

```text
TRACE_DIALOGUE_V14_TOKEN
TRACE_DIALOGUE_V14_LINE
```

見るところ:

```text
direct_general=
observed_tokens_all=
compound_candidates=
source_state=
window_tokens=
```

## 重要

v14でも、`鋼` や `刀` のような語が `$12B2/$12C4` 作業窓に出ない場合は復元できません。  
その場合は `source_state` から原文reader / source stream pointerを追う必要があります。
