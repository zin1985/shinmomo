# ROM-derived dungeon/special map batch 4 — 2026-09-29

## Scope

This batch extends the strict ROM-only normal-map renderer to ten additional
families. Every committed image is reconstructed from ROM layout/metatile data,
opcode-0x10 graphics resources and opcode-0x11 palette resources.

No runtime VRAM/CGRAM dump is used for these outputs.

## Families

| tileset | graphics setup | palette setup | layouts |
|---:|---|---|---|
| 7  | `10 0A / 10 0B` | `11 09` | 42 layouts: 7,9,10,11,12,13,14,15,16,22,23,24,25,26,27,33,36,46,47,48,49,50,51,52,53,54,55,56,63,64,65,67,68,69,71,72,75,76,78,80,84,90 |
| 11 | `10 0C` | `11 0C` | 101 |
| 17 | `10 0E` | `11 15` | 111 |
| 21 | `10 0C / 10 0F` | `11 16` | 119 |
| 26 | `10 0E` | `11 1C` | 131 |
| 34 | `10 0E` | `11 21` | 148 |
| 40 | `10 13` | `11 26` | 157, 159 |
| 45 | `10 13` | `11 2A` | 168 |
| 56 | `10 1A` | `11 36` | 194 |
| 59 | `10 1C` | `11 38` | 201 |

Tileset 21 also contains an alternate `11 17` path in its selector prefix,
but that palette does not cover all non-transparent indices used by layout 119
and is therefore not promoted.

## Validation policy

The same fail-closed checks used by earlier dungeon batches apply:

1. every referenced 4bpp tile must be completely contained in graphics regions
   reconstructed from the selected opcode-0x10 resources;
2. every used non-zero palette index must be inside the selected opcode-0x11
   resource;
3. normal BG color index 0 is emitted as alpha transparency;
4. any incomplete resource set rejects the render instead of producing a
   plausible-looking but unsupported PNG.

Representative outputs were visually inspected and form coherent structures,
including interiors, cave networks, special terrain, large facilities, forest
maps and a ship map. These descriptions are structural only; human-facing place
names remain unresolved until pack/event/dialogue evidence proves them.

## Canonical directories

- `data/maps/rendered/dungeon_tileset_07/`
- `data/maps/rendered/dungeon_tileset_11/`
- `data/maps/rendered/dungeon_tileset_17/`
- `data/maps/rendered/dungeon_tileset_21/`
- `data/maps/rendered/dungeon_tileset_26/`
- `data/maps/rendered/dungeon_tileset_34/`
- `data/maps/rendered/dungeon_tileset_40/`
- `data/maps/rendered/dungeon_tileset_45/`
- `data/maps/rendered/dungeon_tileset_56/`
- `data/maps/rendered/dungeon_tileset_59/`

Each directory contains map-ID PNG/JSON pairs plus `resources.json`,
`palette.json`, and `index.json`.

## Remaining blockers

The next rejected families fall mainly into two groups:

- opcode-0x10 descriptors using graphics reader dispatch 0, which the current
  ROM renderer deliberately does not decode yet;
- families whose immediate selector prefix does not account for every CHR
  region referenced by the map, indicating inherited/common graphics setup that
  must be modeled explicitly rather than guessed.

The next implementation target is therefore the dispatch-0 graphics reader,
followed by inherited/common CHR setup recovery.
