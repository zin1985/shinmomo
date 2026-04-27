# shinmomo dialogue token clean observation tracer v15

## 目的

v14では `$12B3=1850:銀` を「window内の偶然結合ノイズ」と見なして除外していました。  
しかし、実画面の正解が

```text
「桃太郎！　銀次の　そうびを
　ととのえたか？
　銀次は　刀も　そうびできるよ！」
```

だったため、この判断は誤りでした。

v15では `1850=銀` を本文候補として復帰します。

## 変更点

- `$12B3=1850:銀` の除外を解除
- `1850=銀` と `1851=次` が同一会話内で観測されたら `compound_candidates=銀次`
- `1850=銀` だけでも、direct_line内に `の` または `は` があれば `銀次?` 候補を出す
- 固定文章置換はしない方針を維持
- direct_lineのactive phase条件はv14と同じ

## 出力

```text
TRACE_DIALOGUE_V15_TOKEN
TRACE_DIALOGUE_V15_LINE
```

見るところ:

```text
direct_general=
observed_tokens_all=
compound_candidates=
source_state=
window_tokens=
```

## 今回の重要な認識更新

「鋼」ではなく「銀次」でした。  
したがって、`1850=銀` は装備会話では本文由来の可能性が高く、ノイズとして捨ててはいけません。
