# shinmomo dialogue v24 mode02/display candidates

## 目的

v23で以下のように、現在画面に近い断片とヒントが出るようになりました。

```text
display_decode=   のそうび !!!はちまと わじははは いっゅが!」」
display_hints=銀次のそうび? | はちまき | わらじ? | いっしょ?
```

v24ではさらに、`reconstructed_candidate=` を追加します。

## 重要

`reconstructed_candidate` は raw decode ではありません。  
`display_decode` の断片、ROM内で確認した語、画面文脈を合わせた「候補復元」です。

rawと候補を分けるため、以下の3層で出します。

```text
display_decode          実測寄り
display_hints           ROM静的確認語による候補
reconstructed_candidate 画面文脈つき復元候補
```

## 出力

```text
TRACE_DIALOGUE_V24_MODE02_SOURCE
TRACE_DIALOGUE_V24_DISPLAY_LINE
```

見るところ:

```text
display_decode=
display_hints=
reconstructed_candidate=
```

## 追加候補

現時点では、銀次装備系の2パターンを候補化します。

```text
「銀次の そうびを ととのえたか？ 銀次は 刀も そうびできるよ！」
「銀次の そうびは 着流しだ！ はちまきと わらじは 桃太郎と いっしょだがな！」
```
