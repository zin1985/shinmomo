# Mode-7 world reconstruction — 2026-09-29

## Canonical result

Tileset 1 world layouts are rendered at:

```text
data/maps/rendered/world_mode7_tileset_01/
```

Outputs:

- `map_001.png` — 4096 x 4096
- `map_002.png` — 4096 x 4096
- same-ID JSON metadata
- ROM resource metadata and palette files
- `index.json`

## Layout format

Mode-0x01 layouts use 4 bytes per CE definition.  Each definition expands to a
2x2 group of Mode-7 8x8 tile IDs:

```text
byte0 byte1
byte2 byte3
```

The four tile IDs therefore produce one 16x16 map cell.

## ROM graphics and palette setup

Tileset 1 graphics are loaded by opcode `10 01`.

Canonical palette setup is layout-specific:

- layout 1: opcode `11 01`
- layout 2: opcode `11 02`

A separate layout-1 state using `11 03` exists in pack 0xED and is retained as
an alternate visual-state lead rather than being mixed into the canonical map.

## EXTBG correction

The initial reconstruction correctly recovered geometry and raw Mode-7 pixel
bytes, but treated pixel bit 7 as part of an 8-bit CGRAM index.  Runtime state
shows that EXTBG is enabled:

```text
TM     = 0x03  (BG1 + BG2)
TS     = 0x00
CGADSUB= 0x23
SETINI = 0x40  (EXTBG)
```

With EXTBG, BG2 interprets pixel bit 7 as priority and uses the lower seven bits
as its visible color index.  Re-rendering with this rule removes the magenta and
other false colors that were most visible in forests, trees and mountain detail.

No recovered TS1 layout uses raw pixel 0x80, so the visible-background
interpretation is unambiguous for the current world maps.

The renderer is now ROM-only:

```text
tools/python/render_mode7_map_family_from_setup.py
```

and does not require captured VRAM/CGRAM as source data.

## Transparency

Raw pixel 0 is exported as alpha-transparent.  In the currently recovered TS1
layouts the graphics do not use raw index 0, so this mainly defines the correct
renderer behavior for future Mode-7 resources rather than changing large areas
of the present maps.

## Provenance

Raw ROM and emulator capture bytes remain local-only.  Runtime captures are used
only as validation evidence, not as committed rendering inputs.
