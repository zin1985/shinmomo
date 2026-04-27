# 新桃太郎伝説 会話固定単語・漢字補完 v16 解析メモ

## 結論

`$12B2/$12C4` は表示作業窓であり、かなの骨格は取れるが、固定単語・漢字・辞書語は落ちやすい。

そのため、固定文章置換ではなく、以下の3層で扱う。

```text
direct_general      $12B2/$12C4から取れたかな・記号
observed_tokens_all  $12AA..$12CEに見えた02xx/18xx/19xx/1Axx/1Bxx
static_candidates    静的辞書と観測tokenを合成した候補
```

## 今回の認識更新

画面文は「鋼」ではなく「銀次」。

```text
「桃太郎！　銀次の　そうびを
　ととのえたか？
　銀次は　刀も　そうびできるよ！」
```

したがって、前にノイズ扱いした `1850=銀` は本文候補として復帰する。

```text
1850 = 銀
1851 = 次
184C = 刀
181F = 装
1820 = 備
```

## 静的解析で補える語

| 語 | token | 扱い |
|---|---|---|
| 桃太郎 | 02A0 または 1800+1801+1802 | compound |
| 銀次 | 1850+1851 | compound |
| 金太郎 | 1803+1801+1802 | compound |
| 浦島 | 1804+1805 | compound |
| 夜叉姫 | 1808+1809+180A | compound |
| 北西 | 1813+1811 | compound |
| 旅の人 | 029B または 199B+1847 | compound |
| 装備 | 181F+1820 | compound |
| 刀 | 184C | single kanji |
| 鬼 | 18DB | single kanji |
| 穴 | 19EB | single kanji |
| 火 | 188F | single kanji |
| 無理 | 18F2+1A31 | compound |
| 言 | 1A1A | single kanji |

## まだ残る限界

`$12B2/$12C4` に出ないtokenは、静的辞書を追加しても観測できない。  
`銀次` の `次` や `刀` が出ない場合、次は `source_state=$1264..$1286` から原文reader / source pointerを追う必要がある。
