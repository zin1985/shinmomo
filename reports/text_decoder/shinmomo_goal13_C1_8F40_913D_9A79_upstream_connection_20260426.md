# 新桃太郎伝説 Goal 13: `C1:8F40 / C1:913D / C1:9A79` 上流接続と `$157D/$15E9` ラベル確定
作成日: 2026-04-26

## 1. 結論

`C1:90CE` の上流を `C1:8F40 / C1:913D / C1:9A79` でつないだ結果、  
`$157D/$15E9` は「画面上のピクセルY」ではなく、**logical actor の粗いマップ/グリッドY、または深度行(depth row)座標** と見るのが正しい。

最終ラベルは以下。

| field | ラベル | 意味 |
|---|---|---|
| `$1573,X` | `logical_actor_map_x` | logical actorの粗いマップ/グリッドX座標、またはtarget X |
| `$157D,X` | `logical_actor_map_y_depth` | logical actorの粗いマップ/グリッドY座標、またはdepth row / target Y |
| `$15DF,X` | `render_cache_map_x` | 画面投影に使うX座標snapshot/cache |
| `$15E9,X` | `render_cache_map_y_depth` | 画面投影とdepth sortに使うY/depth snapshot/cache |
| `$1591,X` | `visible_object_handle` | logical actor Xに対応するvisible object external handle |
| `$030B/$030C` | `projected_screen_x` | object workへ渡す投影後screen X |
| `$030D/$030E` | `projected_screen_y` | object workへ渡す投影後screen Y |

重要補正:

```text
$157D / $15E9 は screen pixel Y ではない。
$15E9 - $157D を16倍して 0x7F 付近へ足し、$030D screen Yへ投影している。
```

---

## 2. 全体接続

```text
$1569 logical actor list
  -> $1591,X visible object handle
  -> $1573/$157D logical actor map/depth coordinate
  -> C1:9A79 で $15DF/$15E9 render cacheへsnapshot
  -> C1:9F78 で reference $1573/$157D との差分をscreen座標 $030B/$030Dへ投影
  -> C1:938C で object work $0BA7/$0C67 へ書き込み
  -> C1:90CE で $157D - $15E9,X からsort keyを作りAFECへ
  -> $0A61 active linked listをreorder
  -> C0:B03D/B100 でOAM出力
```

これで、`$1569` logical actor層と `$0A61` visible object/OAM層が実線でつながった。

---

## 3. `C1:8F40` の意味

`C1:8F40` は、logical actor X の visible object update pipeline。

主な流れ:

```asm
C1:8F49  LDA $1569,X
         ; actor idが0なら何もしない

C1:8F57  JSL $81:963C

C1:8F5B  LDY $1591,X
C1:8F60  JSL $80:AE88
C1:8F64  JSR $913D
C1:8F67  JSL $81:B43A
C1:8F6B  JSL $80:BCA3

C1:8F6F  JSR $913D
C1:8F72  JSL $81:B413
C1:8F76  JSL $80:BC89

C1:8F91  JSR $93F5
C1:8F94  JSR $9419
C1:8F97  JSR $9175
C1:8F9A  JSR $9186
C1:8F9D  JSR $923E
C1:8FA0  JSR $9296
C1:8FA3  JSR $92BB
C1:8FA6  JSR $9303
```

つまり、`$1591,X` の visible object handle を使って、

- animation state
- sprite group
- position/object work
- special/companion/effect補助
- 表示状態selector

を更新する中核routine。

`C1:90CE` は、このpipelineで更新されたobjectを最終的にactive linked list内で深度順に並べ替える後段と見てよい。

---

## 4. `C1:913D` の意味

`C1:913D` は、logical actorの **display state selector / animation state selector** を返すhelper。

命令上は以下の条件を上から見る。

| order | condition | return |
|---:|---|---:|
| 1 | `$1569,X == 0` | `0` |
| 2 | `$1569,X >= 0x17` | `0` |
| 3 | `$180A[entity-1] bit7 set` | `0x1A` |
| 4 | `$192F == 0x07` | `0x2D` |
| 5 | `$030A != 0` | `0x24` |
| 6 | `$1561 != 0` | `0x0E` |
| 7 | else | `$1569,X` |

つまり、通常時は actor/entity id をそのまま返すが、hidden/suppressed状態やglobal mode時は専用selectorへ差し替える。

これにより、`$180A bit7` のラベルも補強される。

```text
$180A[entity-1] bit7 = actor hidden/suppressed/unavailable flag
```

`C1:913D` は `C1:8F40`, `C1:900A`, `C1:9031`, `C1:9186`, `C1:9AFB` などから呼ばれ、  
logical actorの表示状態/animation状態を一貫して決める共通helperと見てよい。

---

## 5. `C1:9A79` の意味

`C1:9A79` は、logical actor座標の **current -> render cache snapshot**。

```asm
C1:9A79  PHX
C1:9A7A  LDX #$00

loop:
C1:9A7C  LDA $1573,X
C1:9A7F  STA $15DF,X

C1:9A82  LDA $157D,X
C1:9A85  STA $15E9,X

C1:9A88  JSR $9DE5
C1:9A8B  STZ $15FD,X
C1:9A8E  STZ $15D5,X

C1:9A91  INX
C1:9A92  CPX #$0A
C1:9A94  BCC loop

C1:9A97  RTL
```

意味:

```text
for X in 0..9:
    $15DF,X = $1573,X
    $15E9,X = $157D,X
    clear movement/interpolation counters
```

`$15FD/$15D5` は、移動補間や更新pending系の候補。  
`C1:9AFB` や `C1:9F35` で参照されるため、単なる空きではない。

---

## 6. `$157D/$15E9` が「map/depth座標」と言える根拠

`C1:9F78` は `$15DF/$15E9` と `$1573/$157D` の差を取って、screen coordinateへ投影する。

X側:

```asm
C1:9F91  LDA $15DF,X
C1:9F94  SEC
C1:9F95  SBC $1573
C1:9FA0  REP #$20
C1:9FA2  LDA $030B
C1:9FA5  ASL
C1:9FA6  ASL
C1:9FA7  ASL
C1:9FA8  ASL
C1:9FAA  ADC #$0070
...
STA $030B
```

Y側:

```asm
C1:9FC9  LDA $15E9,X
C1:9FCC  SEC
C1:9FCD  SBC $157D
...
C1:9FE4  LDA $030D
C1:9FE7  ASL
C1:9FE8  ASL
C1:9FE9  ASL
C1:9FEA  ASL
C1:9FEC  ADC #$007F
...
STA $030D
```

つまり、

```text
screen_x ≒ ($15DF,X - $1573) * 16 + 0x70 + scroll/suboffset
screen_y ≒ ($15E9,X - $157D) * 16 + 0x7F + scroll/suboffset + terrain/height補正
```

であり、`$157D/$15E9` はピクセルではなく、**16px単位の粗いmap/depth coordinate**。

---

## 7. `C1:938C` で object workへ接続

`C1:938C` は、

```asm
JSL $81:9A79
JSL $81:9F78

LDA $030B
STA $0BA7,Y
LDA $030D
STA $0C67,Y
LDA $030C
STA $0BE7,Y
LDA $030E
STA $0CA7,Y
```

により、投影済みscreen座標をvisible object workへ書く。

したがって、

```text
$15DF/$15E9 render cache
  -> $030B/$030D screen projection
  -> $0BA7/$0C67 object screen position
  -> OAM builder
```

まで接続する。

---

## 8. `C1:90CE` との接続

`C1:90CE` は、

```text
sort key = $157D - $15E9,X + 0x38
```

を作る。これは、reference actorのY/depthとactor Xのrender Y/depthの相対差。

前回の補正どおり、結果は以下の区間写像。

| computed key | final key |
|---|---|
| `< 0x30` | `0x38` |
| `0x30..0x3F` | そのまま |
| `>= 0x40` | `0x48` |

このsort keyを `AFEC` に渡し、visible objectのactive list順を更新する。

つまり、`C1:90CE` は **logical actor render-cache Y/depthに基づくactive linked list depth sorter**。

---

## 9. ゲーム内ラベルの最終案

### 確定寄り

```text
$1573,X = logical_actor_map_x
$157D,X = logical_actor_map_y_depth
$15DF,X = render_cache_map_x
$15E9,X = render_cache_map_y_depth
$1591,X = visible_object_handle
$030B/$030C = projected_screen_x
$030D/$030E = projected_screen_y
```

### まだ注意付き

```text
$15FD,X = movement/interpolation counter candidate
$15D5,X = movement/update pending flag candidate
$1609/$160A = sub-tile scroll / movement offset candidate
$150C/$150D = screen scroll or reference camera offset candidate
```

---

## 10. Goal 13進捗

Goal 13は **99%据え置き**。

99%に上げた根拠は維持できるが、100%にはまだしない。理由:

- `$157D/$15E9` のラベルは「map/depth coordinate」でかなり固い
- ただし、`$15FD/$15D5/$1609/$160A/$150C/$150D` の補間・スクロール意味がまだ残る
- `$0B27` bit定義とB294 frame/pieceの完全接続が未完

---

## 11. 次に攻めるべき場所

1. `C1:9AFB` を完全分解  
   - `$15FD` と `$15D5` の正体
2. `C1:9F35` を完全分解  
   - movement/update pendingと画面投影の関係
3. `C1:9F78` を16bit immediate前提で再分解  
   - `$150C/$150D/$1609/$160A` の意味を確定
4. `C0:B100` とB294のpiece出力を完全対応  
   - `$0B27` bit定義とOAM attr生成を100%へ

