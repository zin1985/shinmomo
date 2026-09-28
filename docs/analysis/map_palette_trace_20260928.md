# Map palette ROM trace 2026-09-28

## Result

The tileset-4 town/field palette path is now structurally identified and runtime-validated.

The Snes9x core does not expose CGRAM as a readable memory domain, but the game itself
maintains a complete 512-byte CGRAM staging image in WRAM at:

`$7E:21C2..$7E:23C1`

A bounded runtime capture of this staging area at frame 6429, while pack `0x50` /
tileset 4 / layout 8 was active, produced the palette now used by the canonical
tileset-4 map renders.

Palette SHA-256:

`323A1D99B931576D513F3953BE90976C1ADAE2E5124BB207C52101836F30B878`
## ROM-side transfer proof

The unique obvious full-CGRAM DMA setup is at `C0:B3DC..`.

Relevant instructions decode as:

```text
C0:B3DC  LDA $111A
C0:B3DF  BEQ skip
C0:B3E1  LDA $0AE6
C0:B3E4  BEQ skip
C0:B3E6  LDA #$00      ; DMA mode
C0:B3E8  STA $4300
C0:B3EB  LDA #$22      ; BBAD = $2122 CGDATA
C0:B3ED  STA $4301
C0:B3F0  LDA #$C2
C0:B3F2  STA $4302
C0:B3F5  LDA #$21
C0:B3F7  STA $4303
C0:B3FA  LDA #$7E
C0:B3FC  STA $4304     ; source = $7E:21C2
C0:B3FF  LDA #$00
C0:B401  STA $4305
C0:B404  LDA #$02
C0:B406  STA $4306     ; size = $0200 bytes
C0:B40E  STZ $2121     ; CGRAM address = 0
C0:B411  LDA #$01
C0:B413  STA $420B     ; start DMA channel 0
```
The routine is called from the display/NMI path at `C0:F0C0` via `JSR $B3DC`.

Immediately upstream, the palette-copy path around `C0:B3A6..` copies 16-bit colors
into `$7E:21C2,X` and then calls mirrored routine `$80:B3D6`, which sets
`$111A=1` to request the CGRAM upload.

This establishes the data path:

```text
palette source data
  -> palette copy routine
  -> WRAM $7E:21C2 staging image
  -> C0:B3DC full 0x0200-byte DMA
  -> CGRAM $000..$1FF
```

## Runtime validation

The recovered WRAM palette was applied to the corrected tileset-4 reconstruction:

- layout: 8
- tileset: 4
- CHR byte base: VRAM `0x0000`
- pixel format: 4bpp
- human identification: 旅立ちの村

The resulting full-color render visually reproduces the live game screen's forests,
roads, buildings, shrine, fields and water colors.
A tile-aligned image search against the live 256x224 screenshot found the best match
at full-map pixel coordinate `(432, 448)`.

Validation metrics including live sprites/actors:

- 8x8-block mean absolute RGB error: about `3.35 / 255`
- full-pixel mean absolute channel error: about `15.21 / 255`
- fraction of pixels with mean RGB error <= 2: about `58.3%`
- fraction with mean RGB error <= 20: about `75.3%`

The remaining differences include runtime sprites/actors and dynamic render details,
so the palette/layout agreement is stronger than a raw screenshot equality metric.

## Canonical outputs

- `tools/python/render_map_layout_images.py`
- `data/maps/rendered/tileset_04/palette.json`
- `data/maps/rendered/tileset_04/index.json`
- `data/maps/rendered/tileset_04/index.csv`
- `data/maps/rendered/tileset_04/map_###.png`

Raw WRAM, VRAM, CGRAM and ROM dumps remain local-only.
