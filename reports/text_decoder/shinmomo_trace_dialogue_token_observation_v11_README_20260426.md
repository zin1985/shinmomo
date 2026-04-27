# shinmomo dialogue token observation tracer v11

## 目的

v10までの `corrected_context` は固定文章置換に寄っていました。  
v11では固定文章置換をやめ、実測トークンからデコードします。

## 出力の分離

```text
direct_line      $12C4/$12B2 の作業窓から読めたかな/単文字
direct_general   direct_line の句読点・重複だけ軽く整えたもの
observed_tokens  $12AA..$12CE に見えた 02xx / 18xx / 19xx / 1Axx / 1Bxx
compound_tokens  複数フレーム履歴から組めた語
```

## 固定文章置換はしない

v11では次のような置換はしません。

```text
さん -> 桃太郎さん
ぢたいじ -> 体で 鬼たいじに
```

代わりに、次を見ます。

```text
02A0 = 桃太郎
または 1800=桃 / 1801=太 / 1802=郎 が同一会話内で観測されたら compound_tokens=桃太郎
```

## 見る行

```text
TRACE_DIALOGUE_V11_LINE
```

特にここを見てください。

```text
direct_general=
observed_tokens=
compound_tokens=
```

## 限界

`$12B2/$12C4` は原文streamではなく表示作業窓です。  
そのため、桃太郎などの複数バイト語が一部しか窓に出ないことがあります。

完全復元には、次に原文reader/stream pointer側を捕まえる必要があります。
