# mapchip pipeline v6（vol016 merge）

## stage 1: runtime logging

Lua pollingで以下を採る。

- VRAM
- CGRAM
- OAM
- PPU registers
- BG summary
- DMA trigger log
- visible object list

## stage 2: tilemap entry decode

SNES BG tilemap entryを以下へ分解する。

```text
bits 0-9   tile_id
bits 10-12 palette
bit 13     priority
bit 14     hflip
bit 15     vflip
```

## stage 3: tile usage / metatile candidate

tile usage頻度、palette variant、2x2 adjacencyからmetatile候補を作る。

## stage 4: adjacency graph

`build_tile_adjacency_v2.py` で、右隣・下隣の共起回数を集計する。

## stage 5: tilemap heuristic inference

`infer_tilemap_layout_v2.py` で、adjacency graphから32x32程度の暫定tilemapを構築する。

注意: adjacencyだけでは絶対配置は一意に決まらない。runtime BG tilemap CSVがある場合はそちらを正とする。

## stage 6: ASCII/PNG debug render

- `render_tilemap_ascii_v2.py`
- `render_tilemap_png_pseudocolor_v1.py`

CGRAM適用前の疑似色確認に使う。

## stage 7: color reconstruction

CGRAM dumpを読み、palette番号とtile pixel値を対応づけてカラーPNG化する。

## stage 8: source tracing

`dma_trigger_log.csv` の `source`, `vram_word_addr`, `size` と `C0:A151/A170/A185` callerを照合し、ROM資材展開元を特定する。
