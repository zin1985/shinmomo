# ROM-derived Mode-7 / EXTBG map reconstruction — 2026-09-29

## Result

All recovered mode-0x01 map families now render from ROM setup resources with
the SNES Mode-7 EXTBG priority semantics applied.

Canonical outputs:

- tileset 1 / layout 1 and 2:
  `data/maps/rendered/world_mode7_tileset_01/`
- tileset 2 / layout 3 and 4:
  `data/maps/rendered/mode7_tileset_02/`
- tileset 3 / layout 5:
  `data/maps/rendered/mode7_tileset_03/`

Renderer:

- `tools/python/render_mode7_map_family_from_setup.py`

Runtime VRAM/CGRAM is not required as rendering input.

## ROM setup

Observed selector setup:

```text
TS1 layout 1: 10 01 / 11 01 / 50 01 01 01
TS1 layout 2: 10 01 / 11 02 / 50 01 02 01
TS2:          10 02 / 11 04 / 50 02 ...
TS3:          10 03 / 11 05 / 50 03 05 01
```

Tileset 1 also has a special layout-1 state using palette operand `11 03`;
that is an alternate visual state and is not used for the canonical normal
layout-1 image.

## Graphics proof

The established tileset-1 runtime capture provides a byte-level oracle.

ROM decoding of opcode `10 01` yields 16384 bytes.  Mode-7 stores its chunky
8-bit pixel stream in the odd byte of each VRAM word.  The decoded ROM resource
is:

```text
16384 / 16384 bytes identical
```

to the captured runtime pixel plane.

SHA-256 on both sides:

```text
5521AEB3F5990961D9510CF88FF671A180D2555EF762E451912E3EC54B303ECE
```

## Palette proof

For normal tileset-1 layout 1, opcode `11 01` provides CGRAM indices
`0x20..0x7F`.

Its 192 ROM payload bytes are:

```text
192 / 192 bytes identical
```

to the matching runtime WRAM/CGRAM staging bytes.

SHA-256:

```text
17A06D5A727CF0B2028A53032AD5FC0CE369AA0E930FE998371095F05AD4B284
```

## EXTBG correction

The first world-map renderer treated each 8-bit Mode-7 pixel as a direct
0x00..0xFF CGRAM index.  That reproduced the captured raw VRAM/CGRAM inputs but
was not the final visible-layer interpretation used by the PPU.

The runtime PPU mirror state proves EXTBG:

```text
WRAM $0379 = 0x03  -> TM: BG1 + BG2 on main screen
WRAM $037A = 0x00  -> TS: no BG layer on subscreen
WRAM $037E = 0x23  -> color math enabled for BG1/BG2/backdrop
WRAM $0382 = 0x40  -> SETINI bit 6: EXTBG enabled
CGRAM 0x00 = 0x0000 -> black backdrop
```

The NMI/display register writer at `C0:F38A..` copies these mirrors to
`$212C/$212D/$2131/$2133`.

In Mode-7 EXTBG, BG2 uses the same pixel stream but interprets bit 7 as its
priority flag.  For raw pixels `0x81..0xFF`, BG2 is visible above BG1 and
uses `raw & 0x7F` as its color index.

For every recovered TS1/TS2/TS3 layout:

- raw `0x80` occurs zero times;
- after applying EXTBG priority semantics, every visible color index is covered
  by that layout's explicit opcode-0x11 palette resource.

Therefore the static visible-background rule used by the renderer is:

```text
raw 0x00       -> transparent/backdrop
raw 0x01..0x7F -> CGRAM[raw]
raw 0x81..0xFF -> CGRAM[raw & 0x7F]
raw 0x80       -> fail closed (not present in recovered layouts)
```

This removes the false magenta/high-palette colors that previously appeared in
forest, mountain and tree features.

Because the runtime backdrop is black and the subscreen has no BG layer, the
observed additive color-math state does not alter these background colors.

## Palette coverage after EXTBG

Visible indices are completely covered by the immediate setup palette:

- TS1 layout 1 / `11 01`: complete
- TS1 layout 2 / `11 02`: complete
- TS2 layouts 3/4 / `11 04`: complete
- TS3 layout 5 / `11 05`: complete

The previously identified high-CGRAM ROM byte sequences remain useful runtime
data, but they are not required to color the visible EXTBG map background.

## Output dimensions

- TS1 map 001: 4096 x 4096
- TS1 map 002: 4096 x 4096
- TS2 map 003: 2048 x 2048
- TS2 map 004: 2048 x 2048
- TS3 map 005: 4096 x 4096

Outputs are RGBA PNGs.  Raw color index 0 is represented with alpha 0.

## Status

Every recovered map-configuration family now has a ROM-derived rendering path.

Remaining map-output work is refinement:

1. bind alternate visual/palette states such as TS1 layout1 + `11 03`;
2. attach human-facing location names using event/dialogue/warp evidence;
3. preserve runtime-only effects separately from canonical geometry images.
