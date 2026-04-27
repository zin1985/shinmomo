# 新桃太郎伝説 Goal 13: `$15F3` direction/motion pattern体系と `C1:9E9A / 9EAD / 9ED9 / 9F18`
作成日: 2026-04-26

## 1. 結論

`$15F3,X` は単なる向きではなく、**logical actor の movement direction / motion pattern selector** と見るのが正しい。

最終ラベル:

```text
$15F3,X = actor_motion_direction_pattern
```

体系としては以下。

```text
state handler
  -> A または $15F3 に direction/motion pattern を持つ
  -> C1:9ED9 で $15DF/$15E9 + delta table から候補座標 $030B/$030D を生成
  -> C1:9EAD で候補座標の移動可否をprobe
  -> C1:9E9A で採用方向を $15F3 に保存し、候補座標を $15DF/$15E9 render cacheへcommit
  -> C1:9F18 で $15D5 から $15FD delayを作る
  -> C1:9F35 で render cache をscreen/object workへ投影する
```

---

## 2. `C1:9ED9`: candidate next coordinate generator

`C1:9ED9` は、Aに入ったdirection/motion patternを2倍し、`$81:81D3/$81:81D4` のdelta tableを引いて候補座標を作る。

### 命令単位

| address | bytes | instruction | meaning |
|---|---|---|---|
| `address` | `bytes` | `instruction` | meaning |
| `C1:9ED9` | `5A` | `PHY` | preserve Y |
| `C1:9EDA` | `DA` | `PHX` | preserve X = logical actor index |
| `C1:9EDB` | `0A` | `ASL A` | direction/motion pattern * 2 for delta table |
| `C1:9EDC` | `DA` | `PHX` | push original X again |
| `C1:9EDD` | `7A` | `PLY` | Y = original logical actor index |
| `C1:9EDE` | `AA` | `TAX` | X = direction/motion pattern table offset |
| `C1:9EDF` | `B9 DF 15` | `LDA $15DF,Y` | base render_cache_map_x |
| `C1:9EE2` | `18` | `CLC` | prepare add |
| `C1:9EE3` | `7F D3 81 81` | `ADC $81:81D3,X` | add signed/relative X delta from movement delta table |
| `C1:9EE7` | `8D 0B 03` | `STA $030B` | candidate projected/map X low/current work |
| `C1:9EEA` | `8D 13 03` | `STA $0313` | duplicate candidate X for later helper |
| `C1:9EED` | `B9 E9 15` | `LDA $15E9,Y` | base render_cache_map_y_depth |
| `C1:9EF0` | `18` | `CLC` | prepare add |
| `C1:9EF1` | `7F D4 81 81` | `ADC $81:81D4,X` | add signed/relative Y/depth delta from movement delta table |
| `C1:9EF5` | `8D 0D 03` | `STA $030D` | candidate projected/map Y/depth current work |
| `C1:9EF8` | `8D 14 03` | `STA $0314` | duplicate candidate Y/depth for later helper |
| `C1:9EFB` | `FA` | `PLX` | restore X |
| `C1:9EFC` | `7A` | `PLY` | restore Y |
| `C1:9EFD` | `60` | `RTS` | return |

### 重要点

`C1:9ED9` の出力:

```text
$030B = candidate_next_map_x
$0313 = candidate_next_map_x duplicate
$030D = candidate_next_map_y_depth
$0314 = candidate_next_map_y_depth duplicate
```

入力:

```text
A = direction/motion pattern
X = logical actor index
base = $15DF,X / $15E9,X render cache coordinate
delta = $81:81D3/$81:81D4 table
```

`$15F3` 自体を直接読まないが、多くのcallerは `LDA $15F3,X; JSR $9ED9` の形で使う。  
つまり `C1:9ED9` は **pattern -> next coordinate** 変換器。

---

## 3. `C1:9EAD`: movement candidate validity probe

`C1:9EAD` は `C1:9ED9` で候補座標を作った後、6つのhelperで移動可否を判定する。

### 命令単位

| address | bytes | instruction | meaning |
|---|---|---|---|
| `address` | `bytes` | `instruction` | meaning |
| `C1:9EAD` | `20 D9 9E` | `JSR $9ED9` | compute candidate next coords into $030B/$030D and $0313/$0314 |
| `C1:9EB0` | `22 DD 81 81` | `JSL $81:81DD` | movement/collision/terrain probe #1 |
| `C1:9EB4` | `B0 21` | `BCS blocked` | if helper reports carry set, return CLC = blocked |
| `C1:9EB6` | `22 32 B2 81` | `JSL $81:B232` | movement/collision/terrain probe #2 |
| `C1:9EBA` | `B0 1B` | `BCS blocked` | if carry set, blocked |
| `C1:9EBC` | `22 4F B1 81` | `JSL $81:B14F` | movement/collision/terrain probe #3 |
| `C1:9EC0` | `B0 15` | `BCS blocked` | if carry set, blocked |
| `C1:9EC2` | `22 C4 A0 81` | `JSL $81:A0C4` | movement/collision/terrain probe #4 |
| `C1:9EC6` | `B0 0F` | `BCS blocked` | if carry set, blocked |
| `C1:9EC8` | `22 0E BA 81` | `JSL $81:BA0E` | movement/collision/terrain probe #5 |
| `C1:9ECC` | `B0 09` | `BCS blocked` | if carry set, blocked |
| `C1:9ECE` | `22 8E B6 81` | `JSL $81:B68E` | movement/collision/terrain probe #6 |
| `C1:9ED2` | `B0 03` | `BCS blocked` | if carry set, blocked |
| `C1:9ED4` | `38` | `SEC` | all probes clear: movement candidate allowed |
| `C1:9ED5` | `80 01` | `BRA return` | skip blocked return |
| `C1:9ED7` | `18` | `CLC` | blocked / invalid movement candidate |
| `C1:9ED8` | `60` | `RTS` | return carry = allowed flag |

### Carry意味

`C1:9EAD` の戻りCarryは以下。

| Carry | 意味 |
|---|---|
| `SEC` | candidate allowed / clear |
| `CLC` | candidate blocked / invalid |

根拠:

各helperがCarry setを返した場合、`C1:9EAD` は `CLC` で返る。  
全helperを通過した場合だけ `SEC` で返る。

つまりhelper側のCarry setは「何かに引っかかった」を示す。

### helper候補

| helper | 仮ラベル |
|---|---|
| `$81:81DD` | map/passability/collision probe #1 |
| `$81:B232` | map/passability/collision probe #2 |
| `$81:B14F` | map/passability/collision probe #3 |
| `$81:A0C4` | object/event collision probe #4 |
| `$81:BA0E` | terrain/event boundary probe #5 |
| `$81:B68E` | actor/NPC/blocking probe #6 |

正確な個別意味は未確定だが、全体として **candidate movement feasibility check** と見てよい。

---

## 4. `C1:9E9A`: commit selected direction and target cache

`C1:9E9A` は、採用したdirection/motion patternを `$15F3,X` に保存し、そのpatternで計算した候補座標を `$15DF/$15E9` にcommitする。

### 命令単位

| address | bytes | instruction | meaning |
|---|---|---|---|
| `address` | `bytes` | `instruction` | meaning |
| `C1:9E9A` | `9D F3 15` | `STA $15F3,X` | store selected direction/motion pattern for logical actor X |
| `C1:9E9D` | `20 D9 9E` | `JSR $9ED9` | compute candidate next map/depth coordinate from pattern A/$15F3-like direction |
| `C1:9EA0` | `AD 0B 03` | `LDA $030B` | load candidate X/column |
| `C1:9EA3` | `9D DF 15` | `STA $15DF,X` | commit candidate X to render_cache_map_x |
| `C1:9EA6` | `AD 0D 03` | `LDA $030D` | load candidate Y/depth row |
| `C1:9EA9` | `9D E9 15` | `STA $15E9,X` | commit candidate Y/depth to render_cache_map_y_depth |
| `C1:9EAC` | `60` | `RTS` | return |

### 意味

```c
$15F3[X] = selected_pattern;
candidate = make_candidate_from_pattern(selected_pattern);
$15DF[X] = candidate.x;
$15E9[X] = candidate.y_depth;
```

これにより、`$15DF/$15E9` の render cache target が1step先へ進む。  
その後、`C1:9F35` がこのrender cacheをscreen coordinateへ投影してvisible objectへ反映する。

---

## 5. `C1:9F18`: step count -> dispatch delay

`C1:9F18` は `$15D5,X` をindexにして、delay tableから `$15FD,X` を設定する。

### 命令単位

| address | bytes | instruction | meaning |
|---|---|---|---|
| `address` | `bytes` | `instruction` | meaning |
| `C1:9F18` | `5A` | `PHY` | preserve Y |
| `C1:9F19` | `BC D5 15` | `LDY $15D5,X` | Y = actor_movement_projection_step_count |
| `C1:9F1C` | `B9 24 9F` | `LDA $9F24,Y` | read delay value from step-count-to-delay table |
| `C1:9F1F` | `9D FD 15` | `STA $15FD,X` | set actor_state_dispatch_delay |
| `C1:9F22` | `7A` | `PLY` | restore Y |
| `C1:9F23` | `60` | `RTS` | return |

### delay table

| `$15D5` | `$15FD` delay | interpretation |
|---:|---:|---|
| `index_15D5` | `delay_15FD` | interpretation |
| `00` | `0F` | long delay for zero/minimal movement step |
| `01` | `0F` | long delay |
| `02` | `07` | medium delay |
| `03` | `07` | medium delay |
| `04` | `03` | short delay |
| `05` | `03` | short delay |
| `06` | `03` | short delay |
| `07` | `03` | short delay |
| `08` | `01` | minimum delay |
| `09` | `01` | minimum delay |
| `0A` | `01` | minimum delay |
| `0B` | `01` | minimum delay |
| `0C` | `01` | minimum delay |
| `0D` | `01` | minimum delay |
| `0E` | `01` | minimum delay |
| `0F` | `01` | minimum delay |

このtableは、movement/projection step count から、次の state dispatch までのcooldownを作る。

```text
$15D5 小さい -> $15FD 大きい
$15D5 大きい -> $15FD 小さい
```

つまり、step count/速度が大きいほど、次のstate再判定を早める設計と読める。

---

## 6. `$15F3` setter体系

`$15F3,X` のsetterは9箇所確認。

| address | bytes | source | meaning |
|---|---|---|---|
| `address` | `bytes` | source | meaning |
| `C1:9C38` | `9D F3 15` | A = ($80:BB68 & 03) + 1 | random cardinal direction/motion pattern 1..4 |
| `C1:9C64` | `9D F3 15` | table C1:9CAA indexed from $160B high bits | direction from global/object movement bits |
| `C1:9CBF` | `9D F3 15` | immediate #02 | force direction/motion pattern 02 |
| `C1:9D12` | `9D F3 15` | A derived from $0038 high bits + 1 | direction from controller/global/random high bits |
| `C1:9D22` | `9D F3 15` | immediate #02 when $15FD==05 | force direction/motion pattern 02 |
| `C1:9D5B` | `9D F3 15` | A = ($80:BB68 & 03)+1 if changed | random new direction different from current $15F3 |
| `C1:9DE1` | `9D F3 15` | A = $1587 & 07 | direction/motion pattern from actor flags low3 |
| `C1:9DEA` | `9D F3 15` | A = $1587,X & 07 | direction/motion pattern from per-actor flags low3 |
| `C1:9E9A` | `9D F3 15` | A input to C1:9E9A | commit selected movement direction/pattern and render-cache target coords |

### 体系

`$15F3` は主に以下の3種類で設定される。

1. **random cardinal direction**  
   - `$80:BB68 & 03 + 1`
   - `1..4` の方向候補

2. **actor flag low3 bits**  
   - `$1587 & 07`
   - 特殊な向き/状態を含む可能性

3. **forced direction / handler-selected pattern**  
   - immediate `#02`
   - A入力を `C1:9E9A` でcommit

したがって、単純に「向き0..3」ではなく、

```text
1..4 = cardinal direction候補
0/5/6/7 = special / idle / scripted / flag-derived pattern候補
```

として扱うべき。

---

## 7. `C1:9EAD` と `C1:9E9A` の使い分け

典型的なcallerは以下のような流れ。

```text
候補patternを選ぶ
  -> C1:9EAD で通行可否を調べる
  -> allowedなら C1:9E9A で $15F3 と $15DF/$15E9 をcommit
  -> C1:9F18 で $15FD delayを設定
```

`C1:9EAD` はprobe専用で、`$15DF/$15E9` を直接commitしない。  
`C1:9E9A` はcommit専用で、可否probeはしない。

これにより、NPC移動の「候補選択」と「採用」が分かれていることが分かった。

---

## 8. フィールド確定更新

| field | final label | meaning | confidence |
|---|---|---|---|
| `field` | `final_label` | meaning | confidence |
| `$15F3,X` | `actor_motion_direction_pattern` | logical actor movement direction / motion pattern selector. Usually 1..4 for cardinal movement, but low3 bits and special selectors are possible | high |
| `$030B/$0313` | `candidate_next_map_x` | candidate X/column generated by C1:9ED9 from $15DF + direction delta | high |
| `$030D/$0314` | `candidate_next_map_y_depth` | candidate Y/depth generated by C1:9ED9 from $15E9 + direction delta | high |
| `$81:81D3/$81:81D4` | `movement_delta_table_x_y` | direction/motion pattern delta table used by C1:9ED9 | medium-high |
| `C flag after C1:9EAD` | `movement_candidate_allowed` | SEC=allowed/clear, CLC=blocked/invalid | high |
| `$15D5,X` | `actor_movement_projection_step_count` | step count used by C1:9F35 and converted to $15FD by C1:9F18 | high |
| `$15FD,X` | `actor_state_dispatch_delay` | delay/cooldown before next state selector dispatch | high |

---

## 9. Goal 13への反映

Goal 13は **99%据え置き**。

今回で以下が確定寄りになった。

```text
$15F3 = actor_motion_direction_pattern
C1:9ED9 = pattern -> candidate next coordinate
C1:9EAD = candidate movement feasibility check
C1:9E9A = selected pattern + render cache target commit
C1:9F18 = movement step count -> state dispatch delay
```

100%にしない理由:

1. `$81:81D3/$81:81D4` delta tableの実値・方向名が未表化
2. `$81:81DD / B232 / B14F / A0C4 / BA0E / B68E` 個別probeの意味が未確定
3. `$1559/$1511` のstep count元値の意味が未確定
4. `$80:BBEC/$80:BC21/$80:AF0C` のscreen delta反映処理がまだ未分解

---

## 10. 次に攻めるべき箇所

1. `$81:81D3/$81:81D4` delta tableを外部化  
   - pattern 0..7 などを dx/dy にする
2. `C1:9E51` 周辺を完全分解  
   - どの候補patternをどの順で試すか
3. `$81:81DD / B232 / B14F / A0C4 / BA0E / B68E` のprobe個別意味を切る
4. `$1559/$1511` setterを追う
5. `$80:BBEC/$80:BC21/$80:AF0C` を切り、screen deltaがobject workへどう反映するか確定する

