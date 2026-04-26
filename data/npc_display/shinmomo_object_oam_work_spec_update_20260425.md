# 新桃太郎伝説 C0:B100 OAM object work 仕様更新メモ（2026-04-25）

## 目的
`$0BA7/$0C67` 系を object 座標配列として確定するため、`$0CE5,X`、`$0B25,X`、`B294` pointer table、`$0AE5,X` の役割を静的解析で整理した。

## 1. `$0CE5,X` の意味

### OAM builder 内での使用

`C0:B19A..B1A4` では sprite piece のY offsetに対して、object側の `$0CE5,X` を引いてから、object本体のY座標 `$0C65,X/$0CA5,X` を足している。

```asm
C0:B19A  B7 2A        LDA [$2A],Y      ; piece y_offset
C0:B19C  38           SEC
C0:B19D  FD E5 0C     SBC $0CE5,X      ; object vertical anchor / draw origin correction
C0:B1A0  18           CLC
C0:B1A1  7D 65 0C     ADC $0C65,X      ; object Y low
C0:B1A4  85 09        STA $09          ; final Y low
C0:B1A6  A5 21        LDA $21          ; sign extension
C0:B1A8  7D A5 0C     ADC $0CA5,X      ; object Y high/sign/page
```

### 結論
`$0CE5,X` は **sprite anchor / vertical pivot / ground offset** と見るのが最も自然。

- objectの座標が「足元・接地点・基準点」を表す場合、sprite pieceをそのぶん上に描くために使う。
- 正の `$0CE5` は、最終描画Yを上方向へずらす。
- `$0CE5` そのものはsprite heightではなく、**object基準点からsprite描画原点までの補正量**。

### 補強材料

`$0CE5,X` そのもののOAM builder内参照は1箇所だが、slotずれ後の `$0CE7,Y` には複数の書込がある。

| 箇所 | 内容 | 解釈 |
|---|---|---|
| `C0:AF8B` | `STZ $0CE7,X` | object確保時のanchor初期化 |
| `C1:9100` | `LDA #$10; STA $0CE7,Y` | 標準anchor=16px候補 |
| `C1:91D4..91DA` | `$0CE7,X` を反転して `$0CE7,Y` へ | 対称/反転objectのanchor補正 |
| `C1:91FB..91FE` | `$0CE7,X -> $0CE7,Y` | object複製時のanchor継承 |
| `C1:92FE` | `STA $0CE7,Y = 0` | anchor無効化 |
| `C1:9341..9346` | table値または0を `$0CE7` へ | 状態/揺れ/形状差によるanchor変更 |

## 2. `$0B25,X` のbit定義

`C0:B119..B127` と `C0:B1F3..B1F7` から、最低限以下まで切れる。

| bit | mask | 意味 | 根拠 |
|---:|---:|---|---|
| 0-3 | `0x0F` | sprite definition group index | `AND #$0F` 後、`group*3` で `B294` pointer table を引く |
| 4-5 | `0x30` | object-level OAM attribute overlay | `AND #$30` してOAM attr `$10` に `TSB` |
| 6 | `0x40` | object draw skip / OAM出力抑制 | `BIT #$40` が立つと即 `JMP $B25C` |
| 7 | `0x80` | このOAM builderでは未使用 | `C0:B100` 直接経路では参照なし |

### 注意
`$0B25,X` はOAM builder側の見え方。object allocator / animation側ではslot indexが2ずれるため、同じslotの論理フィールドは `$0B27,Y` として触られる箇所がある。

## 3. `B294` pointer table

`C0:B294` はコードではなく、**16本の3バイトlong pointer table**。
`$0B25,X & 0x0F` でgroupを選び、`group*3` でこの表を引く。

```asm
C0:B125  29 0F        AND #$0F
C0:B127  85 00        STA $00
C0:B129  0A           ASL A
C0:B12A  65 00        ADC $00       ; group * 3
C0:B12C  A8           TAY
C0:B12F  B9 94 B2     LDA $B294,Y   ; pointer low/mid
C0:B136  B9 96 B2     LDA $B296,Y   ; pointer bank
```

### 16 group summary

| group | pointer | first frame ptr | first frame piece count | first 8 frame ptrs |
|---:|---|---|---:|---|
| 0 | `C5:183A` | `C5:1AF8` | 2 | `C5:1AF8 C5:1B05 C5:1B92 C5:1BF3 C5:1C30 C5:1C4D C5:1C7E C5:1CAF` |
| 1 | `C5:374F` | `C5:387D` | 10 | `C5:387D C5:38A6 C5:38D7 C5:3910 C5:3955 C5:39A2 C5:39EF C5:3A3C` |
| 2 | `C1:0000` | `C1:03B6` | 2 | `C1:03B6 C1:03BF C1:03C8 C1:03D1 C1:03DA C1:03DF C1:03E4 C1:03ED` |
| 3 | `C1:19D3` | `C1:1D5B` | 1 | `C1:1D5B C1:1D60 C1:1D65 C1:1D6A C1:1D6F C1:1D74 C1:1D79 C1:1D7E` |
| 4 | `C1:2BD3` | `C1:2F09` | 1 | `C1:2F09 C1:2F0E C1:2F13 C1:2F18 C1:2F1D C1:2F22 C1:2F27 C1:2F2C` |
| 5 | `C1:3E68` | `C1:41CE` | 1 | `C1:41CE C1:41D3 C1:41D8 C1:41E5 C1:41EA C1:41EF C1:41FC C1:4201` |
| 6 | `C1:62CB` | `C1:6585` | 1 | `C1:6585 C1:658A C1:658F C1:6594 C1:6599 C1:659E C1:65A3 C1:65A8` |
| 7 | `C5:462C` | `C5:48F6` | 1 | `C5:48F6 C5:490B C5:4910 C5:4915 C5:4926 C5:4937 C5:4948 C5:4959` |
| 8 | `C2:50B1` | `C2:531B` | 5 | `C2:531B C2:5330 C2:534D C2:535A C2:535F C2:53AC C2:53F1 C2:53F6` |
| 9 | `C2:5EF7` | `C2:6061` | 1 | `C2:6061 C2:6066 C2:606F C2:6084 C2:60A9 C2:60AE C2:60B3 C2:60B8` |
| 10 | `C2:0000` | `C2:01A8` | 6 | `C2:01A8 C2:01CD C2:01F2 C2:020B C2:0224 C2:022D C2:023C C2:0261` |
| 11 | `C2:1C10` | `C2:1E32` | 18 | `C2:1E32 C2:1E7B C2:1EC4 C2:1F0D C2:1F96 C2:201F C2:20A8 C2:20D9` |
| 12 | `C3:0C01` | `C3:0D99` | 28 | `C3:0D99 C3:0E0A C3:0E8B C3:0F08 C3:0FA1 C3:0FEA C3:104B C3:10AC` |
| 13 | `C3:3830` | `C3:3904` | 38 | `C3:3904 C3:39A1 C3:3A02 C3:3A63 C3:3AC4 C3:3B25 C3:3B86 C3:3BE7` |
| 14 | `C5:086F` | `C5:08DB` | 33 | `C5:08DB C5:0960 C5:09FD C5:0AB6 C5:0B7F C5:0C40 C5:0D65 C5:0DCA` |
| 15 | `C5:1A08` | `C5:1B01` | 1 | `C5:1B01 C5:1C24 C5:1C28 C5:1C49 C5:1EFE C5:1F0A C5:1F18 C5:1FBA` |


### frame definition format

frame tableは2バイトpointer列で、`$0AE5,X - 1` をframe indexとして引く。

```asm
C0:B13B  BD E5 0A     LDA $0AE5,X
C0:B13E  3A           DEC A
C0:B144  0A           ASL A
C0:B146  B7 2A        LDA [$2A],Y   ; frame pointer
```

frame本体は以下の形。

```text
[count]
[piece0: flags, x_offset, y_offset, tile]
[piece1: flags, x_offset, y_offset, tile]
...
```

pieceの4バイトはOAM builderで次のように使われる。

| piece byte | 役割 |
|---:|---|
| +0 | piece flags / attr bits / sign extension flags |
| +1 | X offset |
| +2 | Y offset |
| +3 | tile low |

外部化ファイル:
- `shinmomo_B294_sprite_groups_summary_20260425.csv`
- `shinmomo_B294_sprite_frame_piece_sample_20260425.csv`

## 4. `$0AE5,X` の意味

`$0AE5,X` は **1-based animation frame / pattern index**。

- `0` の場合、`C0:B056` で描画処理を呼ばない。
- `1` 以上の場合、`DEC` して0-based化し、frame pointer tableを引く。
- そのframe定義のpiece countをOAM残枠 `$0A1C` と比較する。

```asm
C0:B056  BD E5 0A     LDA $0AE5,X
C0:B059  F0 03        BEQ $B05E      ; frame=0なら描画しない
C0:B05B  20 00 B1     JSR $B100
...
C0:B13B  BD E5 0A     LDA $0AE5,X
C0:B13E  3A           DEC A          ; 1-based -> 0-based
```

### animation runnerとの接続
`C0:AE94` 系は `$0B27` の下位groupから `B2C1` 側のanimation script tableを引き、scriptの結果として `$0AE7,X` と `$0E67,X` を更新する。
slotずれを考慮すると、OAM builderが `$0AE5,X` として読む値は、object側から見た現在frame/pattern indexである。

## 5. Goal 13 への反映

今回、NPC/ object大量表示軽減の後段は以下まで仕様化できた。

```text
active list $0A61
  -> object slot X
  -> $0B25,X group/attr/skip
  -> $0AE5,X frame index
  -> B294 group pointer
  -> frame pointer table
  -> sprite piece list
  -> $0BA5/$0C65 座標 + piece offset - $0CE5 anchor
  -> screen clipping
  -> OAM lower/high buffer
  -> dirty時だけDMA
```

## 更新進捗

| Goal | 旧 | 新 | 理由 |
|---:|---:|---:|---|
| 13. NPC大量表示時の処理軽減ロジック | 58% | 66% | 座標・anchor・group・frame・OAM抑制の仕様が一本化した |
| 11. 外部データ化 | 95% | 96% | `B294` group summary と frame piece sample をCSV化 |
| 12. 全体構造の人間可読化 | 97% | 98% | object workからOAMまでの構造説明が一段明確化 |

## 次に攻めるべき箇所

1. `B2C1` animation script pointer table を外部化し、`$0AE5/$0E67/$0EA7` の更新仕様を確定する。
2. `$0D25,X` の意味を詰める。piece flagsの`0x06`と加算され、OAM attrのpalette/priority系に入っている。
3. `0x40 draw skip bit` をセットする上流を探し、表示抑制が「画面外」「状態」「負荷制御」のどれで発火するかを分離する。
4. active list `$0A61/$0A1F/$0AA3` の優先順位・ソート規則を詰める。
