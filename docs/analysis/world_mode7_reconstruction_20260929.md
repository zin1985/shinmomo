# World Mode-7 map reconstruction 2026-09-29

## Runtime identity

Walking south out of the runtime-bound 旅立ちの村 sample produced:

- source: pack `0x50`, tileset 4, layout 8, variant 2
- transition pack: `0x4C`
- after selector installation: tileset 1, layout 1, variant 1
- layout 1 header: mode `0x01`, 16x16 chunks, 256 cells

This is the first direct runtime binding of the large mode-0x01 map family to the
world-map transition from 旅立ちの村.
## Alternate map expansion format

`C0:D19E` branches on `$113C`, which is loaded from the layout header low nibble.

Normal maps use `C0:D1B2`:

- combine the metatile ID,
- multiply it by 8,
- read four 16-bit SNES tilemap entries.

Mode-0x01 world layouts use `C0:D1F3` instead:

- mask the staged ID to 8 bits,
- multiply the ID by 4,
- read four single-byte entries with `C0:D225`.

For tileset 1, `CE:2100..CE:23FF` is 768 bytes, exactly 192 definitions of
4 bytes each. Layout 1's maximum ID is 191, which closes the format boundary exactly.
## Mode-7 VRAM proof

The runtime world capture has coherent 8-bit graphics when VRAM is interpreted using
the SNES Mode-7 interleaving:

- even byte of each VRAM word: tilemap-side data
- odd byte of each VRAM word: 8-bit tile pixel data

The odd-byte stream yields exactly 256 x 64 pixel bytes, i.e. 256 8x8 tiles.
Applying the WRAM `$7E:21C2..$23C1` palette staging image produces coherent terrain
tiles including mountains, roads, caves, bridges, snow, vegetation and structures.

The renderer therefore expands each world definition as four 8-bit tile IDs in
TL, TR, BL, BR order.
## Canonical outputs

Reproducible renderer:

- `tools/python/render_world_mode7_maps.py`

Derived outputs:

- `data/maps/rendered/world_mode7_tileset_01/map_001.png`
- `data/maps/rendered/world_mode7_tileset_01/map_002.png`
- same-ID JSON metadata
- `data/maps/rendered/world_mode7_tileset_01/index.json`
- `data/maps/rendered/world_mode7_tileset_01/palette.json`

Both maps render at 4096x4096 pixels.

`map_001` forms a coherent full world map. `map_002` is a sparse alternate map using
the same world tileset; its semantic role remains intentionally unresolved.

Raw ROM, VRAM and WRAM capture bytes remain local-only.
