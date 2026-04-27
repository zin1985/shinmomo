# 新桃太郎伝説 静的解析メモ: C7:F0xx continuation deep cut（2026-04-24）

## 対象
ユーザー指定の5点を静的解析で確認した。

1. `C7:F0F9` helper が参照する `C7:F106` table
2. `$0BA7,Y` の他書込箇所
3. `FF78 / FF88 / FF98 / FF80` が WRAM/VM work領域なのか
4. `35 50 F1 / 35 07 F2` も同じ native helper 呼び出し形式か
5. `0x0399E5` 以降の `next=F0B1 / F11D / F136` continuation 切り

---

## 1. C7:F0F9 helper と C7:F106 table

### helper 本体

ROM `0x03F0F9`:

```asm
C7:F0F9  DA          PHX
C7:F0FA  8A          TXA
C7:F0FB  29 03       AND #$03
C7:F0FD  AA          TAX
C7:F0FE  BD 06 F1    LDA $F106,X
C7:F101  99 A7 0B    STA $0BA7,Y
C7:F104  FA          PLX
C7:F105  60          RTS
```

### table

ROM `0x03F106`:

```text
C7:F106: 48 68 88 A8
```

### 解釈

`X & 0x03` により4値から1つを取り、`$0BA7,Y` に格納する小helper。

| index | value | dec |
|---:|---:|---:|
| 0 | `0x48` | 72 |
| 1 | `0x68` | 104 |
| 2 | `0x88` | 136 |
| 3 | `0xA8` | 168 |

値が 32 刻みで横方向に並んでいるため、`$0BA7,Y` は **actor/object/sprite work のX座標系フィールド** である可能性が高い。

---

## 2. `$0BA7,Y` の他書込箇所

ROM全体では `STA $0BA7,Y` が多いが、今回の C7 continuation 系で重要なのは以下。

| ROM | SNES | 内容 |
|---|---|---|
| `0x0392FF` | `C7:92FF` | object slot初期化。`A9 80 -> STA $0BA7,Y` |
| `0x039ECB` | `C7:9ECB` | `$0BA7,Y -= $11B4,X` 系。座標更新/移動 |
| `0x039EE8` | `C7:9EE8` | `$0BA7,Y += $11B4,X` 系。座標更新/移動 |
| `0x039F2D` | `C7:9F2D` | linked/source slotから座標加算して `$0BA7,Y` |
| `0x03EA61` | `C7:EA61` | `0x60 + index` 系の初期値設定 |
| `0x03F081` | `C7:F081` | table `F091` から `$0BA7/Y`, `$0C67/Y`, `$0CA7/Y` へ |
| `0x03F101` | `C7:F101` | `F106` 4値tableから `$0BA7,Y` へ |
| `0x03F1A0` | `C7:F1A0` | dynamic値 `0x70 + $150C - 1` を `$0BA7,Y` へ |
| `0x03F1EC` | `C7:F1EC` | table `F1F7` から `$0BA7/Y`, `$0C67/Y` へ |
| `0x03F24B` | `C7:F24B` | table `F262` から `$0BA7`, `$0BE7`, `$0C67`, `$0CA7` へ |
| `0x03F307` | `C7:F307` | table `F31E` から `$0BA7`, `$0BE7`, `$0C67`, `$0CA7` へ |
| `0x03F62C` | `C7:F62C` | table `F637` から `$0BA7/Y`, `$0C67/Y` へ |

### 結論

`$0BA7,Y` は単独の特殊フラグではなく、`$0B67 / $0BA7 / $0BE7 / $0C27 / $0C67 / $0CA7` と並ぶ **object/sprite/actor work の並列配列** の1フィールド。

特に以下から、X座標またはX座標に近い表示位置フィールドと見るのが自然。

- 初期化で `0x80` が入る
- `+/- velocity/delta` で更新される
- helper tableが `48/68/88/A8` の横並び値を入れる
- 他のhelperでは `$0C67,Y` と対で更新される

---

## 3. `FF78 / FF88 / FF98 / FF80` の正体

該当continuation:

```text
C7:F0C6: 07 78 FF AC 00 33 17
C7:F0CD: 07 88 FF AC 00 33 10
C7:F0D4: 07 98 FF AC 00 33 09
C7:F0DB: 07 80 FF 9E 00 ...
```

`07` command は、周辺例から **2つの16bit immediateを取るVM命令** と見てよい。

```text
07 <x_lo> <x_hi> <y_lo> <y_hi>
```

| bytes | 16bit signed | dec | 対になる値 |
|---|---:|---:|---|
| `78 FF` | `0xFF78` | -136 | `0x00AC` = 172 |
| `88 FF` | `0xFF88` | -120 | `0x00AC` = 172 |
| `98 FF` | `0xFF98` | -104 | `0x00AC` = 172 |
| `80 FF` | `0xFF80` | -128 | `0x009E` = 158 |

### 結論

これは WRAM/VM work 領域アドレスではなく、**signed座標 immediate** と見るべき。

理由:

- `07 20 01 A0 00` = `(0x0120, 0x00A0)` のような座標ペアが同じ命令形で出る
- `07 80 01 60 00` = `(0x0180, 0x0060)` も同型
- `FF78/FF88/FF98/FF80` は signed で画面外左側の座標として自然
- 直後に `$0BA7,Y` や `$0C67,Y` へ座標値を入れるhelperが多い

よって、`F0C6/F0CD/F0D4/F0DB` は **画面外または左側から出すobject setup** である可能性が高い。

---

## 4. `35 50 F1 / 35 07 F2` の性質

### `35 F9 F0`

既知:

```text
C7:F0E0: 35 F9 F0
```

これは `C7:F0F9` の native helper を呼ぶ形としてかなり強い。

### `35 50 F1`

`C7:F136` continuation 内に出る。

```text
C7:F13F: 2F FA
C7:F141: 35 50 F1
```

target `C7:F150` は native code。

```asm
C7:F150  DA             PHX
C7:F151  22 77 ED 84    JSL $84ED77
...
C7:F1A0  99 A7 0B       STA $0BA7,Y
...
C7:F1B7  60             RTS
```

内部で `$0BA7,Y` / `$0C67,Y` を設定するため、`35 50 F1` は **native helper call** と見てよい。

### `35 07 F2`

`C7:F1D0` continuation 内に出る。

```text
C7:F1D9: 35 07 F2
```

target `C7:F207` も native code。

```asm
C7:F207  5A          PHY
C7:F208  8A          TXA
C7:F209  29 07       AND #$07
C7:F20B  0A          ASL
C7:F20C  A8          TAY
C7:F20D  B9 1B F2    LDA $F21B,Y
C7:F210  9D E4 11    STA $11E4,X
C7:F213  B9 1C F2    LDA $F21C,Y
C7:F216  9D F4 11    STA $11F4,X
C7:F219  7A          PLY
C7:F21A  60          RTS
```

### 結論

`35 <lo> <hi>` は少なくともこのC7:F0xx系では、**bytecodeから同bank native helperを呼ぶ命令** として扱える。

ただし `35 11 30` のように `Fxxx` でない値もあるため、全 `35` を無条件にnative callとは断定しない。  
`target` が `C7:Fxxx` で、先頭が native prologue (`DA`/`5A` など) かつ `60 RTS` 終端なら native helper call と判定する。

---

## 5. `0x0399E5` 以降の continuation 切り

### record 1: `next=F0B1`

ROM `0x0399E5`:

```text
0C 05 04 26 35 3B 00 B1 F0
```

推定:

| field | value |
|---|---|
| op/class | `0C` |
| p1,p2,p3 | `05 04 26` |
| cmd | `35` |
| value | `003B` |
| next | `F0B1` |

#### C7:F0B1 continuation

```text
C7:F0B1: 07 80 01 60 00
C7:F0B6: 0B 70 FF
C7:F0B9: 15 0A
C7:F0BB: 22 2F FC
C7:F0BE: 15 0A
C7:F0C0: 22 30 FC
C7:F0C3: 15 40
C7:F0C5: 37
```

`F0B1..F0C5` で完結。  
`F0C6` へ落ちない。

### record 2: `next=F11D`

ROM `0x0399EE`:

```text
10 00 41 45 31 16 00 1D F1
```

推定:

| field | value |
|---|---|
| op/class | `10` |
| p1,p2,p3 | `00 41 45` |
| cmd | `31` |
| value | `0016` |
| next | `F11D` |

#### C7:F11D continuation

```text
C7:F11D: 07 80 00 20 01
C7:F122: 15 01
C7:F124: 0C 00 FE
C7:F127: 15 50
C7:F129: 0C 00 00
C7:F12C: 15 01
C7:F12E: 21 35 11
C7:F131: 30 FA
C7:F133: 15 20
C7:F135: 37
```

`F11D..F135` で完結。  
中に `35` byte は見えるが、`21 35 11` と読む方が自然で、`35 11 30` call と断定しない。

### record 3: `next=F136`

ROM `0x0399F7`:

```text
2C 05 01 2F 17 54 00 36 F1
```

推定:

| field | value |
|---|---|
| op/class | `2C` |
| p1,p2,p3 | `05 01 2F` |
| cmd | `17` |
| value | `0054` |
| next | `F136` |

#### C7:F136 continuation

```text
C7:F136: 07 70 00 7F 00
C7:F13B: 15 01
C7:F13D: 21 DE 00
C7:F140: 2F FA
C7:F142: 35 50 F1
C7:F145: 15 01
C7:F147: 21 DE 00
C7:F14A: 30 F7
C7:F14C: 14 03 80
C7:F14F: 37
```

`F136..F14F` で完結。  
途中の `35 50 F1` で `C7:F150` native helper を呼ぶ。

---

## 6. 今回の認識更新

### 確度が上がった点

- `C7:F0F9` は `X&3 -> [48,68,88,A8] -> $0BA7,Y` の小helper。
- `$0BA7,Y` は actor/object/sprite work の座標系フィールド。
- `FF78/FF88/FF98/FF80` はWRAMアドレスではなく、signed座標 immediate。
- `35 F9 F0 / 35 50 F1 / 35 07 F2` は、C7 bytecode から C7 native helper を呼ぶ形式としてかなり強い。
- `F0B1/F11D/F136` はそれぞれ `37` で終わる独立 continuation。

### 注意点

- `35` opcodeすべてを native helper call と見るのは危険。
- `35 11 30` に見える箇所は、実際には `21 35 11 / 30 FA` のように切れる可能性が高い。
- `$0BA7,Y` は座標系と見て強いが、最終的な画面X/Yのどちらかは `$0C67,Y` などとの対照が必要。

---

## 7. 進捗更新案

| Goal | 旧 | 新 | 理由 |
|---:|---:|---:|---|
| 8. 条件分岐ディスパッチ系 | 76% | 79% | continuation runner と native helper call の粒度が上がった |
| 9. 会話・店・イベントスクリプト仕様書 | 94% | 95% | C7 target-side bytecodeの切り方が具体化 |
| 11. 外部データ化 | 92% | 93% | C7 record/continuation/helper/table を台帳化可能に |
| 12. 全体構造の人間可読化 | 94% | 95% | target-side blob → continuation → object setup の説明力が上がった |

