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

The Snes9x core does not expose CGRAM as a readable memory domain, but ROM tracing
identified the game's canonical 512-byte CGRAM staging buffer at WRAM
`$7E:21C2..$23C1`.

The tileset-4 batch is now rendered in color from that staging buffer:

- palette mode: `wram_cgram_staging`
- staging capture frame: 6429 on pack `0x50` / tileset 4 / layout 8
- palette SHA-256: `323A1D99B931576D513F3953BE90976C1ADAE2E5124BB207C52101836F30B878`
- derived palette catalog: `data/maps/rendered/tileset_04/palette.json`

The raw WRAM capture remains local-only. Only the derived BGR555/RGB palette,
hashes and colored render outputs are canonical.

`map_008` is runtime-validated against the live 旅立ちの村 screen. The other
28 tileset-4 renders use the same proven staging palette set but remain individually
unverified until their corresponding runtime scenes are captured.

## Why map numbers are sparse

`map_###` is the global ROM layout-record ID from the 203-entry CF layout table,
not a per-town sequential number. This directory contains only layouts currently
used with primary tileset 4, so IDs belonging to other tilesets appear as gaps.

A layout ID can also be referenced by multiple packs/configurations. For example,
layout 8 is used by packs `0x50`, `0xF0` and `0xF1`; the runtime pack context
selects the exact occurrence.

## First-batch map IDs

`006, 008, 018, 019, 028, 029, 030, 031, 034, 035, 039, 044, 045,
057, 058, 059, 060, 061, 062, 070, 073, 074, 081, 082, 085, 086,
088, 089, 091`

The batch includes the runtime-bound `map_008` used for the 旅立ちの村
identification and the town-reference candidate layouts currently under analysis.

## Next

Repeat the same process per tileset as a validated CHR capture becomes available.
Do not render layouts with an unrelated tileset capture merely to fill the catalog.
