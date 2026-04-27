# shinmomo dialogue v23 mode02/display equipment hints

## 目的

v22で、現在表示中の装備会話は `$12AA=02` の mode02 source から来ていることが濃厚になりました。  
ただし mode02 raw は本文そのものではなく、装備名・キャラ名などを別テーブルから差し込む format stream らしく、単純な1byte decodeでは読めません。

v23では、表示窓 `$12B2/$12B3/$12C4/$12C5` から拾えた断片に、ROM静的検索で確認した装備語を hint として付けます。

## 今回ROMで確認した語

```text
着流し = 1A 59 1A 5F 9B
はちまき = A9 A0 AE 96
わらじ = BB B6 D6
いっしょ = 91 F5 9B F8
銀次 = 18 50 18 51
桃太郎 = 18 00 18 01 18 02
```

## 出力

```text
TRACE_DIALOGUE_V23_MODE02_SOURCE
TRACE_DIALOGUE_V23_DISPLAY_LINE
```

見るところ:

```text
display_decode=
display_hints=
mode02_source_state=
```

## 注意

v23も mode02完全デコードではありません。  
ただし、現在画面に近い表示断片へ、装備名・固定語候補を付けるため、v22より読みやすくなります。
