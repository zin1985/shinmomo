# 新桃太郎伝説 `$0BA7/$0C67` → OAM書込・画面外クリッピング経路解析

作成日: 2026-04-25  
対象: `$0BA7/$0C67` 系 object座標配列から、OAM buffer `$0EE9/$10E9` へ落ちる経路

---

## 0. 結論

`$0BA7/$0C67` 系は、OAM構築処理に渡っていると見てよい。  
ただし、C7側で見えている `$0BA7,Y / $0C67,Y` が、OAM builder側ではそのまま同じ表記で読まれるのではなく、**active slot index が +2 された状態で `$0BA5,X / $0C65,X` として読まれる**。

この +2 ずれが今回の最重要点。

```text
C7 object側:
  object_local_id = Y
  X座標 low  = $0BA7,Y
  X座標 high = $0BE7,Y
  Y座標 low  = $0C67,Y
  Y座標 high = $0CA7,Y

OAM builder側:
  active_slot = X = object_local_id + 2
  X座標 low  = $0BA5,X = $0BA7,object_local_id
  X座標 high = $0BE5,X = $0BE7,object_local_id
  Y座標 low  = $0C65,X = $0C67,object_local_id
  Y座標 high = $0CA5,X = $0CA7,object_local_id
```

したがって、`$0BA7/$0C67` は **object座標配列 → sprite片ごとのクリッピング → OAM lower/high buffer → OAM DMA** へ確実に流れる。

---

## 1. slot index の +2 ずれ

### 1-1. object slot allocator

既存メモ上の `C0:AF33` 付近、LoROM換算では `C1:AF33` 相当。  
ここで active object slot を `2..0x41` から探す。

重要箇所:

```text
C0:AF3E  LDX #$02
C0:AF40  LDA $0AA3,X
...
C0:AF5E  STA $0A61,X    ; active list link
...
C0:AF72  LDA $6B
C0:AF74  STA $0AA3,X    ; priority / sort key
C0:AF77  DEX
C0:AF78  DEX            ; X = active_slot - 2
C0:AF79  STZ $0AE7,X
...
C0:AF9C  INC $0AE5
C0:AF9F  TXA
C0:AFA0  STX $6B        ; return object_local_id = active_slot - 2
```

ここで、active list に載る index は `2..` だが、object codeへ返る `$6B` は `active_slot - 2`。

### 1-2. C7 object初期化

C7側の object初期化では、返された `$6B` を `Y` にして、`$0BA7,Y` へ座標を書く。

```text
C7:92F4  LDA $6B
C7:92F6  STA $1154,X
C7:92F9  TAY
C7:92FD  LDA #$80
C7:92FF  STA $0BA7,Y
C7:9304  STA $0BE7,Y
C7:9309  STA $0B67,Y
C7:930E  STA $0C67,Y
C7:9313  STA $0CA7,Y
C7:9318  STA $0C27,Y
```

よって C7側の `Y` は **object_local_id**。

### 1-3. OAM builder側の読み方

OAM builderは active list を `X` で巡回する。

```text
C0:B053  LDX $0A61
C0:B056  LDA $0AE5,X
C0:B059  BEQ skip
C0:B05B  JSR $B100
C0:B05E  LDA $0A61,X
C0:B061  TAX
C0:B062  CPX #$02
C0:B064  BCS $B056
```

ここで `X` は active_slot。つまり `object_local_id + 2`。  
そのため、OAM builder は `$0BA5,X` と読む。

```text
C0:B172  ADC $0BA5,X
C0:B179  ADC $0BE5,X
C0:B1A1  ADC $0C65,X
C0:B1A8  ADC $0CA5,X
```

`X = Y + 2` なので、実体アドレスは一致する。

---

## 2. OAM構築の入口

### 2-1. 1フレームのOAM構築入口

```text
C0:A057  JSL $80:B03D
```

`B03D` はOAM構築のメイン入口。  
既存の disasm 表記では `C0:B03D` だが、ROM offset / LoROM換算では `C1:B03D` 相当として扱うと混乱が少ない。

### 2-2. OAM構築メイン

```text
C0:B03D  PHB
C0:B040  LDA #$80
C0:B042  STA $0A1C      ; 残りOAM枠 = 128
C0:B045  STZ $1109      ; OAM lower table write ptr
C0:B04B  STZ $110B      ; high OAM byte ptr
C0:B050  STA $110C      ; high OAM bit counter = 4
C0:B053  LDX $0A61      ; active list head
```

`$0A1C = 0x80` は、SNES sprite 128枚分の残り枠として非常に自然。

---

## 3. sprite片構築と事前枠チェック

`B100` は active object 1体分の sprite定義を読み、sprite片ごとに画面内判定してOAMへ積む。

```text
C0:B100  LDA $0DE5,X
C0:B104  LDA $0DA5,X
...
C0:B119  LDA $0B25,X
...
C0:B13B  LDA $0AE5,X
C0:B146  LDA [$2A],Y
C0:B14C  LDA [$2A]
C0:B14E  STA $24       ; sprite片数
C0:B150  LDA $0A1C
C0:B153  CMP $24
C0:B155  BCS ok
C0:B157  RTS           ; 残りOAM枠不足ならobjectごと描かない
```

ここで重要なのは、**表示できる残りOAM枠が sprite片数より少なければ、そのobjectは丸ごと描画されない** こと。  
これはNPC大量表示時の軽減ロジックとして重要。

---

## 4. X方向クリッピング

sprite片のX offsetをobject Xに加算し、画面外ならOAMへ書かない。

```text
C0:B160  LDA [$2A],Y   ; sprite片 flags / x符号など
C0:B163  STA $1E
C0:B167  BIT #$10
C0:B169  BEQ +
C0:B16B  DEC $21       ; x offset sign extend = FF

C0:B16D  LDA [$2A],Y   ; sprite片 X offset
C0:B171  CLC
C0:B172  ADC $0BA5,X   ; object X low
C0:B175  STA $06       ; final OAM X low
C0:B177  LDA $21
C0:B179  ADC $0BE5,X   ; object X high / sign page
C0:B17C  AND #$0F
C0:B17E  STA $07       ; high OAM X bit source
C0:B180  BEQ in_range
C0:B182  CMP #$0F
C0:B184  BNE skip
C0:B186  LDA $06
C0:B188  CMP #$C0
C0:B18A  BCS in_range
C0:B18C  JMP $B24C     ; X画面外。OAM書込スキップ
```

### X判定仕様

| 条件 | 判定 |
|---|---|
| high nibble = `0` | 通常画面内 |
| high nibble = `0xF` かつ X low >= `0xC0` | 左端の負座標として許容 |
| それ以外 | sprite片をスキップ |

これにより、画面外のsprite片はOAMを消費しない。

---

## 5. Y方向クリッピング

```text
C0:B190  STZ $21
C0:B192  LDA $1E
C0:B194  BIT #$20
C0:B196  BEQ +
C0:B198  DEC $21       ; y offset sign extend = FF

C0:B19A  LDA [$2A],Y   ; sprite片 Y offset
C0:B19C  SEC
C0:B19D  SBC $0CE5,X   ; object Y anchor / pivot補正
C0:B1A0  CLC
C0:B1A1  ADC $0C65,X   ; object Y low
C0:B1A4  STA $09       ; final OAM Y
C0:B1A6  LDA $21
C0:B1A8  ADC $0CA5,X   ; object Y high
C0:B1AB  AND #$0F
C0:B1AD  BEQ normal_y
C0:B1AF  CMP #$0F
C0:B1B1  BNE skip
C0:B1B3  LDA $09
C0:B1B5  CMP #$F0
C0:B1B7  BCS ok_negative_edge
C0:B1B9  JMP $B24D
C0:B1BC  LDA $09
C0:B1BE  CMP #$E0
C0:B1C0  BCS skip
```

### Y判定仕様

| 条件 | 判定 |
|---|---|
| high nibble = `0` かつ Y < `0xE0` | 通常画面内 |
| high nibble = `0xF` かつ Y >= `0xF0` | 上端/負座標側として許容 |
| Y >= `0xE0` | 非表示扱いでスキップ |
| それ以外 | sprite片をスキップ |

SNES OAMで `Y=E0` は非表示用途としてよく使われるため、`E0` 閾値は自然。

---

## 6. OAM lower table書込

クリッピングを通過したsprite片だけ `$0EE9..` へ4バイトで書かれる。

```text
C0:B225  LDX $1109
C0:B228  LDA $06
C0:B22A  STA $0EE9,X   ; OAM X
C0:B22D  INX
C0:B22E  LDA $09
C0:B230  DEC A
C0:B231  STA $0EE9,X   ; OAM Y - 1
C0:B234  INX
C0:B235  LDA $0F
C0:B237  STA $0EE9,X   ; tile number
C0:B23A  INX
C0:B23B  LDA $10
C0:B23D  STA $0EE9,X   ; attributes
C0:B240  INX
C0:B241  STX $1109
C0:B247  DEC $0A1C     ; 残りOAM枠を1消費
```

### OAM lower entry

| offset | 内容 |
|---:|---|
| +0 | X |
| +1 | Y - 1 |
| +2 | tile |
| +3 | attr |

---

## 7. OAM high table pack

`$10E9..` はSNES OAM high table相当。  
4 sprite分の high bit / size bit を1バイトへ詰める構造。

```text
C0:B1FA  LDX $110B
C0:B1FD  LDA $110C
C0:B200  CMP #$04
C0:B204  STZ $10E9,X   ; 新しいhigh OAM byte開始時にクリア

C0:B207  LSR $07
C0:B209  ROR $10E9,X   ; X high bit
C0:B20C  LDA $1E
C0:B20E  LSR A
C0:B20F  LSR A
C0:B210  LSR A
C0:B211  LSR A
C0:B212  ROR $10E9,X   ; size bit候補

C0:B215  DEC $110C
C0:B218  BNE continue
C0:B21A  INX
C0:B21B  STX $110B
C0:B21E  LDA #$04
C0:B220  STA $110C
```

`$07` はX high判定で作った値。  
`$1E >> 4` から size/高位属性らしきbitも詰めている。

---

## 8. 非表示埋めと表示抑制

### 8-1. 前フレームより表示数が減った場合の非表示埋め

`B03D` の後半では、今回使ったOAM枚数が前回より少ない場合、残った古いOAM entryを `Y=E0` で埋める。

```text
C0:B07E  LDA $0A1C
C0:B081  SEC
C0:B082  SBC $110D
C0:B085  BCC $B0C0
C0:B087  BEQ $B0C0
C0:B089  STA $1E
...
C0:B096  STZ $0EE9,X
C0:B099  STA $0EEA,X   ; E0
C0:B09C  STZ $0EEB,X
C0:B09F  STZ $0EEC,X
```

`$110D` は前回DMA時に保存された残りOAM枠。

```text
C0:B0CC  LDA $0A1C
C0:B0CF  STA $110D
```

したがって、フレーム間でsprite数が減った時にだけ、余った古いspriteを明示的に隠す。

### 8-2. dirty flag

```text
C0:B0C0  LDA #$01
C0:B0C2  STA $0A1B
```

OAM bufferを構築した後、`$0A1B` を立てる。

---

## 9. OAM DMA

```text
C0:B0C7  LDA $0A1B
C0:B0CA  BEQ end
C0:B0CC  LDA $0A1C
C0:B0CF  STA $110D
C0:B0D2  STZ $4300
C0:B0D5  LDA #$E9
C0:B0D7  STA $4302
C0:B0DA  LDA #$0E
C0:B0DC  STA $4303
C0:B0DF  STZ $4304
C0:B0E2  LDA #$04
C0:B0E4  STA $4301      ; BBAD = $2104
C0:B0E7  LDA #$20
C0:B0E9  STA $4305
C0:B0EC  LDA #$02
C0:B0EE  STA $4306      ; size = 0x0220
C0:B0F1  STZ $2102
C0:B0F4  STZ $2103
C0:B0F7  STZ $0A1B
C0:B0FA  LDA #$01
C0:B0FC  STA $420B
```

DMA source: `$00:0EE9`  
DMA destination: `$2104`  
size: `0x0220` bytes

`0x200` bytes lower OAM + `0x20` bytes high OAM と見てよい。

---

## 10. 経路まとめ

```text
C7 object/effect code
  ├─ C7:92FF / C7:9EAB / C7:F081 / C7:F101 / C7:F1A0
  │    ↓
  │  $0BA7,Y / $0BE7,Y / $0C67,Y / $0CA7,Y
  │    ↓  Y = object_local_id
  │
object allocator / active list
  ├─ active_slot = object_local_id + 2
  ├─ $0A61 active list
  │    ↓
  │
OAM builder B03D/B100
  ├─ reads $0BA5,X / $0BE5,X / $0C65,X / $0CA5,X
  │       = $0BA7,Y / $0BE7,Y / $0C67,Y / $0CA7,Y
  ├─ sprite piece X/Y offset加算
  ├─ X/Y 画面外クリッピング
  ├─ OAM残枠不足ならobjectごと描画中止
  │    ↓
  │
OAM buffer
  ├─ $0EE9.. lower OAM
  ├─ $10E9.. high OAM
  ├─ unused entryはY=E0で非表示埋め
  │    ↓
  │
OAM DMA B0C7
  └─ $0EE9..$1108 → PPU $2104, 0x220 bytes
```

---

## 11. NPC大量表示軽減として見えた仕様

今回、Goal 13に直結する表示抑制ロジックは以下。

| レイヤー | 内容 | 確度 |
|---|---|---:|
| active list巡回 | `$0A61` linked listで表示対象objectのみ巡回 | 高 |
| object単位OAM枠チェック | `$0A1C < sprite片数` ならobjectごと描画しない | 高 |
| sprite片Xクリッピング | 画面外Xならその片をOAMに積まない | 最高 |
| sprite片Yクリッピング | `Y>=E0` やhigh nibble異常ならOAMに積まない | 最高 |
| high OAM pack | X high/size bitを4sprite単位で圧縮 | 高 |
| stale OAM非表示 | 前フレームより使用数が減った分をY=E0で隠す | 高 |
| dirty flag DMA | `$0A1B` が立った時だけOAM DMA | 高 |

これにより、NPC大量表示時には、

1. active objectだけ見る
2. OAM枠が足りないobjectは丸ごと諦める
3. 画面外sprite片はOAMに積まない
4. 余った古いspriteはY=E0で隠す
5. 必要時だけOAM DMAする

という多段の軽減がある。

---

## 12. 13目標への反映

| Goal | 旧 | 新 | 理由 |
|---:|---:|---:|---|
| 8. 条件分岐ディスパッチ系 | 80% | 80% | 今回は表示後段が中心のため据え置き |
| 11. 外部データ化 | 94% | 95% | OAM/object work仕様を外部表化できた |
| 12. 全体構造の人間可読化 | 96% | 97% | object座標からOAM DMAまで一本の経路で説明可能に |
| 13. NPC大量表示時の処理軽減ロジック | 46% | 58% | OAM枠不足・画面外クリッピング・非表示埋め・DMAまで接続 |

Goal 13は **46% → 58%** に上げてよい。  
理由は、これまで「座標配列」と「OAM builder」が別々だったものが、slot index +2補正で直接接続できたため。

---

## 13. 次に攻めるべき箇所

1. `$0CE5,X` の意味を確定する  
   - `B19D SBC $0CE5,X` でY offsetから引かれる。sprite anchor / height / pivot候補。

2. `$0B25,X` のbit定義を詰める  
   - `bit 0x40` で `B25C` へ直行。
   - 下位4bitは sprite definition group index。
   - `0x30` はattrへ混ぜられる。

3. `$0AE5,X` の animation frame / pattern index を確定する  
   - sprite definition pointerから frameごとのsprite片定義を選ぶ。

4. `B294` pointer tableを外部化する  
   - sprite definition groupごとの pointerを抽出し、sprite片数・片定義を一覧化する。

5. `$0DA5/$0DE5` と tile番号 `$0F` の関係を整理する  
   - tile base / dynamic tile offset / VRAM tile index候補。

6. active list `$0A61/$0A1F/$0AA3` を仕様表にする  
   - 表示優先度、挿入順、sort keyが見える可能性がある。

