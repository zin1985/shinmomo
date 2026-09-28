# Map-chip CHR trace and corrected tileset-4 reconstruction

Updated: 2026-09-28

## Result

The first tileset-4 render batch used the wrong CHR base. The map/layout and
metatile reconstruction were correct, but the bitmap source was not.

The runtime-bound 旅立ちの村 sample now establishes the correct field/town
render basis as:

- primary tileset: 4
- primary layout: 8
- pixel format: 4bpp
- CHR byte base in captured VRAM: `0x0000`
- palette mode in committed renders: tile-index grayscale, because the active
  Snes9x core does not expose CGRAM as a readable memory domain

With `char_base=0x0000`, the reconstructed full map visibly reproduces the
same building roofs/walls, trees, fields, ponds, roads, stairs and shrine
components seen in the live 旅立ちの村 screen.
## Why the previous 0x8000 basis was wrong

The active 旅立ち capture has a completely empty VRAM region at 0x8000:

- VRAM 0x8000..0x87FF: all zero in the sampled field state
- the previous renderer nevertheless treated 0x8000 as the 4bpp CHR base

That could preserve map placement while producing wrong or blank tile graphics.
The old PNGs were therefore structural placeholders, not valid map-chip
reconstructions.

Candidate full-map renders were generated at 0x0000, 0x2000, 0x4000, 0x6000
and 0x8000. Only 4bpp/0x0000 reconstructs coherent town graphics matching the
live field scene.
## ROM-side facts retained

The map structure path remains unchanged and independently proven:

`CF:2000 layout record`
-> standalone layout decode
-> metatile IDs
-> `CE:2000` tileset/metatile definitions
-> four SNES tilemap entries per normal metatile
-> map upload queue / VRAM tilemap

The correction affects only the final interpretation of tile-number -> CHR bitmap.

A raw-ROM scan of 32-byte VRAM tiles found almost no meaningful direct ROM
matches for the field CHR region. This supports the model that the resident CHR
is produced by a loader/decompression path rather than copied as a flat,
uncompressed tile array from ROM.
## CF:0000 parallel table clarification

The CF:0000 table is not a CHR-source pointer table.

For tilesets 4..59, 56 of 56 adjacent spans tested match exactly:

`CF parallel span bytes == CE metatile block span bytes / 8`

Examples:

- tileset 4: CE span 3392 bytes -> 424 metatiles; CF span 424 bytes
- tileset 7: CE span 3056 bytes -> 382 metatiles; CF span 382 bytes
- tileset 21: 256 metatiles; CF span 256 bytes
- tileset 50: 231 metatiles; CF span 231 bytes

The first three tilesets use a different-width special form. The dominant
one-byte-per-metatile relation makes CF:0000 a per-metatile attribute/property
family, not the field CHR bitmap source.
## DA:3800 exclusion

The previously noted DA:3800 stream family was rechecked visually. Its decoded
records contain digits, Latin/Japanese glyph-like forms and narrow variable
patterns. It is not the town/field terrain CHR source and should not be used for
map-chip salvage.

## Canonical corrected outputs

- `tools/python/render_map_layout_images.py`
- `data/maps/rendered/tileset_04/`
- `docs/analysis/map_layout_render_batch_20260928.md`

All 29 tileset-4 `map_###.png` files are regenerated from the same ROM
layout/metatile data using 4bpp CHR at VRAM byte base 0x0000.

## Remaining gap

The exact compressed ROM asset source and decompression routine that populate
VRAM 0x0000 remain to be connected. BizHawk's Snes9x Waterbox core accepted
Lua memory callbacks for PPU/DMA registers but did not deliver write/execute
events in this session, so the current correction is grounded in static ROM
structure plus the validated resident VRAM/image correspondence.

Do not revert to 0x8000 for tileset-4 field/town renders.
