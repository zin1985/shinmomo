# Static map-layout render batch 2026-09-28

## Result

A reproducible renderer now reconstructs full map-layout images from the proven ROM
layout/metatile data plus a validated runtime tileset capture.

The first committed batch covers every configuration currently using primary tileset 4:

- 29 distinct map/layout IDs
- filenames are the map/layout IDs: `map_006.png` ... `map_091.png`
- each PNG has a same-ID JSON metadata file
- `index.csv` and `index.json` enumerate the complete batch
## Reconstruction basis

Tool:

- `tools/python/render_map_layout_images.py`

Canonical outputs:

- `data/maps/rendered/tileset_04/`

The renderer uses:

1. `decode_map_layout.py` to decode the CF layout records,
2. CE tileset-4 metatile definitions to expand the logical map to SNES tilemap entries,
3. 4bpp CHR data at VRAM byte base `0x0000` from the runtime-confirmed pack-0x50 capture. This base was corrected by direct comparison against the live 旅立ちの村 screen; the earlier 0x8000 assumption was wrong.

Raw ROM, VRAM and CGRAM are not committed.
## Palette status

The active Snes9x capture exposes a 512-byte CGRAM file containing only zero bytes.
Therefore color reconstruction from that capture is not valid.

The committed images intentionally use `tile_index_grayscale`:

- 4bpp pixel index 0..15 is rendered as grayscale 0..255,
- tile shape, flip state, map placement and metatile composition remain preserved,
- no false color information is invented.

When a non-zero CGRAM capture becomes available, the same renderer automatically
switches to captured-CGRAM color mode and can regenerate the batch.
## First-batch map IDs

`006, 008, 018, 019, 028, 029, 030, 031, 034, 035, 039, 044, 045,
057, 058, 059, 060, 061, 062, 070, 073, 074, 081, 082, 085, 086,
088, 089, 091`

The batch includes the runtime-bound `map_008` used for the 旅立ちの村
identification and the town-reference candidate layouts currently under analysis.

## Next

Repeat the same process per tileset as a validated CHR capture becomes available.
Do not render layouts with an unrelated tileset capture merely to fill the catalog.
