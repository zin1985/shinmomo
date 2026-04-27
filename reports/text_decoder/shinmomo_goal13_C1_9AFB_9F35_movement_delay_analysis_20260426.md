# 新桃太郎伝説 Goal 13: `C1:9AFB` / `C1:9F35` と `$15FD/$15D5` の確定
作成日: 2026-04-26

## 1. 結論

`$15FD/$15D5` は、どちらも logical actor の移動・表示更新に関係するが、役割が違う。

| field | ラベル | 意味 |
|---|---|---|
| `$15FD,X` | `actor_state_dispatch_delay` | state/animation selector dispatchの遅延カウンタ。非0の間、`C1:9AFB` のjump table dispatchを抑制する |
| `$15D5,X` | `actor_movement_projection_step_count` | movement/projection step count。`C1:9F35` がこの回数だけ投影・screen更新を回す。`C1:9F18` で `$15FD` の遅延値にも変換される |

つまり、

```text
$15D5 = movement/projectionを何段階・何回ぶん適用するか
$15FD = 次のstate/animation dispatchまで待つカウント
```

という分担。

前回の「pending系」という見立ては半分正しいが、より正確には、

```text
$15D5: movement projection step count
$15FD: state dispatch delay / cooldown
```

とするのがよい。

---

## 2. 更新pipeline全体

`C1:9AF1` は、logical actor X の1回ぶん更新として以下を呼ぶ。

```asm
C1:9AF1  JSR $9AFB   ; state/animation dispatch gate
C1:9AF4  JSR $9F35   ; movement/projection apply loop
C1:9AF7  JSR $9031   ; normal visible-object update continuation
```

したがって順序は、

```text
state/animationを決める
  -> movement projectionをscreen/object workへ適用
  -> visible object通常更新
```

となる。

---

## 3. `C1:9AFB`: state dispatch delay + selector jump table

`C1:9AFB` は `$15FD,X` を最初に見る。

```asm
LDA $15FD,X
BEQ evaluate_state
DEC $15FD,X
BRA return
```

つまり `$15FD,X` が非0なら、1減らして state dispatch をスキップする。  
これが `actor_state_dispatch_delay` と見る最大の根拠。

`$15FD` が0の場合、`C1:9B33` でdispatch可否を評価し、必要なら `C1:913D` から表示状態selectorを得る。

selectorは最大 `0x1A` に丸められ、`C1:9B6F` のjump tableへ入る。

```text
selector -> handler
```

このhandler群が `$15D5`, `$15FD`, `$15F3`, `$1573/$157D/$15DF/$15E9` などを更新し、移動・向き・アニメ状態を作る。

---

## 4. `C1:9B33` helperの戻り

`C1:9B33` は、state dispatchをどうするかを返すgate helper。

| condition | return | 意味 |
|---|---|---|
| condition | return | meaning |
| X == 0 | A=00, CLC | leader/reference actor uses selector0 path; no forced C1:913D |
| $0307 bit40 clear | A=00, CLC | state dispatch not forced when global display flag not active |
| $DE bit18 set | A=FF, CLC | suppress dispatch this frame |
| $0309 != 0 | SEC | force C1:913D selector |
| ($DE & 04) OR $1563 OR $1543 OR $160C OR $1562 != 0 | A=00, CLC | use selector0/default path under blocking/global modes |
| ($1587,X & 40) OR $1268 != 0 | A=FF, CLC | suppress dispatch under actor/global lock flag |
| otherwise | SEC | force C1:913D selector |

戻りの解釈:

```text
Carry set:
  C1:913D display-state selectorを取り直す

Carry clear + A>=0:
  Aをそのままselectorとして使う。主に selector 0

Carry clear + A<0:
  dispatchを完全に抑制してreturn。主に A=FF
```

---

## 5. `C1:9B6F` selector jump table

`C1:9AFB` はselectorを2倍し、`C1:9B6F` からhandler pointerを読む。

| selector | handler | rough role |
|---:|---|---|
| `selector` | `handler` | rough_role |
| `00` | `C1:9BB1` | set $15D5 from $1511 then snapshot coords |
| `01` | `C1:9BB1` | same as selector 00 |
| `02` | `C1:9BC7` | random/direction movement path |
| `03` | `C1:9C02` | directed movement/path update |
| `04` | `C1:9C0F` | input/global movement flag path |
| `05` | `C1:9BE0` | common movement toward target/check path |
| `06` | `C1:9BE0` | common movement path |
| `07` | `C1:9BE0` | common movement path |
| `08` | `C1:9BE0` | common movement path |
| `09` | `C1:9BE0` | common movement path |
| `0A` | `C1:9BE0` | common movement path |
| `0B` | `C1:9CB2` | special random/idle path, sets $15FD=40 |
| `0C` | `C1:9BE0` | common movement path |
| `0D` | `C1:9CC8` | directed path with $9E22 then common target check |
| `0E` | `C1:9CD6` | state-specific compare current/cache coords |
| `0F` | `C1:9CFF` | state-specific animation direction update |
| `10` | `C1:9D16` | state-specific animation direction update |
| `11` | `C1:9D26` | selector 06 path |
| `12` | `C1:9BE0` | common movement path |
| `13` | `C1:9D2B` | distance/random direction path |
| `14` | `C1:9D70` | selector = X then directed path |
| `15` | `C1:9BA5` | clear $15D5 |
| `16` | `C1:9BA5` | clear $15D5 |
| `17` | `C1:9BE0` | common movement path |
| `18` | `C1:9D74` | random/path special path |
| `19` | `C1:9D88` | distance/approach special path |
| `1A` | `C1:9BA9` | set $15D5 from $1559 then snapshot coords |

重要setter:

```asm
C1:9BA5  STZ $15D5,X
C1:9BA9  LDA $1559 ; STA $15D5,X
C1:9BB1  LDA $1511 ; STA $15D5,X
C1:9BFE  LDA #$05 ; STA $15FD,X
C1:9CC4  LDA #$40 ; STA $15FD,X
C1:9F18  LDA table[$15D5,X] ; STA $15FD,X
```

これにより、`$15D5` は移動/projection step count、`$15FD` はそれに応じたdispatch delay/cooldownとして働く。

---

## 6. `C1:9F18` delay table

`C1:9F18` は `$15D5,X` をYにして、`C1:9F24` tableから `$15FD,X` を設定する。

table bytes:

```text
index: 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F
value: 0F 0F 07 07 03 03 03 03 01 01 01 01 01 01 01 01
```

意味:

```text
大きいmovement step countほど短いdispatch delay
小さいmovement step countほど長いdispatch delay
```

と読める。

おそらく移動距離/速度/歩行状態に応じて、次のstate dispatchまでの待ちを調整する仕組み。

---

## 7. `C1:9F35`: movement/projection apply loop

`C1:9F35` は `$15D5,X` または global `$00DF` を回数として、screen projectionとobject work更新を繰り返す。

擬似コード:

```c
count = $00DF;
if (count == 0) {
    count = $15D5[X];
    if (count == 0) return;
}

$0C = count;

do {
    JSL $81:9F78;   // project map/depth coords to $030B/$030D
    JSR $A080;      // apply projected coords and compute deltas $0311/$0312

    if (($0311 | $0312) == 0) break;

    if ($0311 != 0) JSL $80:BBEC;
    if ($0312 != 0) JSL $80:BC21;

    if ($1551 & 0x0F) JSL $80:AF0C;

    $0C--;
} while ($0C != 0);
```

重要なのは、`C1:9F35` 自体は `$15D5,X` を直接減らしていない点。  
`$15D5` は「この更新で何回ぶんprojection/apply loopを回すか」のper-actor設定値として使われる。

---

## 8. `C1:9F35` 命令単位

| address | bytes | instruction | meaning |
|---|---|---|---|
| `address` | `bytes` | `instruction` | meaning |
| `C1:9F35` | `8B DA 4B AB` | `PHB; PHX; PHK; PLB` | set DBR=C1, preserve X |
| `C1:9F39` | `AD DF 00` | `LDA $00DF` | load global projection/movement step override |
| `C1:9F3C` | `D0 05` | `BNE $9F43` | if nonzero use global count |
| `C1:9F3E` | `BD D5 15` | `LDA $15D5,X` | else load per-actor movement/projection step count |
| `C1:9F41` | `F0 32` | `BEQ $9F75` | if zero, no projection work |
| `C1:9F43` | `85 0C` | `STA $0C` | local loop counter |
| `C1:9F45` | `22 78 9F 81` | `JSL $81:9F78` | project map/depth coords to screen coords $030B/$030D |
| `C1:9F49` | `20 80 A0` | `JSR $A080` | apply projected coords to current visible object and compute deltas $0311/$0312 |
| `C1:9F4C` | `AD 11 03 / 0D 12 03` | `LDA $0311; ORA $0312` | check if projected screen coord changed |
| `C1:9F52` | `F0 21` | `BEQ $9F75` | if no delta, finish |
| `C1:9F54` | `AD 11 03` | `LDA $0311` | horizontal delta flag/value |
| `C1:9F59` | `22 EC BB 80` | `JSL $80:BBEC` | apply horizontal/related visible-object update if X delta exists |
| `C1:9F5D` | `AD 12 03` | `LDA $0312` | vertical delta flag/value |
| `C1:9F62` | `22 21 BC 80` | `JSL $80:BC21` | apply vertical/related visible-object update if Y delta exists |
| `C1:9F66` | `AD 51 15 / 89 0F` | `LDA $1551; BIT #0F` | check low-nibble movement/camera/party flags |
| `C1:9F6D` | `22 0C AF 80` | `JSL $80:AF0C` | additional object update when $1551 low bits present |
| `C1:9F71` | `C6 0C` | `DEC $0C` | decrement local loop counter |
| `C1:9F73` | `D0 D4` | `BNE $9F49` | repeat apply/update loop |
| `C1:9F75` | `FA AB 60` | `PLX; PLB; RTS` | return |

---

## 9. setter / reference一覧

| field | address | op | source | meaning |
|---|---|---|---|---|
| `field` | `address` | operation | source | meaning |
| `$15FD,X` | `C1:9A8B` | STZ | C1:9A79 snapshot reset | clear state dispatch delay when current coords are snapshotted |
| `$15FD,X` | `C1:9B03` | DEC | C1:9AFB | count down state dispatch delay; while nonzero, skip state dispatch |
| `$15FD,X` | `C1:9BFE` | STA #05 | movement target blocked path | short delay after failed/blocked movement target |
| `$15FD,X` | `C1:9CC4` | STA #40 | special idle/random path | long delay/cooldown |
| `$15FD,X` | `C1:9F1F` | STA table[$15D5,X] | C1:9F18 delay table | derive animation/state delay from movement step count |
| `$15D5,X` | `C1:9A8E` | STZ | C1:9A79 snapshot reset | clear movement/projection step count on coordinate snapshot |
| `$15D5,X` | `C1:9BA5` | STZ | selector 15/16 handler | clear movement/projection step count |
| `$15D5,X` | `C1:9BAC` | STA $1559 | selector 1A handler | load movement/projection step count from global/actor parameter $1559 |
| `$15D5,X` | `C1:9BB4` | STA $1511 | selector 00/01 handler | load movement/projection step count from global/actor parameter $1511 |
| `$15D5,X` | `C1:9DD8` | STA A/$1559 | helper $9DD5/$9DD8 | set movement/projection step count, often before/after path update |
| `$15D5,X` | `C1:9F3E` | LDA | C1:9F35 | used as local loop count for projection/application work |

---

## 10. `$15FD/$15D5` の最終ラベル

| field | final label | meaning | confidence |
|---|---|---|---|
| `field` | `final_label` | meaning | confidence |
| `$15FD,X` | `actor_state_dispatch_delay` | per logical actor countdown that suppresses C1:9AFB selector dispatch while nonzero; also feeds animation/state delay behavior | high |
| `$15D5,X` | `actor_movement_projection_step_count` | per logical actor movement/projection loop count used by C1:9F35; also used by C1:9F18 to derive $15FD delay | high |
| `$00DF` | `global_projection_step_override` | if nonzero, C1:9F35 uses this instead of $15D5,X as loop count | medium-high |
| `$15F3,X` | `actor_direction_or_motion_pattern` | direction/pattern value set by several jump handlers and helpers | medium-high |
| `$1609/$160A` | `subtile_projection_offset_x/y` | projection offset added before screen coordinate conversion | medium-high |
| `$0311/$0312` | `projected_screen_delta_flags` | set by C1:A080 family when object screen position changed; gates $80BBEC/$80BC21 | medium-high |

---

## 11. Goal 13への反映

Goal 13は **99%据え置き**。

今回で、movement補間・pending系の主な未解決点だった `$15FD/$15D5` はかなり確定した。

ただし100%にしない理由:

1. `$15F3,X` の direction / motion pattern 体系がまだ完全ではない
2. `$1559/$1511` が具体的に何の速度・step countか未分類
3. `$00DF` global overrideがどの場面で入るか未確定
4. `$80:BBEC/$80:BC21/$80:AF0C` がscreen/object updateにどう効くか未分解
5. `C1:9F35` のloopが `$15D5` を直接減らさないため、外部でのライフサイクル確認が必要

---

## 12. 次に攻める箇所

1. `$15F3,X` のdirection/motion pattern体系  
   - `C1:9E9A / C1:9EAD / C1:9ED9 / C1:9F18` を切る
2. `$1559/$1511` のsetter追跡  
   - movement step countの元値を確定
3. `$80:BBEC / $80:BC21 / $80:AF0C` を分解  
   - projected screen deltaがobject work/OAMへどう伝播するか確認
4. `$00DF` setter追跡  
   - global projection step overrideの用途を確定

