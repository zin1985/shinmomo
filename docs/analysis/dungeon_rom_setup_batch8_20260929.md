# ROM-derived dungeon/special map batch 8 — 2026-09-29

## Result

Tileset 42 / pack 0x9D is now renderable without guessing an inherited palette.

The record0/entry1 script at `CC:FB5D..CC:FBA1` selects the primary map with:

```text
10 13
10 14
50 2A A3 01
```

The selector is therefore:

- primary tileset: 42
- primary layout: 163
- variant: 1

The same entry then branches into two map-display states.  The two states are
kept as separate canonical render groups because their palette provenance is
different and explicitly encoded by the VM script.

## Branch A: palette 0x29

The fall-through path after the selector loads:

```text
11 29
13 00
10 06
11 05
...
```

The first palette operation uses the state-0 descriptor index 2 and loads
palette operand 0x29.

The later descriptor-index-0 operations do not overwrite the map resources:

- graphics operand 0x06 at descriptor index 0 loads VRAM byte
  `0x6000..0x6FFF`;
- tileset-42 layouts 163/164 use tile IDs only through 0x2DD, i.e. below
  VRAM byte 0x5BC0;
- palette operand 0x05 at descriptor index 0 writes CGRAM indices
  `0x70..0x7F`;
- the map uses palette indices covered by the state-0 0x29 resource at
  `0x20..0x5F`.

Thus the later index-0 graphics/palette work is disjoint from the normal-map
CHR/palette ranges and does not invalidate the palette-0x29 map render.

Canonical output:

- `data/maps/rendered/dungeon_tileset_42_p29/`
- layout 163

## Branch B: palette 0x28 plus secondary layout

The alternate branch reaches:

```text
11 28
15 00 11
51 2A A4
...
```

Opcode 0x11 operand 0x28 loads the map palette range `0x20..0x5F`.

Opcode 0x51 is the proven secondary-map selector:

```text
51 <secondary tileset> <secondary layout>
```

so `51 2A A4` sets:

- secondary tileset: 42
- secondary layout: 164

The primary selector remains tileset 42 / layout 163.

Canonical output:

- `data/maps/rendered/dungeon_tileset_42_p28_secondary/`
- `map_163.png`: primary layout under palette 0x28
- `map_164.png`: secondary layout under the same palette

The two layouts are stored separately; this batch does not invent a composite
layering rule beyond the proven primary/secondary selector state.

## Validation

Both branch families use the same proven map CHR setup:

```text
10 13
10 14
```

Strict resource checks pass:

- every referenced 4bpp tile is inside the explicit graphics resources;
- every non-transparent map palette index is inside the selected map palette
  resource;
- color index 0 remains alpha-transparent;
- no runtime VRAM/CGRAM payload is required.

The branch-A index-0 resource ranges were checked explicitly and are disjoint
from the map's used CHR/palette ranges.

## Remaining blocker

Tileset 58 remains unresolved only because layout 196 references one low/common
CHR tile, tile 0x0E0, once.  Packs 0xE3..0xE8 otherwise have a complete explicit
setup:

```text
10 1B
10 0D
11 37
```

The low VRAM region is not globally constant across runtime captures, so tile
0x0E0 is intentionally not guessed.  Its common/inherited CHR provenance must
be established before promotion.
