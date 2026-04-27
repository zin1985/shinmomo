# 新桃太郎伝説 静的解析メモ: `0x03F09A / 0x03F0DB / 0x03F0C6 / 0x03F0CD / 0x03F0D4` continuation runner 切り分け

作成日: 2026-04-24

## 目的

`0x039847..0x0399E4` の A/B 系 9バイト record 末尾に出てくる `next=F09A / F0DB / F0C6 / F0CD / F0D4` を、continuation runner / sub-blob として静的に切る。

本メモでは ROM file offset を主表記とし、必要に応じて LoROM 風に `C7:Fxxx` と併記する。

---

## 1. 結論

今回の最大の成果は、`F0C6 / F0CD / F0D4` が独立した3本のrunnerではなく、**途中入口を持つ階段型 continuation** として読めたこと。

```text
C7:F0C6 -> C7:F0CD -> C7:F0D4 -> C7:F0DB -> C7:F0F9 helper -> end
```

`0x0399CA / 0x0399D3 / 0x0399DC` の B系末尾例外 record は、それぞれこの階段の途中に入る。

| record | ROM offset | id | cmd | val | next | 実行される追加setup |
|---:|---|---:|---:|---:|---|---|
| B例外1 | `0x0399CA` | `19` | `35` | `0x0A1C` | `F0C6` | 3本すべて |
| B例外2 | `0x0399D3` | `1A` | `35` | `0x0F2B` | `F0CD` | 後ろ2本 |
| B例外3 | `0x0399DC` | `1B` | `35` | `0x1134` | `F0D4` | 後ろ1本 |

つまり、B系の `id=19/1A/1B` は通常の `F0DB` 直行ではなく、必要な追加setupを積んでから `F0DB` 共通後段へ入る構造。

---

## 2. `0x03F09A` = A系 common continuation

### 範囲

```text
ROM offset : 0x03F09A..0x03F0B0
LoROM風   : C7:F09A..C7:F0B0
```

### bytecode切り

```text
C7:F09A: 07 20 01 A0 00
C7:F09F: 0B EC FF
C7:F0A2: 15 0A
C7:F0A4: 22 2F FC
C7:F0A7: 15 0A
C7:F0A9: 22 30 FC
C7:F0AC: 15 78
C7:F0AE: 15 78
C7:F0B0: 37
```

### 解釈

- A系 `cmd=32/35` record群の共通後段。
- 末尾 `37` をこのVM/bytecode内の block end / return 系と見る。
- 直後の `C7:F0B1` は別 continuation 入口であり、`F09A` の一部として流し込まない方が安全。

---

## 3. 参考: `0x03F0B1` は隣接する別 continuation

今回ユーザー指定範囲ではないが、誤って `F09A` の続きに含めやすいため分離しておく。

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

`0x0399E5` 付近の `next=F0B1` record から入る別系統 continuation と見る。

---

## 4. `0x03F0C6 / 0x03F0CD / 0x03F0D4` = 階段型 setup chain

### `C7:F0C6` entry

```text
C7:F0C6: 07 78 FF AC 00
C7:F0CB: 33 17
```

この後、終端せず `C7:F0CD` へ落ちる。

### `C7:F0CD` entry

```text
C7:F0CD: 07 88 FF AC 00
C7:F0D2: 33 10
```

この後、終端せず `C7:F0D4` へ落ちる。

### `C7:F0D4` entry

```text
C7:F0D4: 07 98 FF AC 00
C7:F0D9: 33 09
```

この後、終端せず `C7:F0DB` へ落ちる。

### 解釈

3本とも形式が同じ。

```text
07 <lo> <hi> AC 00 33 <imm>
```

候補意味:

- `07 xx xx AC 00` = 何らかのslot / work / source指定
- `33 imm` = 即値/小分類/表示値/条件値を積む、または該当slotへ書く
- `78 FF / 88 FF / 98 FF` は連続する3つのwork領域候補
- `17 / 10 / 09` は id=19/1A/1B 系で追加される段階値または補正値候補

重要なのは、entry位置により実行本数が変わること。

```text
next=F0C6: 17,10,09 をすべて積む
next=F0CD: 10,09 のみ積む
next=F0D4: 09 のみ積む
```

このため `F0C6/CD/D4` は「個別runner」ではなく、**残りsetup数を入口で調整する階段型 continuation** と見る。

---

## 5. `0x03F0DB` = B系 common postlude

### 範囲

```text
ROM offset : 0x03F0DB..0x03F0F8
LoROM風   : C7:F0DB..C7:F0F8
```

### bytecode切り

```text
C7:F0DB: 07 80 FF 9E 00
C7:F0E0: 35 F9 F0
C7:F0E3: 0B 40 00
C7:F0E6: 20 08
C7:F0E8: 15 80
C7:F0EA: 29 2F FC
C7:F0ED: 25 57 03 01
C7:F0F1: 0B 00 00
C7:F0F4: 15 F0
C7:F0F6: 33 FD
C7:F0F8: 37
```

### `35 F9 F0` の意味

`35 F9 F0` は、直後の native helper らしき `C7:F0F9` を呼ぶ命令候補。

`35 F9 F0` はROM全体検索でもこの位置だけで、`C7:F0F9` は以下のように 65816 native routine としてかなり自然に見える。

```text
C7:F0F9: DA          ; PHX
C7:F0FA: 8A          ; TXA
C7:F0FB: 29 03       ; AND #$03
C7:F0FD: AA          ; TAX
C7:F0FE: BD 06 F1    ; LDA $F106,X
C7:F101: 99 A7 0B    ; STA $0BA7,Y
C7:F104: FA          ; PLX
C7:F105: 60          ; RTS
```

したがって `C7:F0DB` は、B系の共通postludeとして

1. work/slot指定
2. native helper `F0F9` 呼び出し
3. 後続の固定bytecode処理
4. `37` で終了

という流れに見える。

---

## 6. record列との接続

### A系

A系 `0x039847..0x039914` は基本的に `next=F09A`。

```text
38 05 01 <id> <cmd> <val_lo> <val_hi> 9A F0
```

A系は、個別recordの `id/cmd/val` を読んだ後、`C7:F09A` の共通後段へ進む。

### B系通常

B系 `0x039916..0x0399C8` の通常recordは `next=F0DB`。

```text
38 05 01 <id> <cmd> <val_lo> <val_hi> DB F0
```

B系はA系と同じid並びを持ち、`val` がA系+1になっている箇所が多い。

### B系末尾例外

B系末尾の `id=19/1A/1B` は `op=37` かつ `cmd=35` になり、`F0C6/CD/D4` 階段に入る。

```text
0x0399CA: 37 05 01 19 35 1C 0A C6 F0
0x0399D3: 37 05 01 1A 35 2B 0F CD F0
0x0399DC: 37 05 01 1B 35 34 11 D4 F0
```

これにより、B系末尾だけ通常postludeの前に追加setupが入る。

---

## 7. 認識変更

### 修正したこと

- `F09A` を `F0C5` まで一続きにしない。
  - `F09A..F0B0` と `F0B1..F0C5` は別continuationとして分離。
- `F0C6 / F0CD / F0D4` を別々のrunnerではなく、階段型の途中入口として整理。
- `F0DB` の中に `35 F9 F0` による native helper呼び出し候補を確認。
- B系末尾 `id=19/1A/1B` の特別扱いを説明可能にした。

### まだ未確定なこと

- opcode `07 / 0B / 15 / 20 / 22 / 25 / 29 / 33 / 35 / 37` の正式意味。
- `78FF / 88FF / 98FF / 80FF` が指すwork領域の正体。
- `33 17 / 33 10 / 33 09 / 33 FD` の値が、表示値、条件値、slot番号、分類値のどれか。
- native helper `C7:F0F9` が `$0BA7,Y` に入れる値の意味。

---

## 8. 進捗更新案

| Goal | 旧 | 新 | 理由 |
|---:|---:|---:|---|
| 8. 条件分岐ディスパッチ系 | 74% | 76% | continuationの入口/終端/階段構造が読めた |
| 9. 会話・店・イベントスクリプト仕様書 | 93% | 94% | target-side blobの制御構造を仕様化できるようになった |
| 11. 外部データ化 | 91% | 92% | A/B record列と next runner を表として外部化可能 |
| 12. 全体構造の人間可読化 | 93% | 94% | `0x398xx/0x399xx` blobを説明しやすくなった |

13目標平均は概算で約73.8〜74.0%。

---

## 9. 次に静的で攻める場所

1. `C7:F0F9` helperが参照する `C7:F106` tableを切る。
2. `$0BA7,Y` の他書込箇所を逆引きし、`F0F9` helperの意味を確定する。
3. `07 xx xx` のxx候補、特に `FF78/FF88/FF98/FF80` をROM/WRAM参照として逆引きする。
4. `35 50 F1` / `35 07 F2` も同じ「bytecodeからnative helper呼び出し」形式か確認する。
5. `0x0399E5` 以降の `next=F0B1 / F11D / F136` も同じ粒度で切る。
