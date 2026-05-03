# bank87 `$0759/$0799` object slot再分類（2026-05-03）

## 結論

`$0759/$0799` は全object共通のpointer low/highではない。
object type / routine依存で意味が変わる汎用slot fieldとして扱う。

## 実スキャン結果

CSV:

- `data/csv/bank87_0759_0799_xrefs_vol017.csv`

bank87内で検出した主なpattern:

```text
STA $0759,X / STA $0799,X
LDA $0759,X / LDA $0799,X
DEC/INC/STZ $0799,X
```

## 重要コンテキスト

### `$87:82C0` reader候補

```text
BD 59 07 85 2A  BD 99 07 85 2B
```

`$0759/$0799` を `$2A/$2B` に移し、後段で `($2A),Y` 参照する候補。

### `$87:8459` state toggle

```text
LDA $0759,X
INC A
AND #$01
STA $0759,X
```

pointerではなく0/1 phase/state。

### `$87:E579` position/velocity風

```text
$0719 += $0799
$0759 += $07D9
```

pointerではなく位置・速度系。

## 補正

これにより、以前の「0x39850 row末尾word -> $0759/$0799へ直接設定」という仮説は弱まった。
`F09A/F0DB` はslot pointer値ではなく、evaluator/interpreterがその場で読むblob label寄り。
