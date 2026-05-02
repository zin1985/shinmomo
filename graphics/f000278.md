# 新桃太郎伝説 解析 vol016 戦闘グラフィック静的解析メモ（2026-05-01）

## 結論

戦闘ログの白黒CHRはかなり有効。  
ただし `vram.bin` 内の戦闘CHRは、ROM上に **SNES 4bpp/2bppタイルとしてそのまま直置きされていない**。

今回の静的サーチ結果:

| 対象 | 解釈 | chunk | ROM exact match |
|---|---|---:|---:|
| battle current `vram.bin` | 4bpp tile | 32 bytes | 0 |
| battle current `vram.bin` | 2bpp tile | 16 bytes | 0 |

このため、次の本線は `vram.bin` の直接一致検索ではなく、**asset decoder / DMA queue builder / DA:3800 stream 系を追うこと**。

## 静的に進んだ点

### 1. `DA:3800` はグリフ・小型ビットマップ資材の入口としてかなり濃い

既存の `shinmomo_da3800_streams_decoded_records_20260314.csv` を再レンダリングしたところ、stream 1 は数字・記号・かなり小さいグリフ資材として自然に見える。

- `DA:3800` pointer table operand は ROM raw `0x04A9B5` に1件だけ出現。
- 周辺コードは `BF 00 38 DA` / `BF 01 38 DA` で、`DA:3800 + X` から16bit pointerを引いている。
- 直後に `$2A/$2B/$2C` に long pointer を作り、`A7 2A` で stream header を読んでいる。

該当コード近傍:

```asm
raw 04A9B1:
A5 07        ; stream id系?
3A           ; DEC
0A           ; *2
AA           ; TAX
BF 00 38 DA  ; load low from DA:3800 + X
85 2A
BF 01 38 DA  ; load high
85 2B
A9 DA
85 2C        ; long ptr = DA:xxxx
A7 2A        ; read stream header
```

### 2. `C4:AA6D` 近傍が VRAM転送キュー投入に近い

`raw 0x04AA7D` 近辺では、`7E:394B / 7E:397B` から値を読み、`80:A151 / 80:A170 / 80:A185` を呼ぶ。

```asm
raw 04AA7D:
22 51 A1 80  ; JSL $80:A151
A2 00
BF 4B 39 7E  ; read 7E:394B,X
85 06
BF 7B 39 7E  ; read 7E:397B,X
85 07
22 70 A1 80  ; JSL $80:A170
...
22 85 A1 80  ; JSL $80:A185
```

これは「DA stream decode → 7E:390B/394B/397B 系 staging → VRAM queue」の線としてかなり強い。

### 3. `A151/A170/A185` 呼び出しは bank C0/C2/C3/C4 に分布

静的参照数:

| pattern | hit count | bank cluster |
|---|---:|---|
| `JSL $80:A151` | 16 | C0:5 / C4:5 / C2:3 / C3:3 |
| `JSL $80:A170` | 27 | C0:10 / C4:10 / C3:4 / C2:3 |
| `JSL $80:A185` | 25 | C0:14 / C4:5 / C2:3 / C3:3 |
| `JSL $80:A474` | 36 | C6:10 / C4:8 / C5:8 / C3:7 / C0:1 / C1:1 / C2:1 |
| `DA:3800 pointer table operand` | 1 | C4:1 |

C4側は `DA:3800` 資材、C0/C2/C3側は汎用表示・戦闘/フィールド/画面部品側の別入口候補。

## 今後の攻め方

1. `raw 04A8FE..04AC8B` を「DA stream decoder + VRAM queue builder」として正式分解。
2. `80:A151/A170/A185` の引数 `$0F/$06/$07` の意味を確定する。
3. `7E:390B / 394B / 397B / 399B` が VRAM のどの tile index に落ちるかを、次のログで DMA/VRAM hook と突合。
4. 戦闘背景本体は `DA:3800` とは別の圧縮資材の可能性が高いので、次は `JSL $80:A151/A170/A185` の C0/C2/C3 側 caller を順に切る。

## 生成物

- `da3800_stream1_candidate_glyphs.png`
- `da3800_streams_01_22_overview.png`
- `static_dma_asset_reference_summary_20260501.csv`
- `static_dma_asset_reference_hits_20260501.csv`
- `battle_vram_exact_rom_match_summary_20260501.csv`
- `shinmomo_static_graphics_probe_20260501.py`

