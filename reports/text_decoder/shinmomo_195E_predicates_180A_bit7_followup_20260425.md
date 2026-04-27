# 新桃太郎伝説 `$195E` 周辺predicate / `$180A bit7` ラベル再整理  
作成日: 2026-04-25

## 1. 今回の目的

前回までに、`C4:C8AA` が candidate `0x10..0x13` を走査し、`$1958` に次のspawn候補entityを入れる feeder だと整理した。

今回は続きとして、

- `$195E` の setter / tester / all-done 判定
- `$180A + entity` bit7 の実ラベル
- `C4:C357 / C4:C366` の成功/失敗出口
- 現時点でROM修正できそうな安全度

を静的に整理した。

---

## 2. `$195E` の三点セット

### 2-1. `C4:C86E` = candidate消費済みset

```asm
C4:C86E  JSR $C880
C4:C871  BCC $C876
C4:C873  JMP $C366
C4:C876  LDA $84:C8F4,X
C4:C87A  TSB $195E
C4:C87D  JMP $C357
```

意味:

```text
現在の ($1923,$1924) が candidate 10..13 / type 1 に該当するなら
$195E に該当bitを立てて成功
```

### 2-2. `C4:C8F8` = candidate未消費チェック

```asm
C4:C8F8  LDA $1924
C4:C8FB  CMP #$01
C4:C8FD  BEQ $C902
C4:C8FF  JMP $C91E   ; success

C4:C902  LDX #$00
loop:
C4:C904  LDA $84:C8F0,X
C4:C908  CMP $1923
C4:C90B  BNE next
C4:C90D  LDA $84:C8F4,X
C4:C911  BIT $195E
C4:C914  BEQ $C919
C4:C916  JMP $C366   ; already consumed -> failure
next:
C4:C919  INX
C4:C91A  CPX #$04
C4:C91C  BCC loop
C4:C91E  JMP $C357   ; unconsumed or non-candidate -> success
```

意味:

```text
candidate typeで、かつ該当bitが立っているなら失敗。
それ以外は成功。
```

これは **「このcandidateはまだ使えるか？」 predicate** と見てよい。

### 2-3. `C4:C89B` = all candidates consumed check

```asm
C4:C89B  LDA $195E
C4:C89E  AND #$0F
C4:C8A0  CMP #$0F
C4:C8A2  BEQ $C8A7
C4:C8A4  JMP $C366
C4:C8A7  JMP $C357
```

意味:

```text
candidate 10..13 の4bitがすべて立っていれば成功
```

つまり `$195E` は単なる状態flagではなく、candidate群の消費進捗として使われている。

---

## 3. `$180A + entity` bit7 の実ラベル

`$8586AC` condition `0x38/0x39/0x3A` により、`$180A + (entity-1)` のbit操作が行われる。

| condition | 役割 | handler |
|---:|---|---|
| `0x38` | set bits | `C5:8964` |
| `0x39` | clear bits | `C5:8973` |
| `0x3A` | test clear | `C5:8952` |

`C4:C8AA` では `$1E=0x80`、condition `0x3A` なので、

```text
$180A[entity-1] bit7 == 0 なら candidate 採用
```

と読める。

### 3-1. bit7のラベル候補

bit7は以下のような文脈で使われる。

| caller | 文脈 | 解釈 |
|---|---|---|
| `C4:C8AA` | candidate feeder | bit7 clear のentityだけspawn候補 |
| `C1:8DAE` | `$1569`内の通常actorを数える | bit7 clear の通常actorを「有効表示対象」と数える |
| `C1:B8BE` | `$1569[0..3]` から候補選択 | bit7 clear の通常actorを返す |
| `C3:BD90` | 通常actorの座標/表示候補 | bit7 clear の通常actorだけ対象 |
| `C3:A535/A5C8` | event/dialogue候補 | bit7 clearで追加処理へ進む |

したがって bit7 は以下のどれかが濃い。

```text
候補A: entity hidden / unavailable flag
候補B: already handled / suppressed flag
候補C: event-side non-display / inactive flag
```

現時点では、表示系文脈では **hidden/suppressed flag** と呼ぶのが安全。

---

## 4. `C4:C357 / C4:C366` の意味

### success

```asm
C4:C357  LDA #$01
C4:C359  STA $1957
C4:C35C  CLC
C4:C35D  RTS
```

### failure

```asm
C4:C366  LDA #$01
C4:C368  STZ $1957
C4:C36B  CLC
C4:C36C  RTS
```

`C4:C357` は `$1957 = 1`、`C4:C366` は `$1957 = 0` を返すだけ。  
Carry はどちらもclear。

つまり、C4系script commandの成功/失敗は **Carryではなく `$1957` に返る**。

これはscript側のpredicate command群の標準戻り値と見てよい。

---

## 5. ROM修正の検討

### 5-1. 現時点で比較的安全な実験

#### 通常actor cap変更

`C1:9474` の `<0x17` 通常actor capを変える修正は、処理対象が限定されているため比較的試しやすい。

| 変更 | 効果 | 安全度 |
|---|---|---:|
| cap 4 -> 3 | 表示/処理軽減テスト | 中 |
| cap 4 -> 6 | 表示増加テスト | 低〜中 |

既にIPSとして出力済み。

### 5-2. 新しく見えた実験候補

#### candidate scan 4 -> 2

`C4:C8AA` の candidate走査対象を `0x10/0x11` の2本だけにする。

必要変更候補:

| file offset | 旧 | 新 | 目的 |
|---:|---:|---:|---|
| `0x04C894` | `04` | `02` | `C4:C880` candidate match loop |
| `0x04C8A1` | `0F` | `03` | all-done mask `0x0F -> 0x03` |
| `0x04C8EA` | `04` | `02` | `C4:C8AA` feeder loop |
| `0x04C91B` | `04` | `02` | `C4:C8F8` unconsumed check loop |

ただしこれは、candidate `0x12/0x13` を無視するため挙動破壊の可能性がある。  
処理軽減テスト用としては作れるが、安全度は低い。

### 5-3. まだ危険な修正

| 修正 | 危険理由 |
|---|---|
| `$180A bit7` test無効化 | hidden/suppressed状態のentityを出してしまう |
| OAM clipping緩和 | OAM overflow / sprite破綻の可能性 |
| candidate table拡張 | table直後に別コードがあり、スペース不足 |
| `$195E` 初期化変更 | event進行やcandidate再出現に影響する可能性 |

---

## 6. Goal 13 進捗

今回、前段のpredicate群がほぼつながった。

```text
candidate key 10..13
  -> $195Eで消費済み管理
  -> $80DA57でentity解決
  -> $180A bit7でhidden/suppressed除外
  -> $1958
  -> C1:9474
  -> $1569
  -> OAM builder
```

Goal 13 は **95% -> 96%** としてよい。

残りは以下。

1. `$180A bit7` のゲーム内ラベル確定  
2. `$195E` の初期化タイミング確定  
3. `candidate 0x10..0x13` のゲーム内実体ラベル確定  
4. 実機/エミュレータでcap変更時の挙動確認  

