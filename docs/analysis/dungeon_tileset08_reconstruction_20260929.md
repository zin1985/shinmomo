# Dungeon tileset-8 reconstruction 2026-09-29

## Result

The first dungeon/cave map family is now reconstructable directly from ROM setup
opcodes, without runtime VRAM or CGRAM dumps.

Canonical layouts:

- tileset 8 / layout 92
- tileset 8 / layout 94
- tileset 8 / layout 96

Relevant runtime/script packs include:

- pack `0x53` -> layout 94
- packs `0x91..0x95` -> layout 92
- pack `0x95` -> layout 96

Human-facing location names are intentionally not assigned by shape alone.
## Setup signature

The normal-VM selector prefixes for the tileset-8 family repeatedly contain:

```text
10 0C
10 0D
11 0A
...
50 08 <layout> 02
```

For comparison, the runtime-validated tileset-7 interior sample uses:

```text
10 0A
10 0B
11 09
50 07 0F 02
```

Opcode `0x10` reaches `C4:8A54 -> 80:B572 -> 80:B7A7` and selects
an eight-byte graphics-load descriptor.
Opcode `0x11` reaches the `80:B340..` palette path that writes into the
canonical CGRAM staging buffer at `$7E:21C2`.
## Graphics resources

State0 fixes `$035F=2`, selecting descriptor base `C3:0850`.

### Opcode `10 0C`

Descriptor `C3:08A8`:

```text
00 10 00 20 BA CD D3 12
```

Decoded fields:

- VRAM word destination: `0x1000`
- VRAM byte destination: `0x2000`
- decoded size: `0x2000` bytes
- compressed source: `D3:CDBA`
- reader dispatch: 2 / `C0:C03C,C07F`
- decoded SHA-256:
  `59B1C33E007CF773784485D000481D9859A033128B0283D37DAC8550D69E5F84`

### Opcode `10 0D`

Descriptor `C3:08B0`:

```text
00 20 00 20 02 E9 D3 12
```

Decoded fields:

- VRAM word destination: `0x2000`
- VRAM byte destination: `0x4000`
- decoded size: `0x2000` bytes
- compressed source: `D3:E902`
- reader dispatch: 2 / `C0:C03C,C07F`
- decoded SHA-256:
  `1FA0B969901B3CB85FBDB69429E661E72CDC2F7682DBF271C3C31565BB384735`
## Decoder validation

The dispatch-2 stream is a four-context byte-reuse codec:

- one control byte is consumed MSB-first,
- output context is selected by output-position bit0 and bit4,
- control bit 1 reads a new literal and updates that context,
- control bit 0 reuses the previous byte for that context.

The decoder was validated against the known tileset-7 runtime capture before it
was used for dungeon graphics:

- room resource `D3:A566`, 0x2000 bytes -> runtime VRAM byte `0x2000`:
  **100.0% byte equality**
- room resource `D3:BCE3`, 0x16A0 bytes -> runtime VRAM byte `0x4000`:
  **100.0% byte equality**

This independently proves both the codec and the VRAM byte-address conversion.
## Palette resource

Opcode `11 0A`, under the same state0 descriptor index, resolves as:

```text
C0:B516[2]      -> C0:4C11
entry (0A-1)    -> C0:5367
descriptor       = 20 00 40 00
payload          = C0:536B
```

Therefore it loads:

- CGRAM start index: `0x20`
- color count: `0x40` (64 colors)
- covered CGRAM range: `0x20..0x5F`

All non-transparent palette indices used by layouts 92/94/96 fall inside this
range.
## Runtime capture independence

Tile-index usage proves that these maps do not depend on the common
`VRAM 0x0000..0x1FFF` region:

- layout 92: minimum tile ID 256
- layout 94: minimum tile ID 256
- layout 96: minimum tile ID 310

Thus the committed tileset-8 renders are reconstructed entirely from:

1. ROM layout data,
2. ROM CE metatile definitions,
3. ROM opcode-0x10 graphics resources,
4. ROM opcode-0x11 palette resource.

No runtime graphics dump is required.

For normal SNES BG rendering, 4bpp color index 0 is treated as transparent.
## Canonical outputs

Renderer:

- `tools/python/render_normal_map_family_from_setup.py`

Derived tileset-8 batch:

- `data/maps/rendered/dungeon_tileset_08/map_092.png`
- `data/maps/rendered/dungeon_tileset_08/map_094.png`
- `data/maps/rendered/dungeon_tileset_08/map_096.png`
- same-ID JSON metadata
- `data/maps/rendered/dungeon_tileset_08/resources.json`
- `data/maps/rendered/dungeon_tileset_08/palette.json`
- `data/maps/rendered/dungeon_tileset_08/index.json`

The PNG files use alpha transparency for normal-BG color index 0.
