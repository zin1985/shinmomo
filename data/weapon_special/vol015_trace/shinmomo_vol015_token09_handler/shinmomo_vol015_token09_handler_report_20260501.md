# 新桃太郎伝説 vol015: token 09 handler JMP/分岐先特定メモ

## 結論

`token 09` handler の分岐先は **`84:9F24`**。

ただし命令は `JMP` ではなく、`84:9EBA: F0 68` による **`BEQ $9F24`**。

```asm
84:9EB1  C9 02      CMP #$02
84:9EB3  D0 03      BNE $9EB8
84:9EB5  4C 34 9F   JMP $9F34      ; token 02

84:9EB8  C9 09      CMP #$09
84:9EBA  F0 68      BEQ $9F24      ; token 09

84:9EBC  C9 0A      CMP #$0A
84:9EBE  F0 1C      BEQ $9EDC
84:9EC0  C9 11      CMP #$11
84:9EC2  F0 59      BEQ $9F1D
84:9EC4  4C 32 9E   JMP $9E32
```

## token 09 handler 本体

```asm
84:9F24  20 C7 9E   JSR $9EC7
84:9F27  90 03      BCC $9F2C
84:9F29  4C 18 9E   JMP $9E18

84:9F2C  20 8D 9F   JSR $9F8D
84:9F2F  9C A9 12   STZ $12A9
84:9F32  80 0B      BRA $9F3F
```

## 9EC7 queue helper

```asm
84:9EC7  AE 96 12   LDX $1296
84:9ECA  BD 9F 12   LDA $129F,X
84:9ECD  D0 03      BNE $9ED2
84:9ECF  38         SEC
84:9ED0  80 06      BRA $9ED8

84:9ED2  48         PHA
84:9ED3  BD 97 12   LDA $1297,X
84:9ED6  FA         PLX
84:9ED7  18         CLC
84:9ED8  EE 96 12   INC $1296
84:9EDB  60         RTS
```

意味:

- `$1296` = queue head
- `$129F[head]` = type
- `$1297[head]` = value
- type が 0 なら `SEC`
- type が非0なら `A=value`, `X=type`, `CLC`

## 重要な認識更新

前回の「token 09 は直後1byte operandを読む direct execution」という見立ては撤回。

正しくは:

```text
token 09
  -> 84:9F24
  -> 84:9EC7 queue helper
  -> queue pair (value,type) を取り出す
  -> 84:9F8D で現在context退避
  -> 84:AE3A(value,type) でdirect-hit判定
  -> direct-hitしなければ C7:0000 の type別3byte root table から fallback family root を引く
  -> valueをordinalとして 9DBB でrecord skip
```

つまり token 09 は **stream直後のoperandを読む命令ではなく、事前に積まれたqueue pairを消費する命令**。

## token 02 との差

```text
token 02:
  streamから次byteを読む
  value = next - A0
  type = 01
  AE3A/fallbackへ

token 09:
  streamから追加byteを読まない
  queueから value/type をpop
  AE3A/fallbackへ
```

## Goal更新

- Goal 7 武器特殊能力サブシステム: 93% -> 94%
- Goal 9 script仕様書化: 73% -> 75%
- Goal 10 文字コード・表示系: 95% -> 96%
