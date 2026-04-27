# 新桃太郎伝説 `$195E` / `$180A+entity` setter追跡とROM修正可否メモ
作成日: 2026-04-25

## 1. `$195E` setter

### 結論
`$195E` は candidate `0x10..0x13` の処理済み/消費済みbitmaskとして使われる。

直接setterは以下。

```asm
C4:C86E  JSR $C880
C4:C871  BCC $C876
C4:C873  JMP $C366
C4:C876  LDA $84:C8F4,X
C4:C87A  TSB $195E
C4:C87D  JMP $C357
```

`C4:C880` は現在の `$1923/$1924` が candidate table に該当するか確認する小ルーチン。

```text
C4:C8F0 = 10 11 12 13
C4:C8F4 = 01 02 04 08
```

### 意味
- `$1924 == 1`
- `$1923` が `10/11/12/13` のいずれか
- 該当した index の bit を `$195E` に立てる

つまり、

```text
$195E |= candidate_bit[index]
```

と読める。

### 注意
`$195E` の直接 `STA/STZ` は見つからなかった。  
初期化は周辺WRAMブロック初期化、またはイベント/場面切替時の範囲クリアに含まれる可能性が高い。

---

## 2. `$180A + entity` setter / clear / test

### 結論
`$8586AC` condition evaluator の condition `0x38 / 0x39 / 0x3A` が三兄弟になっている。

| condition id | handler | 役割 |
|---:|---|---|
| `0x38` | `C5:8964` | `$180A[entity-1] |= $1E` |
| `0x39` | `C5:8973` | `$180A[entity-1] &= ~$1E` |
| `0x3A` | `C5:8952` | `($180A[entity-1] & $1E) == 0` を判定 |

`C4:C8AA` では、

```asm
LDA #$80
STA $1E
LDA #$3A
JSL $85:86AC
```

なので、

```text
$180A[entity-1] bit7 が clear なら採用
```

となる。

### handler概要

#### condition 0x38: set
```asm
C5:8964  LDX #$01E7
C5:8967  JSR $89E2
C5:896A  LDA $1623,X
C5:896D  ORA $1E
C5:896F  STA $1623,X
C5:8972  RTS
```

#### condition 0x39: clear
```asm
C5:8973  LDX #$01E7
C5:8976  JSR $89E2
C5:8979  LDA $1E
C5:897B  EOR #$FF
C5:897D  AND $1623,X
C5:8980  STA $1623,X
C5:8983  RTS
```

#### condition 0x3A: test clear
```asm
C5:8952  LDX #$01E7
C5:8955  JSR $89E2
C5:8958  LDA $1623,X
C5:895B  BIT $1E
C5:895D  BEQ carry_set
C5:895F  CLC
C5:8962  SEC
C5:8963  RTS
```

`C5:89E2` により、`X = 0x01E7 + ($1620 - 1)` へ変換されるため、実体は `$180A + (entity - 1)`。

---

## 3. condition 0x38/0x39/0x3A の直接呼び出し候補

### 0x38 set 呼び出し
| caller | 内容候補 |
|---|---|
| `C2:B74F` | entity flag bit set |
| `C2:CD18` | entity flag bit set |

### 0x39 clear 呼び出し
| caller | 内容候補 |
|---|---|
| `C1:A665` | entity flag bit clear |
| `C1:A8E8` | entity flag bit clear |
| `C2:B741` | entity flag bit clear |

### 0x3A test 呼び出し
| caller | 内容候補 |
|---|---|
| `C0:DB9E` | entity flag test |
| `C1:8DAE` | entity flag test |
| `C1:B8BE` | entity flag test |
| `C3:A535` | entity flag test |
| `C3:A5C8` | entity flag test |
| `C3:BD90` | entity flag test |
| `C4:C8DD` | C4:C8AA candidate feeder内の表示/採用判定 |

---

## 4. C4:C8AA と C1:9474 の軽減構造

現時点で見えている多段フィルタは以下。

```text
C4:C8AA
  candidate 0x10..0x13 の4本だけ走査
  $195E bitmaskで既処理candidateを除外
  $80DA57で実entityへ解決
  entity >= 0x15 を除外
  $180A[entity-1] bit7 set を除外
  $1958へ出力

C4:C85D
  $1958を C1:944B へ渡す

C1:9474
  通常actor ID < 0x17 は slot0..3 に制限
  全logical objectは slot0..9 に制限

OAM builder
  object単位skip
  piece単位clip
  OAM残枠不足なら描画抑制
```

---

## 5. ROM修正可否

### 可能
IPSパッチ形式なら作成可能。  
ただし、現時点で安全に提案できるのは **実験用のcap変更** まで。

### 危険
以下はまだ危険。

- candidate table `10 11 12 13` を増やす
  - 直後に別コードが続くため、単純拡張スペースがない
  - `$195E` bitmaskは8bitだが、candidate keyの意味辞書が未確定
- OAM builderのclip条件変更
  - sprite破綻、OAM overflow、副作用が大きい
- `$180A bit7` 判定の無効化
  - 表示不可/処理済み/イベント状態の区別を壊す可能性がある

### 実験用パッチ案

#### A. 処理軽減テスト: 通常actor cap 4 -> 3
- `C1:9492 CPX #$04` の immediate を `03` へ
- `C1:94A9 CPX #$04` の immediate を `03` へ

効果:
- 通常actorを最大3体に制限
- 表示負荷は下がる可能性
- ただしNPC/同行者表示が減る

#### B. 表示増加テスト: 通常actor cap 4 -> 6
- `C1:9492 CPX #$04` の immediate を `06` へ
- `C1:94A9 CPX #$04` の immediate を `06` へ

効果:
- 通常actorを最大6体まで logical list に許容
- 画面上のNPCが増える可能性
- ただし処理負荷/OAM負荷は上がる可能性

---

## 6. 推奨

現時点で「処理改善」を目的にROMへ入れるなら、まずは **A. cap 4 -> 3** のIPSを別名ROMに当てて比較するのが安全。

「大量表示を増やせるか」を目的にするなら、**B. cap 4 -> 6** を実験する。ただしこれは軽減ではなく表示増加方向なので、負荷改善とは逆向きになる可能性がある。

本命の最適化は、まだ以下を確定してから。

1. `$195E` の初期化タイミング
2. `$180A bit7` の実ラベル
3. `C4:C357/C4:C366` の成功/失敗戻り
4. `$80DA57` が解決する candidate key `0x10..0x13` の実体
