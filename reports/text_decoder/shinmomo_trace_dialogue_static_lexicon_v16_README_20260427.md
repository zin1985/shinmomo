# shinmomo dialogue static lexicon assisted tracer v16

## 目的

v15までの `$12B2/$12C4` 作業窓方式は、かな文字の骨格は拾えますが、固定単語・漢字・辞書語が落ちます。

v16では、固定文章置換ではなく、**静的解析で確定している文字コード/熟語辞書**を観測tokenに重ねます。

## 重要な方針

全文を固定置換しません。

```text
NG: さん -> 桃太郎さん
OK: 1800=桃 / 1801=太 / 1802=郎 または 02A0=桃太郎 が観測されたら compound_candidates=桃太郎
OK: 1850=銀 + 1851=次 が観測されたら compound_candidates=銀次
OK: 1850=銀 + direct_lineに そうび/の/は がある場合だけ 銀次? 候補
```

## 追加した静的辞書

### キャラ名

```text
1800 桃
1801 太
1802 郎
1803 金
1804 浦
1805 島
1808 夜
1809 叉
180A 姫
1850 銀
1851 次
02A0 桃太郎
```

### 地名・会話語

```text
1811 西
1813 北
199B 旅
1847 人
029B 旅の人  暫定
0284 行く    暫定
02D7 入れ    暫定
```

### 装備・施設語

```text
181F 装
1820 備
184C 刀
18DB 鬼
19EB 穴
188F 火
1815 体
18F2 無
1A31 理
1A1A 言
```

## 出力

```text
TRACE_DIALOGUE_V16_TOKEN
TRACE_DIALOGUE_V16_LINE
```

見るところ:

```text
direct_general=
observed_tokens_all=
compound_candidates=
static_candidates=
source_state=
window_tokens=
```

## 今回の銀次そうび会話で期待する候補

```text
observed_tokens_all=1850:銀 ... 1851:次 ... 184C:刀 ...
compound_candidates=銀次 / 刀 / 銀次のそうび? / 銀次は刀もそうびできる?
```

`1851=次` や `184C=刀` が窓に出ない場合は、`source_state` から原文reader側を追う必要があります。
