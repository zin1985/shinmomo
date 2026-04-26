# 新桃太郎伝説 C7 object work 仕様表  
対象: `$0BA7/$0C67` 系 object座標配列  
作成日: 2026-04-25

## 0. 結論

`$0BA7,Y / $0C67,Y` 系は、C7側 object / sprite / effect work の **座標配列** と見てよい。

特に `C7:92FF` のslot初期化、`C7:9ECB/9EE8` の移動更新、`C7:F081/F101/F1A0` の初期座標helperが同じ配列を操作しており、以下の構造がかなり強い。

```text
object slot Y
  X座標:
    $0B67,Y = X subpixel / fraction low
    $0BA7,Y = X position low / screen X
    $0BE7,Y = X position high / sign / page

  Y座標:
    $0C27,Y = Y subpixel / fraction low
    $0C67,Y = Y position low / screen Y
    $0CA7,Y = Y position high / sign / page

motion parameter slot X
  $11A4,X = X velocity low / fraction
  $11B4,X = X velocity high / signed integer
  $11C4,X = Y velocity low / fraction
  $11D4,X = Y velocity high / signed integer
  $11E4,X = secondary X accel / angle / parameter
  $11F4,X = secondary Y accel / delta / parameter
```

重要なのは、`$0BA7` と `$0C67` が単独ではなく、`$0B67/$0BE7`、`$0C27/$0CA7` と組で更新されている点。  
したがって `8bit座標だけ` ではなく、**固定小数点＋符号/ページ付きのobject座標** と見るのが安全。

---

## 1. object work 配列表

| WRAM | 用途 | 確度 | 根拠 |
|---|---|---:|---|
| `$0B67,Y` | X subpixel / fraction low | 高 | `C7:9EBC`, `C7:9ED9` で `$11A4,X` と加減算 |
| `$0BA7,Y` | X position low / screen X | 最高 | `C7:92FF`, `C7:9ECB/9EE8`, `C7:F081/F101/F1A0` など多数が書込 |
| `$0BE7,Y` | X position high / sign/page | 高 | `C7:9ED3/9EF0` で `$11B4` の符号拡張分 `$0F` を反映 |
| `$0C27,Y` | Y subpixel / fraction low | 高 | `C7:9F03` で `$11C4,X` と加算 |
| `$0C67,Y` | Y position low / screen Y | 最高 | `C7:930E`, `C7:9F0C`, `C7:F087/F1A9` など多数が書込 |
| `$0CA7,Y` | Y position high / sign/page | 高 | `C7:9F14` で `$11D4` の符号拡張分 `$0F` を反映 |
| `$11A4,X` | X velocity low / fraction | 高 | `C7:9EBC/9ED9` で `$0B67,Y` に加減算 |
| `$11B4,X` | X velocity high / signed integer | 高 | `C7:9EC5/9EE2` で `$0BA7,Y` に加減算 |
| `$11C4,X` | Y velocity low / fraction | 高 | `C7:9EFD` で `$0C27,Y` に加算 |
| `$11D4,X` | Y velocity high / signed integer | 高 | `C7:9F06` で `$0C67,Y` に加算 |
| `$11E4,X` | secondary X acceleration / angle-like param | 中〜高 | `C7:9F5B` で `$11A4/$11B4` に加算、`C7:F207` でtable設定 |
| `$11F4,X` | secondary Y acceleration / delta-like param | 中〜高 | `C7:9F5B` で `$11C4/$11D4` に加算、`C7:F207` でtable設定 |
| `$1174,X` | object flags / direction / mode | 高 | `C7:9EB4` でbit `0x04` を見てX方向を反転、`C7:9F96` でも下位bit参照 |
| `$1154,X` | object slot id / active slot link | 中〜高 | `C7:92F6` でslot保存、`C7:9F18` linked source参照で使用 |
| `$1164,X` | parent/source slot link | 中〜高 | `C7:9333` で初期化、`C7:9F1A` でsource参照 |

---

## 2. `C7:92FF` slot初期化

### 対象範囲

```text
C7:92FD: A9 80
C7:92FF: 99 A7 0B   STA $0BA7,Y
C7:9302: A9 00
C7:9304: 99 E7 0B   STA $0BE7,Y
C7:9307: A9 00
C7:9309: 99 67 0B   STA $0B67,Y
C7:930C: A9 80
C7:930E: 99 67 0C   STA $0C67,Y
C7:9311: A9 00
C7:9313: 99 A7 0C   STA $0CA7,Y
C7:9316: A9 00
C7:9318: 99 27 0C   STA $0C27,Y
C7:931B: 9E A4 11   STZ $11A4,X
C7:931E: 9E B4 11   STZ $11B4,X
C7:9321: 9E C4 11   STZ $11C4,X
C7:9324: 9E D4 11   STZ $11D4,X
C7:9327: 9E E4 11   STZ $11E4,X
C7:932A: 9E F4 11   STZ $11F4,X
```

### 仕様

| 項目 | 初期値 | 意味 |
|---|---:|---|
| `$0BA7,Y` | `0x80` | X low 初期値 |
| `$0BE7,Y` | `0x00` | X high 初期値 |
| `$0B67,Y` | `0x00` | X fraction 初期値 |
| `$0C67,Y` | `0x80` | Y low 初期値 |
| `$0CA7,Y` | `0x00` | Y high 初期値 |
| `$0C27,Y` | `0x00` | Y fraction 初期値 |
| `$11A4..$11F4,X` | `0x00` | 速度/加速度/副パラメータを初期化 |

### 解釈

object slot生成時、座標を `(x=0x0080, y=0x0080)` 付近に置き、速度系を0にする初期化ルーチン。  
この後、`C7:F081` / `C7:F101` / `C7:F1A0` などのhelperで初期座標が上書きされる。

---

## 3. `C7:9EAB..9F17` 移動更新

### X方向

```text
C7:9EAB: STZ $0F
C7:9EAD: LDA $11B4,X
C7:9EB0: BPL +
C7:9EB2: DEC $0F
C7:9EB4: LDA $1174,X
C7:9EB7: BIT #$04
C7:9EB9: BEQ add_x

sub_x:
C7:9EBB: SEC
C7:9EBC: LDA $0B67,Y
C7:9EBF: SBC $11A4,X
C7:9EC2: STA $0B67,Y
C7:9EC5: LDA $0BA7,Y
C7:9EC8: SBC $11B4,X
C7:9ECB: STA $0BA7,Y
C7:9ECE: LDA $0BE7,Y
C7:9ED1: SBC $0F
C7:9ED3: STA $0BE7,Y
C7:9ED6: BRA y_update

add_x:
C7:9ED8: CLC
C7:9ED9: LDA $0B67,Y
C7:9EDC: ADC $11A4,X
C7:9EDF: STA $0B67,Y
C7:9EE2: LDA $0BA7,Y
C7:9EE5: ADC $11B4,X
C7:9EE8: STA $0BA7,Y
C7:9EEB: LDA $0BE7,Y
C7:9EEE: ADC $0F
C7:9EF0: STA $0BE7,Y
```

### Y方向

```text
C7:9EF3: STZ $0F
C7:9EF5: LDA $11D4,X
C7:9EF8: BPL +
C7:9EFA: DEC $0F
C7:9EFC: CLC
C7:9EFD: LDA $0C27,Y
C7:9F00: ADC $11C4,X
C7:9F03: STA $0C27,Y
C7:9F06: LDA $0C67,Y
C7:9F09: ADC $11D4,X
C7:9F0C: STA $0C67,Y
C7:9F0F: LDA $0CA7,Y
C7:9F12: ADC $0F
C7:9F14: STA $0CA7,Y
C7:9F17: RTS
```

### 仕様

| 条件 | X方向処理 |
|---|---|
| `$1174,X & 0x04 != 0` | X速度を減算。左右反転/逆走扱い |
| `$1174,X & 0x04 == 0` | X速度を加算。通常方向 |

Y方向は常に加算。  
`$11B4` / `$11D4` の符号を `$0F` に拡張して high byte に反映しているため、座標は **fraction + low + high の3段構造** と見てよい。

---

## 4. `C7:9F18..9F5A` parent/source object からの相対座標設定

### 役割

子objectやエフェクトobjectを、親objectの現在座標を基準に置く処理。

```text
target.x = source.x + offset_x
target.y = source.y + offset_y
```

### 観測点

| 書込 | 意味 |
|---|---|
| `C7:9F2D STA $0BA7,Y` | source `$0BA7` + `$11A4` をtarget Xへ |
| `C7:9F3A STA $0BE7,Y` | source `$0BE7` + `$11B4` をtarget X highへ |
| `C7:9F48 STA $0C67,Y` | source `$0C67` + `$11C4` をtarget Yへ |
| `C7:9F55 STA $0CA7,Y` | source `$0CA7` + `$11D4` をtarget Y highへ |

### 解釈

`$1164,X` → parent/source slot、`$1154,X` → object work slot id のようなリンクをたどり、  
親座標にoffsetを足して子objectの座標を作る。  
表示エフェクト、付属パーツ、弾、吹き出し、演出objectに使われる可能性が高い。

---

## 5. `C7:9F5B..9F95` 加速度 / 速度更新

### 概要

```text
$11A4/$11B4 += sign_extend($11E4)
$11C4/$11D4 += sign_extend($11F4)
```

### 観測点

| 書込 | 意味 |
|---|---|
| `C7:9F78 STA $11A4,X` | X velocity low を更新 |
| `C7:9F80 STA $11B4,X` | X velocity high を更新 |
| `C7:9F89 STA $11C4,X` | Y velocity low を更新 |
| `C7:9F91 STA $11D4,X` | Y velocity high を更新 |

### 解釈

`$11E4/$11F4` は、通常の座標ではなく **速度へ足し込む二次パラメータ**。  
文脈により「加速度」「重力」「角度から算出したdelta」「演出用の変化量」として使われる可能性がある。

---

## 6. 初期座標helper群

## 6-1. `C7:F081` helper

### code

```text
C7:F07E: BD 91 F0   LDA $F091,X
C7:F081: 99 A7 0B   STA $0BA7,Y
C7:F084: BD 94 F0   LDA $F094,X
C7:F087: 99 67 0C   STA $0C67,Y
C7:F08A: BD 97 F0   LDA $F097,X
C7:F08D: 99 A7 0C   STA $0CA7,Y
C7:F090: 60         RTS
```

### tables

```text
C7:F091: 80 80 80
C7:F094: 40 40 40
C7:F097: FF FD FB
```

### 仕様

| index | `$0BA7` X low | `$0C67` Y low | `$0CA7` Y high |
|---:|---:|---:|---:|
| 0 | `0x80` | `0x40` | `0xFF` |
| 1 | `0x80` | `0x40` | `0xFD` |
| 2 | `0x80` | `0x40` | `0xFB` |

### 解釈

Xは中央付近固定、Y highを大きく変える。  
画面外上/下、あるいは遠方から入る演出objectの初期位置候補。

---

## 6-2. `C7:F0F9 / C7:F101` helper

### code

```text
C7:F0F9: DA          PHX
C7:F0FA: 8A          TXA
C7:F0FB: 29 03       AND #$03
C7:F0FD: AA          TAX
C7:F0FE: BD 06 F1    LDA $F106,X
C7:F101: 99 A7 0B    STA $0BA7,Y
C7:F104: FA          PLX
C7:F105: 60          RTS
```

### table

```text
C7:F106: 48 68 88 A8
```

| index | X low |
|---:|---:|
| 0 | `0x48` |
| 1 | `0x68` |
| 2 | `0x88` |
| 3 | `0xA8` |

### 解釈

32px刻みの横位置table。  
`X & 3` で4列に配置するため、objectを横に4本並べる処理の可能性が高い。

---

## 6-3. `C7:F150..F1B7` / `C7:F1A0` dynamic座標helper

### 座標書込部

```text
C7:F19A: A9 70       LDA #$70
C7:F19C: 18          CLC
C7:F19D: 6D 0C 15    ADC $150C
C7:F1A0: 99 A7 0B    STA $0BA7,Y

C7:F1A3: A9 7F       LDA #$7F
C7:F1A5: 18          CLC
C7:F1A6: 6D 0D 15    ADC $150D
C7:F1A9: 99 67 0C    STA $0C67,Y
```

### 仕様

| 書込先 | 値 |
|---|---|
| `$0BA7,Y` | `0x70 + $150C` |
| `$0C67,Y` | `0x7F + $150D` |

### 追加観測

このhelper内では以下の外部/共通処理も呼ぶ。

```text
JSL $84ED77
JSL $80AE79
JSL $80A510
JSL $80AFEC
```

### 解釈

固定tableではなく、`$150C/$150D` のruntime値を使う **画面/対象/カメラ/actor相対の初期座標helper**。  
`$0BA7/$0C67` に直接入れるため、座標helperである点は高確度。

---

## 6-4. 補助座標helper群

| helper | 書込先 | table | 役割候補 |
|---|---|---|---|
| `C7:F1EC` | `$0BA7,$0C67` | `F1F7` 8組 | 小さな弧/列配置 |
| `C7:F24B` | `$0BA7,$0BE7,$0C67,$0CA7` | `F262` 8組×4byte | full座標table |
| `C7:F307` | `$0BA7,$0BE7,$0C67,$0CA7` | `F31E` 8組×4byte | full座標tableその2 |
| `C7:F62C` | `$0BA7,$0C67` | `F637` 12組程度 | 散開/配置table |

### `C7:F1F7` table

```text
(6A,78), (6E,72), (72,70), (76,6F),
(7A,6F), (7E,70), (82,72), (86,78)
```

小さな弧状・波状配置に見える。

### `C7:F262` full coordinate table

```text
(18,00,80,FF), (36,00,7A,FF), (54,00,77,FF), (68,00,75,FF),
(88,00,75,FF), (9C,00,77,FF), (BA,00,7A,FF), (D8,00,80,FF)
```

`X low, X high, Y low, Y high` の4byte組として非常に自然。

### `C7:F31E` full coordinate table

```text
(10,01,C0,00), (D0,00,10,01), (30,00,10,01), (F0,FF,C0,00),
(F0,FF,20,00), (30,00,F0,FF), (D0,00,F0,FF), (10,01,20,00)
```

符号付き高byteを含むため、画面外/周辺からの出現配置に見える。

### `C7:F637` coordinate table

```text
(38,30), (B0,30), (38,B0), (B0,B0),
(C0,58), (B0,68), (B0,78), (C0,88),
(28,58), (38,68), (38,78), (28,88)
```

12点の配置table。矩形/周辺配置の候補。

---

## 7. object座標系の仕様まとめ

### 7-1. 座標モデル

```text
X = sign/page($0BE7) : low($0BA7) : frac($0B67)
Y = sign/page($0CA7) : low($0C67) : frac($0C27)
```

`$0BA7/$0C67` だけを見ると8bit座標に見えるが、移動更新ではfractionとhigh/signも一緒に扱う。  
よって、内部的には **固定小数点のobject座標**。

### 7-2. 移動モデル

```text
if ($1174 & 0x04):
    X -= velocityX
else:
    X += velocityX

Y += velocityY
```

```text
velocityX = $11B4:$11A4
velocityY = $11D4:$11C4
```

### 7-3. 加速度モデル

```text
velocityX += sign_extend($11E4)
velocityY += sign_extend($11F4)
```

ただし `$11E4/$11F4` は他ルーチンでは角度/速度パラメータとして使われる可能性もあるため、  
**secondary motion parameter** として扱うのが安全。

### 7-4. helperの役割

| helper | 役割 |
|---|---|
| `C7:92FF` | slot初期化 |
| `C7:9EAB..9F17` | position += velocity |
| `C7:9F18..9F5A` | parent/source + offset で子object位置を作る |
| `C7:9F5B..9F95` | velocity += secondary delta |
| `C7:F081` | table型の初期座標設定 |
| `C7:F101` | 横4列のX初期値設定 |
| `C7:F1A0` | runtime値 `$150C/$150D` に基づく動的初期座標設定 |
| `C7:F1EC/F24B/F307/F62C` | table型の配置helper |

---

## 8. 13目標への反映

| Goal | 旧 | 新 | 理由 |
|---:|---:|---:|---|
| 8. 条件分岐ディスパッチ系 | 79% | 80% | continuation runnerがobject setupへつながる理解が進んだ |
| 9. 会話・店・イベントスクリプト仕様書 | 95% | 95% | 会話仕様ではなくobject/effect VM側なので据え置き |
| 11. 外部データ化 | 93% | 94% | object work配列と初期座標tableを外部仕様化できた |
| 12. 全体構造の人間可読化 | 95% | 96% | C7 continuation と object work の接続が説明可能になった |
| 13. NPC大量表示時の処理軽減ロジック | 42% | 46% | object座標配列が固まり、OAM/クリッピング追跡の足場が強化 |

---

## 9. 次に攻めるべき箇所

次は `$0BA7/$0C67` をOAMへ落とす経路を追うのが最重要。

候補は以下。

1. `$0BA7/$0C67` の read 箇所を逆引きする  
   - 特に `LDA $0BA7,Y` / `LDA $0C67,Y`
   - OAM work `$0200..$04xx`、`$0Axx`、`$7E:xxxx` への転送を探す

2. `C7:B100..B25C` の画面外クリッピングと接続する  
   - 以前のNPC大量表示軽減候補
   - `$0BA7/$0C67` がそこに入るなら Goal 13 が大きく伸びる

3. `$0BE7/$0CA7` のクリッピング判定を見る  
   - high/signが0以外のとき非表示にしている可能性が高い

4. `$1174` bit定義を詰める  
   - bit `0x04` = X方向反転はかなり強い
   - 他bitが表示/消滅/更新/クリッピングに絡む可能性あり

5. `C7:F24B/F307` のfull coordinate tableが何の演出に対応するか、record側から逆引きする