# 新桃太郎伝説 vol015: bank85 handler table index confirmation

## 対象

- Target handler: `85:80B7`
- Raw PC offset: `0x0280B7`

## 結論

`85:80B7` は、bank85 mini-VM / handler dispatch table の **index `0x00`** に対応する handler です。

有効opcode換算では、dispatcher `85:8000` が入力Aから `0x50` を引いて table index にしているため、

```text
index = opcode - 0x50
85:80B7 = table[0]
opcode = 0x50
```

となります。

## 根拠1: dispatcher `85:8000`

`85:8000` は概ね以下の処理です。

```asm
85:8000  PHB
85:8001  PHK
85:8002  PLB
85:8003  REP #$30
85:8005  AND #$00FF
85:8008  SEC
85:8009  SBC #$0050
85:800C  BPL valid
85:800E  BRK #$EA       ; invalid opcode guard / debug trap candidate
85:8010  LDA #$0000     ; BRK return fallback candidate
valid:
85:8013  ASL A
85:8014  TAY
85:8015  LDA $8031,Y
85:8018  STA $06
85:801A  SEP #$30
85:801C  JSR $8021
85:801F  PLB
85:8020  RTL

85:8021  LDY #$01
85:8023  JMP ($0006)
```

このため、table base は `85:8031`、entry size は2バイト、index は `opcode - 0x50` です。

## 根拠2: table[0] が `85:80B7`

`85:8031` から始まる2バイトpointer tableの先頭は、

```text
85:8031  B7 80   -> 85:80B7
85:8033  C2 80   -> 85:80C2
85:8035  CD 80   -> 85:80CD
...
```

です。

したがって、

```text
opcode 0x50 / index 0x00 -> 85:80B7
opcode 0x51 / index 0x01 -> 85:80C2
opcode 0x52 / index 0x02 -> 85:80CD
```

という対応になります。

## `85:80B7` handler本体

```asm
85:80B7  LDA [$98],Y
85:80B9  TAX
85:80BA  JSR $9F4B
85:80BD  JSL $84:9BC5
85:80C1  RTS
```

意味は次の通りです。

```text
opcode 0x50
  -> stream operand を1byte読む
  -> operand を X = queue write index にする
  -> 85:9F4B で $1986 row から $1297/$129F queue を作る
  -> 84:9BC5 evaluator を起動
```

## 重要な補正

`85:80B7` は「任意のqueue builder呼び出し」ではなく、**bank85 handler table の opcode `0x50` handler** です。

これにより、直前まで追っていた token09 用queue準備は次のように整理できます。

```text
bank85 mini-VM opcode 0x50
  -> 85:80B7
  -> 85:9F4B
  -> $1986 row から queue pair 作成
  -> 84:9BC5
  -> C7 descriptor 評価
  -> token09
  -> 89:9EC7 queue pair pop
```

## 進捗更新

- Goal 7 武器特殊能力サブシステム: `97.5% -> 98%`
- Goal 9 script仕様書化: `81% -> 82%`

## 次に静的で攻める箇所

1. opcode `0x50` の stream operand が、どの値で渡されるかを C7/CB stream 上から列挙する。
2. `84:9BC5` の caller/contextを再確認し、`$1296` queue head 初期化位置を確定する。
3. `85:80B7 -> 9F4B` で作った queue が、直後の `84:9BC5 -> 9E10/token09` で何個消費されるかを静的に数える。
