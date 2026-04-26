# 新桃太郎伝説 B2C1 animation script pointer table 外部化メモ（2026-04-25）

## 0. 重要な補正

`C0:B2C1` は、`C0:B294` sprite definition group table の末尾エントリでもあり、同時に `C0:AE94` から参照される **animation script pointer table** の先頭でもある。

つまり、ここは **overlap table** として扱うのが正しい。

```asm
C0:AE99  B9 27 0B     LDA $0B27,Y
C0:AE9C  29 0F        AND #$0F
C0:AE9E  85 00        STA $00
C0:AEA0  0A           ASL A
C0:AEA1  65 00        ADC $00       ; group * 3
C0:AEA3  AA           TAX
C0:AEA6  BD C1 B2     LDA $B2C1,X   ; low/high
C0:AEAD  BD C3 B2     LDA $B2C3,X   ; bank
```

## 1. tableの役割

`$0B27,Y & 0x0F` で animation group を選ぶ。

`C0:B2C1 + group*3` から 24bit pointer を取り、その先を **state number -> script pointer table** として使う。

その後、

```asm
C0:AEB4  B9 27 0E     LDA $0E27,Y
C0:AEC1  3A           DEC A
C0:AEC2  0A           ASL A         ; state index * 2
C0:AECD  B7 2A        LDA [$2A],Y   ; script pointer
C0:AED3  BC A7 0E     LDY $0EA7,X   ; script cursor
C0:AED6  B7 2D        LDA [$2D],Y   ; frame/pattern
C0:AED8  9D E7 0A     STA $0AE7,X
C0:AEDC  B7 2D        LDA [$2D],Y+1 ; duration
C0:AEDE  9D 67 0E     STA $0E67,X
```

となる。

## 2. script形式

script本体は原則として2バイト単位。

```text
[frame_or_pattern, duration]
[frame_or_pattern, duration]
...
[00, 00]  ; 終端 / ループ戻り候補
```

`C0:AF0C` 側では、`$0E67` が0になると `$0EA7 += 2` して次pairへ進む。  
次pairのdurationが0だった場合、`$0EA7` を0へ戻して再取得するため、`00 00` は **script終端/ループ戻り** と見てよい。

## 3. top-level table

| group | entry | bytes | script pointer table | 推定state数 | first script | first script pair preview | note |
|---:|---|---|---|---:|---|---|---|
| 0 | `C0:B2C1` | `08 1A C5` | `C5:1A08` | 120 | `C5:1B01` | `01:01 00:00` | overlaps B294 group15 pointer |
| 1 | `C0:B2C4` | `41 38 C5` | `C5:3841` | 30 | `C5:3CF4` | `01:03 02:03 03:03 04:03 05:03 06:03 07:03 08:03 09:03 0A:03 0B:03 0C:03 0D:03 0E…` |  |
| 2 | `C0:B2C7` | `F2 01 C1` | `C1:01F2` | 229 | `C1:0436` | `01:20 02:20 00:00` |  |
| 3 | `C0:B2CA` | `63 1B C1` | `C1:1B63` | 253 | `C1:1D83` | `01:10 02:10 00:00` |  |
| 4 | `C0:B2CD` | `AD 2D C1` | `C1:2DAD` | 174 | `C1:2F99` | `05:05 01:05 02:05 03:05 04:05 07:05 08:05 09:05 08:05 07:05 04:05 06:05 04:05 03…` |  |
| 5 | `C0:B2D0` | `62 40 C1` | `C1:4062` | 182 | `C1:41DD` | `01:0A 02:0A 03:0A 00:00` |  |
| 6 | `C0:B2D3` | `93 64 C1` | `C1:6493` | 122 | `C1:65F7` | `01:10 02:10 00:00` |  |
| 7 | `C0:B2D6` | `1A 48 C5` | `C5:481A` | 110 | `C5:48FB` | `01:10 00:00` |  |
| 8 | `C0:B2D9` | `65 52 C2` | `C2:5265` | 92 | `C2:53C9` | `05:02 02:02 01:02 06:03 01:05 02:02 06:05 01:03 05:01 02:01 05:01 00:05 02:02 00…` |  |
| 9 | `C0:B2DC` | `2F 60 C2` | `C2:602F` | 25 | `C2:6198` | `11:04 02:04 17:04 04:04 0B:02 0C:02 05:02 06:02 0D:02 0E:02 07:02 08:02 0F:02 10…` |  |
| 10 | `C0:B2DF` | `2C 01 C2` | `C2:012C` | 62 | `C2:01C1` | `01:FF 00:00` |  |
| 11 | `C0:B2E2` | `8A 1D C2` | `C2:1D8A` | 87 | `C2:23EA` | `01:FF 00:00` |  |
| 12 | `C0:B2E5` | `1B 0D C3` | `C3:0D1B` | 63 | `C3:0F85` | `01:30 02:07 01:07 02:07 01:07 02:07 00:00` |  |
| 13 | `C0:B2E8` | `C4 38 C3` | `C3:38C4` | 33 | `C3:399D` | `01:FF 00:00` |  |
| 14 | `C0:B2EB` | `B5 08 C5` | `C5:08B5` | 19 | `C5:0D15` | `01:FF 00:00` |  |
| 15 | `C0:B2EE` | `00 00 00` | `00:0000` | 0 | `` | `` | NULL terminator/no group |

※ 推定state数は「連続して `00 00` 終端を持つscript pointerとして読める数」を機械的に数えたもの。  
呼び出し側の `$0E27` が有効範囲を保証しているはずなので、ここでは **実使用数の上限候補** として扱う。

## 4. $0AE7 / $0E67 / $0EA7 の意味更新

| WRAM | 役割 | 更新元 |
|---|---|---|
| `$0B27,Y & 0x0F` | animation/script group index | object生成時の種別 |
| `$0E27,Y` | animation state number, 1-based | `C0:AE88` など |
| `$0EA7,Y` | script cursor / byte offset | `C0:AF0C` が2ずつ進める |
| `$0AE7,Y` | current frame / pattern index | script pair 1バイト目 |
| `$0E67,Y` | current frame duration / wait counter | script pair 2バイト目 |

OAM builderが読む `$0AE5,X` は、slotずれを含めてこの `$0AE7,Y` 系の現在frame値に接続する。

## 5. Goal 13への反映

今回で、object表示系は以下まで接続できた。

```text
$0B27 lower nibble
  -> C0:B2C1 animation group table
  -> state pointer table
  -> frame/duration script
  -> $0AE7 current frame
  -> $0E67 duration counter
  -> $0EA7 script cursor
  -> OAM builderのframe selection
  -> B294 sprite frame definition
  -> OAM書込 / 画面外clip / 表示抑制
```

これにより、NPC大量表示軽減に関係する「動いているobjectだけ、必要なframeだけ、OAMへ流す」後段仕様がさらに明確になった。

## 6. 出力ファイル

- `shinmomo_B2C1_animation_top_table_20260425.csv`
- `shinmomo_B2C1_animation_state_scripts_20260425.csv`

## 7. 次に攻める箇所

1. `$0E27,Y` をセットするcallerを列挙し、animation state numberの意味を割り当てる。
2. `$0B27,Y` の上位bitと下位groupの両方を、object種別ごとに対応づける。
3. `$0AE7 -> $0AE5` のslotずれを、実際のactive list indexで再確認する。
4. `B294` sprite frame definition と `B2C1` animation script の frame number が同じ番号空間を使っているかを検証する。
