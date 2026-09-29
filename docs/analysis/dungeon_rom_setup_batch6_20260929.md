# ROM-derived dungeon/special map batch 6 — 2026-09-29

## Result

This batch models normal-VM opcode `0x33` graphics placement and closes eight
additional map families under strict ROM-only CHR/palette coverage.

No runtime VRAM/CGRAM payload is committed. The renderer decodes graphics from ROM,
places them according to opcode-0x10 descriptor destinations and opcode-0x33
explicit destinations, applies the opcode-0x11 palette, then fails closed if a
layout references any uncovered tile or non-transparent palette index.
## Opcode 0x33 semantics

Normal-VM opcode `0x33` dispatches to `C4:8A5E`.

The handler reads:

```text
33 <VRAM word low> <VRAM word high> <graphics descriptor>
```

The first two operands are stored in `$0F/$10`. The third operand is passed to
`$80:B557`.

`B557` preserves the caller's `$0F`, calls `B7A7` to resolve the selected
graphics descriptor/source/size/reader, restores the caller's `$0F`, then enters
the common graphics transfer path. Therefore opcode 0x33 uses the descriptor's
source and output size while overriding its VRAM destination.
## Families promoted

| tileset | graphics setup | palette | layouts |
|---:|---|---|---|
| 22 | `33 00 10 0F` | `11 18` | 121 |
| 23 | `33 00 10 0F / 10 0D` | `11 19` | 123 |
| 24 | `33 00 10 0F / 10 0D` | `11 1A` | 125, 127 |
| 25 | `33 00 10 0F / 10 0D` | `11 1B` | 129 |
| 28 | `33 00 10 0F / 10 0D` | `11 19` | 136 |
| 29 | `10 10 / 33 00 20 12` | `11 1D` | 138 |
| 30 | `33 00 10 0F / 10 0D` | `11 19` | 140 |
| 37 | `33 00 10 0F / 10 0D` | `11 24` | 152 |

For example, `33 00 10 0F` places descriptor `0x0F` at VRAM word
`0x1000` (byte `0x2000`), exactly covering the tile ranges that failed before
the opcode-0x33 destination override was modeled.
## Outputs

- `data/maps/rendered/dungeon_tileset_22/`
- `data/maps/rendered/dungeon_tileset_23/`
- `data/maps/rendered/dungeon_tileset_24/`
- `data/maps/rendered/dungeon_tileset_25/`
- `data/maps/rendered/dungeon_tileset_28/`
- `data/maps/rendered/dungeon_tileset_29/`
- `data/maps/rendered/dungeon_tileset_30/`
- `data/maps/rendered/dungeon_tileset_37/`

Nine map-ID PNGs are produced in total. Representative outputs form coherent cave,
waterway and structure maps rather than random tile assemblies.

The renderer records opcode-0x33 placements separately as `graphics_overrides`
in per-map and batch metadata.

## Remaining work

- tileset 5: a small high-CHR region is still not accounted for;
- tileset 32: tiles `0x21B..0x21E` remain outside its immediate setup;
- tileset 58: tile `0x0E0` remains outside its immediate setup;
- tileset 42: palette state is inherited and not yet proven;
- tilesets 2/3: mode-0x01 layouts require the Mode-7 path.
