# 新桃太郎伝説 Goal 13: `$0A61` active linked list 静的逆引きメモ
作成日: 2026-04-26

## 1. 結論

NPCログを材料に、静的側へ戻って `$0A61` 周辺を逆引きした結果、  
月の神殿・はじまりの村で見えていた画面上NPC/移動NPCの本線は、以下でかなり確定寄り。

```text
$0A61[slot] = next slot
$0A1F[slot] = prev slot
$0AA3[slot] = sort key / priority / depth key

C0:AF33  object allocate + sorted insert
C0:AFAA  object remove / unlink
C0:AFEC  existing object reorder / sort-key update
C0:B03D  active chain walk + OAM build
C0:B0C7  OAM DMA transfer
```

つまり `$0A61` は「active object ID配列」ではなく、**active object linked list の next pointer table**。

runtimeログの、

```text
15->03->02->04->0C->0D->...->01->FF
```

のようなactive chainは、この `$0A61/$0A1F` 双方向リストそのものと見てよい。

---

## 2. フィールド定義更新

| field | 新しい解釈 | 根拠 |
|---|---|---|
| `$0A61[slot]` | next pointer | `STA $0A61,X/Y` でリンク差し替え。`C0:B03D` が `$0A61` 先頭から辿る |
| `$0A1F[slot]` | previous pointer | insert/remove/reorderでnextと対になる |
| `$0AA3[slot]` | sort key / priority / depth key | `C0:AF33` で `$6B` を格納、`C0:AFEC` で新key `$1E` を格納 |
| `$0AE5` absolute | active object count | allocate時 `INC $0AE5`、remove時 `DEC $0AE5` |
| `$0A1D` | default sprite group/attr seed | initで `0x20`、allocate時 `$0B27,X` へ入る |
| `$0A1C` | OAM remaining budget / remaining sprite pieces | OAM build開始時 `0x80`、piece出力ごとに減る |
| `$0A1B` | OAM dirty flag | OAM build後に `1`、DMA後に `0` |
| `$0EE9..` | OAM mirror | `x,y,tile,attr` 形式。hiddenは `00 E0 00 00` |

注意: runtime Luaの `b25/ae5` 表示は「slot indexぶんずらした見え方」。  
静的には多くの本体fieldが `$0B27,Y` / `$0AE7,Y` のように、slot handle `Y` を前提にアクセスされる。  
たとえばruntimeの `s02/b25=22` は `$0B25+2=$0B27` を読んでいるので、静的field `$0B27` と一致する。

---

## 3. 主要routine

### 3-1. `C0:AE59` 近辺: active list初期化

```asm
C0:AE59  LDA #$01
C0:AE5B  STA $0AA3
C0:AE5E  STA $0A61
C0:AE61  LDA #$FF
C0:AE63  STA $0AA4
C0:AE66  STA $0A62
C0:AE69  LDA #$20
C0:AE6B  STA $0A1D
C0:AE6E  LDA #$01
C0:AE70  STA $0EE7
```

初期状態で、

```text
$0A61[0] = 1
$0A61[1] = FF
$0AA3[0] = 1
$0AA3[1] = FF
```

を作っている。slot0/slot1は番兵に近い。

---

### 3-2. `C0:AF33`: object allocate + sorted insert

入口で `A` を `$6B` に保存。

```asm
C0:AF35  STA $6B
C0:AF37  LDA $0AE5
C0:AF3A  CMP #$40
...
C0:AF40  LDA $0AA3,X
C0:AF43  BEQ free_found
```

空slotを探し、`$0AA3` の値を使って挿入位置を探索。

```asm
C0:AF4E  LDA $0AA3,Y
C0:AF51  CMP $6B
C0:AF55  BCS insert_here
C0:AF57  LDA $0A61,Y
C0:AF5A  TAY
C0:AF5B  BRA loop
```

挿入時にnext/prevを更新。

```asm
C0:AF5D  TYA
C0:AF5E  STA $0A61,X      ; new.next = current
C0:AF63  LDX $0A1F,Y
C0:AF66  STA $0A61,X      ; prev.next = new
C0:AF6B  STA $0A1F,X      ; new.prev = prev
C0:AF6F  STA $0A1F,Y      ; current.prev = new
C0:AF72  LDA $6B
C0:AF74  STA $0AA3,X      ; new.sort_key = A
```

その後、object workを初期化。

```asm
STZ $0AE7,X
STZ $0E27,X
STZ $0E67,X
STZ $0EA7,X
STZ $0DA7,X
STZ $0DE7,X
STZ $0CE7,X
LDA $0A1D
STA $0B27,X
LDA #$FF
STA $0D27,X
STA $0D67,X
INC $0AE5
```

解釈:

```text
A = sort key / priority / depth key
戻り = new object handle in X/A系
```

---

### 3-3. `C0:AFAA`: object remove / unlink

対象slot `X` をリストから外す。

```asm
C0:AFD2  STZ $0AA3,X
C0:AFD5  LDY $0A1F,X      ; prev
C0:AFD8  LDA $0A61,X      ; next
C0:AFDB  STZ $0A61,X
C0:AFDE  STA $0A61,Y      ; prev.next = next
C0:AFE1  TAX
C0:AFE2  TYA
C0:AFE3  STA $0A1F,X      ; next.prev = prev
C0:AFE6  DEC $0AE5
```

完全に双方向リストのremove処理。

---

### 3-4. `C0:AFEC`: existing object reorder / sort-key update

既存object `X=$6A+2` をリスト内で移動し、sort keyを更新するroutine。

```asm
C0:AFEE  LDX $6A
C0:AFF0  INX
C0:AFF1  INX
C0:AFF2  STA $1E          ; new sort key
C0:AFF4  LDY $0A61        ; head.next
```

`$0AA3` を比較しながら新しい挿入位置を探す。

```asm
C0:AFF7  LDA $0AA3,Y
C0:AFFA  CMP $1E
C0:AFFC  BCS candidate_position
C0:AFFE  LDA $0A61,Y
C0:B001  TAY
C0:B002  CPY #$01
C0:B004  BNE loop
```

現在位置と違う場合、unlinkして再insert。

```asm
C0:B00F  LDY $0A61,X
C0:B012  LDA $0A1F,X
C0:B015  STA $0A1F,Y
...
C0:B01B  STA $0A61,Y
...
C0:B029  TXA
C0:B02A  STA $0A61,Y
...
C0:B032  STA $0A61,X
C0:B035  LDA $1E
C0:B037  STA $0AA3,X
```

つまり runtimeログでactive_chainが移動中に変わる理由は、このsorterが走っているためと見てよい。

---

### 3-5. `C0:B03D`: active chain walk + OAM build

OAM mirror構築入口。

```asm
C0:B040  LDA #$80
C0:B042  STA $0A1C       ; OAM budget
C0:B045  STZ $1109       ; OAM write index
C0:B048  STZ $110A
C0:B04B  STZ $110B       ; high table index
C0:B04E  LDA #$04
C0:B050  STA $110C
C0:B053  LDX $0A61       ; head.next
```

active chainを辿る。

```asm
loop:
C0:B056  LDA $0AE5,X
C0:B059  BEQ skip_draw
C0:B05B  JSR $B100       ; draw one object
C0:B05E  LDA $0A61,X
C0:B061  TAX
C0:B062  CPX #$02
C0:B064  BCS loop
```

slotが `>=2` のactive objectだけを描画対象にする。  
slot0/slot1は番兵/終端扱い。

描画後、残ったOAMは隠す。

```asm
C0:B094  LDA #$E0
C0:B096  STZ $0EE9,X
C0:B099  STA $0EEA,X
C0:B09C  STZ $0EEB,X
C0:B09F  STZ $0EEC,X
```

つまり hidden entryは、

```text
x=00, y=E0, tile=00, attr=00
```

最後にdirty flag。

```asm
C0:B0C0  LDA #$01
C0:B0C2  STA $0A1B
```

---

### 3-6. `C0:B0C7`: OAM DMA transfer

`$0A1B` が1なら `$0EE9` からOAM DMA。

```asm
C0:B0C7  LDA $0A1B
C0:B0CA  BEQ return
...
C0:B0D5  LDA #$E9
C0:B0D7  STA $4302
C0:B0DA  LDA #$0E
C0:B0DC  STA $4303
...
C0:B0F7  STZ $0A1B
C0:B0FC  STA $420B
```

`$0EE9` をDMA元としてOAMへ流す。

---

## 4. OAM build本体 `C0:B100`

`C0:B100` は1 objectのsprite pieceをOAM mirrorへ出す。

要点:

```text
$0B27,X & 0x0F -> B294 sprite group pointer
$0AE5,X        -> frame index。1-based
$0BA5/$0BE5,X -> X座標
$0C65/$0CA5,X -> Y座標
$0CE5,X        -> vertical anchor / pivot
$0A1C          -> OAM remaining budget
$0EE9..        -> OAM mirror
$10E9..        -> OAM high table mirror
```

実書き込みは以下。

```asm
C0:B228  LDA $06
C0:B22A  STA $0EE9,X     ; x
C0:B22E  LDA $09
C0:B230  DEC
C0:B231  STA $0EE9,X     ; y-1
C0:B235  LDA $0F
C0:B237  STA $0EE9,X     ; tile
C0:B23B  LDA $10
C0:B23D  STA $0EE9,X     ; attr
C0:B247  DEC $0A1C       ; consume OAM budget
```

今回、OAM mirrorの読み順を `x,y,tile,attr` に補正したのは、この静的結果とも一致する。

---

## 5. NPCログとの接続

### 月の神殿ログ

```text
$1569 = 01 only
$0A61 chain = 05->06->...->01->FF
visible slots = s02/s0C/s0D/s0E/s0F
```

これは、script logical actorではなく、visible object層がNPCを出していることを示した。

### はじまりの村ログ

```text
$1569 = 01 0D
$0A61 chain = 長い、移動中に変化
```

`$1569[1]=0D` は銀次/同行actor候補。  
一方、村人・移動NPCは `$0A61` active chain側。  
active_chainが変わるのは `C0:AFEC` のsort-key updateによる並び替えと見て自然。

---

## 6. Goal 13進捗更新

Goal 13は **96% -> 98%** に戻してよい。

理由:

- runtimeログで `$0A61` linked list が見えた
- 静的に `$0A61/$0A1F/$0AA3` が双方向sorted listとして確定寄り
- OAM build `C0:B03D/B100/B0C7` と `$0EE9` DMAまでつながった
- `x,y,tile,attr` のOAM mirror形式も静的とruntimeで一致

残り:

1. `$0AA3` sort key の計算元を全callerで分類する
2. `C0:AFEC` のcallerを列挙して、Y座標/depth順なのか優先度込みなのか確定
3. `$0B27 bit6/0x30/low4bit` の完全定義
4. `$0A1C` 0x80 budgetの単位を「sprite piece 128本」まで確定

---

## 7. 次に攻めるべき静的箇所

1. `C0:AF33` caller列挙  
   - object生成時のsort key `$6B` の意味を分類する
2. `C0:AFEC` caller列挙  
   - active_chain並べ替えのtriggerを確定する
3. `C0:B100` のpiece loopを完全分解  
   - B294 frame定義からOAM 4byte生成まで仕様化する
4. `$0A1C` / `$1109..$110D` のOAM high table処理  
   - OAM high bits / size bitsの格納形式を確定する
