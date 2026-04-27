# shinmomo dialogue token candidate tracer v9

## v9の目的

v8は補正が1つ前の「おむすびころりん」会話に寄りすぎていました。  
v9では出力を3層に分けます。

```text
raw_linebuf          実測寄り
corrected_general    句読点・重複・既知辞書/漢字だけの軽補正
corrected_context    スクショ文脈に基づく強補正候補
```

## 追加

```text
188F = 火
```

既存/重要:

```text
1800 = 桃
1801 = 太
1802 = 郎
18DB = 鬼
19EB = 穴
1A1A = 言
02A0 = 桃太郎
02AC = オニ
029B = 旅の人（暫定）
```

## 今回のたき火会話への文脈補正

```text
^！ん！ -> 桃太郎さん！
き?にににに -> たき火に
あたっ いきよ -> あたって いきなよ
あったいよー -> あったかいよー
```

## 出力

```text
TRACE_DIALOGUE_V9_TOKEN
TRACE_DIALOGUE_V9_LINE
```

見るところ:

```text
raw_linebuf=
corrected_general=
corrected_context=
window_tokens=
```

## 注意

`corrected_context` は確定デコードではありません。  
スクショと照合した補正候補です。GitHub資料では raw と correction を必ず分けてください。
