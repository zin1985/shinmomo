# ROM-derived dungeon/special map batch 10 — 2026-09-29

## Result

Tileset 58 / layout 196 is now fully reconstructable from ROM-proven runtime
initialization plus the already-proven pack-specific setup.

This closes the only missing tileset-58 layout.

Canonical family:

- tileset 58 / layout 196
- tileset 58 / layout 197
- tileset 58 / layout 198

All three are stored in:

- `data/maps/rendered/dungeon_tileset_58/`

The family setup remains:

```text
10 1B
10 0D
11 37
```

Layout 196 additionally depends on one tile from the low/common VRAM region.
That dependency is now resolved by the normal-map transition zero-fill proven
below.
## The previous blocker

Layout 196 references tile `0x0E0` exactly once.

Exact provenance:

- expanded tile coordinate: `(366, 116)`
- SNES tilemap entry: `0x10E0`
- palette ID: 4
- CE metatile: tileset-58 metatile `0x8C`
- metatile raw bytes: `e0 10 09 15 2f 15 07 11`
- tile byte range in 4bpp VRAM: `0x1C00..0x1C1F`

The pack-specific graphics resources begin at VRAM byte `0x2000`, so the old
strict validator correctly rejected layout 196 until the low/common region had
an independent source.

The low VRAM region is not globally constant across runtime captures, so no
runtime sample or arbitrary common tile is borrowed.
## Common transition zero-fill proof

The normal map-transition path reaches `80:CBB6` before the state-0 pack
entry is executed.

Immediately before the normal-map clear helper, `80:CBB6` reaches
`80:A361`.

For the normal-map branch (`$113C == 0`), `80:A361`:

```text
STZ $03AD
LDA #$01
STA $03AE
JSL $80:A3A5
JSL $80:A3AF
```

Thus the queued fill value in `$03AD` is zero.

`80:A3A5` initializes the 16-bit destination accumulator to `0x0800`.
`80:A3AF` initializes it to `0x1000`.
Both call `80:A420`.
`80:A420` performs 16 iterations.  Each iteration subtracts `0x0080`
from the destination before calling `80:A438`.

Therefore the two calls enqueue these VRAM word destinations:

```text
A3A5: 0780,0700,0680,0600,0580,0500,0480,0400,
      0380,0300,0280,0200,0180,0100,0080,0000

A3AF: 0F80,0F00,0E80,0E00,0D80,0D00,0C80,0C00,
      0B80,0B00,0A80,0A00,0980,0900,0880,0800
```

Together they cover every `0x80`-word block from VRAM word `0x0000`
through `0x0FFF`.
## DMA queue semantics

For each block, `80:A438` queues:

```text
control word       = 0x0084
transfer byte size = 0x0100
VRAM word address  = current block destination
payload            = 0x80 words copied from $03AD
```

Because `$03AD == 0`, every payload byte is zero.

The queue consumer at `80:A1B9` interprets control `0x0084` as a normal
VRAM DMA using `$2118/$2119`, loads the queued VRAM word destination into
`$2116`, and transfers the queued `0x0100` bytes.

Each destination therefore clears `0x80` VRAM words, or `0x0100` bytes.

The combined clear is exactly:

```text
VRAM words: 0x0000 .. 0x0FFF
VRAM bytes: 0x0000 .. 0x1FFF
```

Tile `0x0E0` occupies bytes `0x1C00..0x1C1F`, wholly inside this
proven-zero range.
## Renderer model

`tools/python/render_normal_map_family_from_setup.py` now accepts:

```text
--zero-fill-range BYTE_START:BYTE_END
```

The range is not an ad-hoc missing-tile replacement.  It is added to the same
coverage ledger used for ROM graphics resources, with
`placement_source = proven_transition_zero_fill`.

The final VRAM ordering remains:

1. transition zero-fill,
2. explicit map graphics resources,
3. map rendering.

Thus later explicit CHR resources retain precedence over any overlapping
transition-clear range.

For tileset 58 the proven range is:

```text
--zero-fill-range 0x0000:0x2000
```
## Validation

Full tileset-58 regeneration with the proven zero-fill passes strict coverage
for layouts 196, 197 and 198.

Regression checks:

- layout 197 PNG is byte-identical to the previously committed render:
  `39965F6D0F464058CD400371BB1DB12B863185CB6370AB11E2C90A3961F4360F`
- layout 198 PNG is byte-identical to the previously committed render:
  `CCCD04100D3A8284747177CEC56C0682C2A54E29997ED7627549E6D917F54641`
- tileset-8 / layout-92 rendered without a zero-fill option remains
  byte-identical to its canonical PNG.

The newly resolved tile `0x0E0` decodes as an all-zero 4bpp tile after the
transition clear, so normal BG color-index-0 transparency makes its 8x8 cell
transparent as required.

No raw ROM, VRAM, WRAM or CGRAM payload is committed.
