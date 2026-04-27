# shinmomo source reader contextual static lexicon tracer v19

## 目的

ユーザーが画面文脈から確認した語を、ROM内の実出現で照合し、source reader辞書に追加した版です。

v19では v18 の `static_hits=` に加えて、

```text
context_candidates=
```

を出します。

## 方針

全文固定置換はしません。  
ROM内に見つかったtoken/部分列だけを辞書化し、複数tokenが同じsource windowに見えた場合だけ候補化します。

## 追加した文脈語

```text
銀次 / 銀次の / 銀次は
刀
装備
そうび
できるよ
たき火
おむすびころりん
鬼たいじ
行くのか
するな
入れ
旅の人
```

## 出力

```text
TRACE_DIALOGUE_V19_SOURCE
```

見るところ:

```text
src_decode=
static_hits=
context_candidates=
```

## 注意

以下はROM完全一致が見つかりませんでした。

```text
銀次のそうび
銀次は刀
刀も
そうびを
北西
入れません
```

これは「存在しない」という意味ではなく、制御コード、辞書、source reader分岐で分断されている可能性があります。  
v19では、`銀次の` + `そうび` のような部品hitから候補化します。
