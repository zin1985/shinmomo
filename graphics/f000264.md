# 新桃太郎伝説解析 vol016 フィールド移動時 VRAM/BG/マップチップ解析メモ 2026-05-01

## 入力

アップロードされたファイルを確認した。

- `manifest.csv`
- `bg_summary.csv`
- `ppu_regs_capture.csv`
- `dma_trigger_log.csv`
- `ppu_write_log.csv`
- `vram.bin`

注意点として、`bg_summary.csv` / `ppu_regs_capture.csv` / `vram.bin` は同名ファイルが複数アップロードされていたが、作業環境上で参照できたのは最後に残った同名ファイルのみだった。
今回の解析は、現在参照できる `vram.bin` に基づく。

## 入力ログの状態

### manifest

`manifest.csv` には以下の5 snapshot があった。

| frame | reason | vram_hash | cgram_hash |
|---:|---|---|---|
| 53931 | init | 3D32 | 9DC5 |
| 54000 | interval | 3D32 | 9DC5 |
| 54300 | interval | 5D93 | 9DC5 |
| 54600 | interval | 872F | 9DC5 |
| 54900 | interval | 5EE2 | 9DC5 |

VRAM hash が移動中に変化しているので、フィールド移動に伴うVRAM更新は実際に発生している。

### PPU/DMA log

`ppu_regs_capture.csv` は `2100..213F / 4200..421F` がほぼすべて `00`。
`dma_trigger_log.csv` と `ppu_write_log.csv` はヘッダのみだった。

このため、今回の実行では PPU register write hook / DMA trigger hook は捕捉できていない。
ただし、`vram.bin` 自体は有効で、tilemap と tile graphics の対応は復元できた。

## 今回の最重要発見

現在参照できる `vram.bin` について、以下の組み合わせでフィールド背景がかなり自然に復元できた。

```text
tilemap base : VRAM 0x0000
char base    : VRAM 0x8000
bpp          : 4bpp
BG size      : 64x64候補、および 0x0000..0x7FFF に 16枚分の32x32 screen候補
```

特に `VRAM 0x0000` 先頭は以下のような16bit BG tilemap entry として読める。

```text
0000: 02 00 03 00 02 00 03 00 ...
0080: 02 2A 03 2A 02 2A 03 2A ...
```

little endian で読むと `0x0002 / 0x0003 / 0x2A02 / 0x2A03` などになり、SNES BG tilemap entry として自然。

`0x2A02` は tile index `0x202` を指す。
`char_base=0x8000, 4bpp` の場合、tile `0x202` の実体は:

```text
0x8000 + 0x202 * 0x20 = 0xC040
```

つまり、`0xC000` 付近の4bppタイル群がフィールド地形タイルとして参照されている。

## VRAM暫定レイアウト

| VRAM範囲 | 暫定用途 | 根拠 |
|---|---|---|
| `0x0000..0x7FFF` | field BG tilemap / 複数screen name table候補 | 16bit entry として自然。32x32 screenが16枚ぶん描画可能。 |
| `0x8000..0x87FF` | 空き/未使用寄り | ほぼ全ゼロ。 |
| `0x8800..0x9BFF` | 文字/UI/小物タイル候補 | 2bpp/4bpp sheetで字形・記号系に見える。 |
| `0xA000..0xA7FF` | 補助タイル候補 | 部分的に非ゼロ。 |
| `0xA800..0xBFFF` | 空き寄り | ほぼ全ゼロ。 |
| `0xC000..0xD8FF` | field地形/オブジェクト系 4bpp tile 本命 | `char_base=0x8000` の高tile番号から参照され、背景復元に使われる。 |
| `0xDC00..0xEFFF` | 空き寄り | ほぼ全ゼロ。 |
| `0xF000..0xFFFF` | stripe/fill/special pattern候補 | 2値パターンが多い。 |

## tilemap統計

`0x0000..0x7FFF` を 0x800 byte = 32x32 screen 単位で16画面に分けて解析した。

- 16 screen合計 tilemap entries: 16384
- 2x2 metatile候補: 4096
- 2x2 metatile pattern unique: 2962
- `char_base=0x8000 / 4bpp` 前提の tile usage CSV を出力済み

頻出entryの例:

| entry | 意味 |
|---|---|
| `0x2502` / `0x2503` | tile `0x102/0x103`, palette 2, vflip/priority等あり |
| `0x2512` / `0x2513` | tile `0x112/0x113`, palette 2 |
| `0x2A02` / `0x2A03` | tile `0x202/0x203`, palette 2, 0xC000台参照 |
| `0x3E12` / `0x3E13` | tile `0x212/0x213`, palette 3/属性つき |
| `0x4B12` / `0x4B13` | tile `0x312/0x313`, 属性つき |

## 生成物

- `field_tilemap_16_screens_map0000_to_7FFF_char8000_4bpp.png`
  - `0x0000..0x7FFF` の16 screen候補を一覧化した画像。
- `field_bg_candidate_map0000_char8000_4bpp_64x64.png`
  - `map_base=0x0000, char_base=0x8000, 4bpp, 64x64` として復元した候補画像。
- `field_vram_0000_7fff_tilemap_entries_decoded.csv`
  - 各tilemap entryを `tile/palette/hflip/vflip/priority` に分解。
- `field_tile_usage_charbase8000_4bpp.csv`
  - field tile使用頻度。
- `field_2x2_metatile_pattern_usage.csv`
  - 2x2 tile block pattern 使用頻度。
- `field_top_2x2_metatile_patterns.png`
  - 頻出2x2 patternの画像カタログ。
- `shinmomo_field_vram_analyzer_20260501.py`
  - 同じ解析を再実行できるPythonスクリプト。

## 次に必要な採取

今回、同名 `vram.bin` が上書き扱いになり、複数snapshotを比較できなかった。
次回は以下の形で取得すると、移動差分を直接解析できる。

```text
frame_053931/vram.bin
frame_054000/vram.bin
frame_054300/vram.bin
frame_054600/vram.bin
frame_054900/vram.bin
```

または、`shinmomo_graphics_probe_out` フォルダ全体をそのまま固めて渡す。

次に複数snapshotが揃えば、以下を確定しやすい。

1. 移動時に更新される VRAM tilemap screen
2. field scroll方向と更新screenの関係
3. 32x32 screenのリングバッファ構造
4. ROM側 mapchip stream / DMA source との接続
5. `B294` sprite pattern table と field地形tileの分離

## 13ゴールへの反映

今回伸びたのは主に Goal 13 と Goal 12。

| 目標 | 反映 |
|---|---|
| Goal 13 NPC大量表示時の処理軽減/表示更新 | VRAM側のfield tilemap配置が見えた。OAMだけでなくBG更新側の足場ができた。 |
| Goal 12 全体構造再構成 | field描画資材のVRAM構造が一段進んだ。 |
| Goal 10 文字/表示系 | `0x8800..0x9BFF` にUI/文字系タイル候補が見えた。 |
| Goal 11 外部データ化 | tilemap entry / tile usage / metatile候補をCSV化した。 |

