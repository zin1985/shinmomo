# 新桃太郎伝説 Goal 13: `C1:90CE..90F6` depth reorder routine 完全分解
作成日: 2026-04-26

## 1. 結論

`C1:90CE..90F6` は、`$1591[X]` に保存された logical actor の visible object handle を使い、  
`$157D` と `$15E9,X` の縦位置差から sort key を作って `C0:AFEC` に渡す **logical actor depth reorder routine** と見てよい。

これにより、前回見えていた active chain の揺れはかなり説明できる。

```text
logical actor X
  -> $1591,X = visible object external handle
  -> sort key = f($157D - $15E9,X)
  -> $6A = handle
  -> JSL $80:AFEC
  -> physical slot = handle + 2
  -> $0A61/$0A1F linked list内で再配置
```

---

## 2. 重要な補正: handle と physical slot は2ずれる

今回の静的分解で、かなり大事な補正が入った。

`C0:AF33` は空き physical slot を `$0AA3[slot]` から探して linked list に挿入するが、  
最後に `DEX; DEX` してから object workを初期化し、`TXA` で戻る。

つまり、

```text
AF33 return handle = physical slot - 2
```

逆に `C0:AFEC` は、

```asm
LDX $6A
INX
INX
```

から始まるため、

```text
physical slot = external handle + 2
```

である。

したがって runtimeログで見えていた `s02` は、外部handle `00` に対応する。  
これまでの `s02/b25=22` は、静的には `$0B27 + handle0` に相当する。

```text
runtime physical slot s02
  = external handle 00
  = object work index 00
  = $0B27 / $0AE7 / $0E27 / $0BA7 / $0C67...
```

これは `$0A61` linked listと object work配列をつなぐ重要な補正。

---

## 3. `C1:90CE..90F6` 命令単位

| address | bytes | instruction | meaning |
|---|---|---|---|
| `address` | `bytes` | `instruction` | meaning |
| `C1:90CE` | `5A` | `PHY` | preserve Y |
| `C1:90CF` | `DA` | `PHX` | preserve X |
| `C1:90D0` | `A2 09` | `LDX #$09` | logical actor index loop starts at 9 |
| `C1:90D2` | `BC 91 15` | `LDY $1591,X` | load visible object handle for logical actor X |
| `C1:90D5` | `AD 7D 15` | `LDA $157D` | load leader/player current Y/depth candidate, slot0 of $157D array |
| `C1:90D8` | `38` | `SEC` | prepare subtraction |
| `C1:90D9` | `FD E9 15` | `SBC $15E9,X` | subtract actor X cached/base Y/depth |
| `C1:90DC` | `18` | `CLC` | prepare add |
| `C1:90DD` | `69 38` | `ADC #$38` | bias into person/depth sort key band |
| `C1:90DF` | `C9 30` | `CMP #$30` | lower threshold check |
| `C1:90E1` | `B0 02` | `BCS $90E5` | if computed >= 0x30 keep it for next threshold |
| `C1:90E3` | `A9 38` | `LDA #$38` | if computed < 0x30, force to middle/person band 0x38 |
| `C1:90E5` | `C9 40` | `CMP #$40` | upper threshold check |
| `C1:90E7` | `90 02` | `BCC $90EB` | if computed < 0x40 keep it |
| `C1:90E9` | `A9 48` | `LDA #$48` | if computed >= 0x40, force to high/front band 0x48 |
| `C1:90EB` | `84 6A` | `STY $6A` | pass object handle to AFEC; AFEC internally adds +2 to physical slot |
| `C1:90ED` | `22 EC AF 80` | `JSL $80:AFEC` | reorder existing object by new sort key in A |
| `C1:90F1` | `CA` | `DEX` | next logical actor |
| `C1:90F2` | `10 DE` | `BPL $90D2` | loop while X >= 0 |
| `C1:90F4` | `FA` | `PLX` | restore X |
| `C1:90F5` | `7A` | `PLY` | restore Y |
| `C1:90F6` | `60` | `RTS` | return |

---

## 4. sort key算出の正確な形

疑似コード:

```c
for (X = 9; X >= 0; X--) {
    Y = $1591[X];                 // external object handle
    A = $157D - $15E9[X] + 0x38;  // relative vertical/depth key

    if (A < 0x30) {
        A = 0x38;
    }

    if (A >= 0x40) {
        A = 0x48;
    }

    $6A = Y;                      // external handle
    AFEC(A);                      // reorder by sort key
}
```

注意点: これは単純な `clamp(0x38..0x48)` ではない。  
厳密には以下の区間写像。

| computed key | final key |
|---|---|
| `< 0x30` | `0x38` |
| `0x30..0x3F` | そのまま |
| `>= 0x40` | `0x48` |

したがって sort keyは、  
**相対Y差を0x38基準に変換しつつ、極端に後ろ/前のものを0x38/0x48へ寄せる描画深度キー** と見るのが安全。

---

## 5. `$157D` / `$15E9,X` の意味

`C1:9A79` 付近に以下がある。

```asm
LDA $1573,X
STA $15DF,X

LDA $157D,X
STA $15E9,X
```

これにより、

```text
$1573,X = current X/position-like array
$157D,X = current Y/depth-like array
$15DF,X = cached/base X
$15E9,X = cached/base Y/depth
```

と見るのが自然。

`C1:90CE` では `AD 7D 15`、つまり indexedではない `$157D` を使っている。  
これは `$157D,0`、つまり leader/player/current reference Y と見てよい。

```text
sort key = leader/reference Y - actor cached Y + 0x38
```

この結果を使って、同行者・logical actorの表示順を並び替えている可能性が高い。

---

## 6. `$1591,X` の意味

`C1:8E7B` で以下。

```asm
LDA #$38
JSL $80:AF33
STA $1591,X
TAY
```

`AF33` の戻り値は external object handle。  
したがって `$1591,X` は、

```text
logical actor X -> visible object external handle
```

の対応表。

このhandleは、そのまま object work indexとして使われるが、  
linked listのphysical slotへアクセスする時だけ `+2` される。

---

## 7. NPCログとの接続

はじまりの村ログでは、

```text
logical_1569 = 01 0D ...
active_chain = 15->03->02->04->...->01->FF
```

が見えていた。

今回の静的結果から、`$1569` 側のlogical actorは `$1591` 経由で visible object handleを持ち、  
`C1:90CE` が `$157D - $15E9,X` により sort keyを更新し、`AFEC` でactive chain上の位置を変えると読める。

つまり、

```text
$1569 logical actor
  -> $1591 handle
  -> physical slot = handle + 2
  -> $0A61 linked list
  -> OAM build
```

まで接続した。

---

## 8. Goal 13進捗

Goal 13は **98% -> 99%** に上げてよい。

理由:

- `$0A61` linked listの生成/削除/並べ替えが静的に見えた
- `AF33` 戻り値と runtime slotの `+2` 補正が確定寄り
- `$1591` が logical actor -> visible object handle表として説明できた
- `C1:90CE` が Y/depth差から active chain reorder keyを作る本命routineとして切れた

残り:

1. `$157D/$15E9` のゲーム内ラベルを完全確定する
2. `C1:90CE` が全移動NPC/同行者に対して毎フレーム呼ばれるかruntimeで確認
3. `$0B27` bit定義とB294 frame pieceの完全接続
4. `$0A1C` high OAM table処理まで完全仕様化

---

## 9. 次に攻める箇所

次は `C1:90CE` を呼ぶ上流と、`$157D/$15E9` の更新系を攻めるのがよい。

候補:

```text
C1:9A79  current position -> cached position snapshot
C1:936B  leader/current Yをactor slotへ転写
C1:8F40  logical actor visible object update main
C1:913D  actor state/direction helper
```

