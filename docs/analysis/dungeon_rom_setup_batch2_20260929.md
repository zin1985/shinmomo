# ROM-derived dungeon/special map batch 2 — 2026-09-29

## Scope

This batch extends the ROM-only normal-map renderer beyond tileset 8.

Every committed family in this batch passes strict resource coverage checks:

- every 4bpp tile referenced by the expanded layout is contained inside the graphics
  regions loaded by its `10 <operand>` setup commands;
- every non-transparent palette index used by the map is contained inside the
  palette range loaded by its `11 <operand>` setup command;
- normal-BG color index 0 is emitted as alpha transparency.

This prevents visually plausible but incompletely sourced maps from being promoted.
## Families in this batch

| tileset | graphics setup | palette setup | layouts |
|---:|---|---|---|
| 9  | `10 0C / 10 0D` | `11 0B` | 97, 98 |
| 13 | `10 0C / 10 0D` | `11 0D` | 103 |
| 14 | `10 0C / 10 0D` | `11 0E` | 105 |
| 14 | `10 0C / 10 0D` | `11 11` | 105 |
| 15 | `10 0C / 10 0D` | `11 0F` | 107 |
| 16 | `10 0C / 10 0D` | `11 10` | 109 |
| 18 | `10 0C / 10 0D` | `11 12` | 112 |
| 19 | `10 0C / 10 0D` | `11 13` | 113, 115 |
| 20 | `10 0C / 10 0D` | `11 14` | 117 |
| 27 | `10 0C / 10 0D` | `11 0A` | 132, 134 |

Tileset 14 deliberately has two canonical palette variants because two normal selector
families use the same layout and graphics resources with different opcode-0x11 operands.
## Validation basis

The graphics decoder used here is the same four-context codec proven against the
runtime tileset-7 sample:

- ROM `D3:A566` -> runtime VRAM byte `0x2000`: 100% byte equality.
- ROM `D3:BCE3` -> runtime VRAM byte `0x4000`: 100% byte equality.

The generic renderer was also independently run on the known
tileset-7 / layout-15 room using only ROM setup resources. Against the live game
screenshot, the best viewport was exactly `(32,32)`; despite NPC/dynamic-layer
differences, about 83.8% of pixels had mean RGB error <= 20.

This gives an external runtime check for both the decoded CHR and ROM-derived palette path.
## Visual sanity checks

Representative outputs were inspected after the strict coverage pass. They form coherent
map structures rather than random tile assemblies, including:

- large water/cave regions;
- lava/red-rock and orange platform maps;
- spike/ice-field regions;
- large rocky cave floors;
- small shrine/chamber-like interiors;
- compact cave-room groups.

These descriptions are structural only. Human-facing place names and story roles are not
assigned from appearance alone.

## Canonical directories

- `data/maps/rendered/dungeon_tileset_09/`
- `data/maps/rendered/dungeon_tileset_13/`
- `data/maps/rendered/dungeon_tileset_14_p0E/`
- `data/maps/rendered/dungeon_tileset_14_p11/`
- `data/maps/rendered/dungeon_tileset_15/`
- `data/maps/rendered/dungeon_tileset_16/`
- `data/maps/rendered/dungeon_tileset_18/`
- `data/maps/rendered/dungeon_tileset_19/`
- `data/maps/rendered/dungeon_tileset_20/`
- `data/maps/rendered/dungeon_tileset_27/`

Each directory contains map-ID PNG/JSON pairs plus `resources.json`,
`palette.json`, and `index.json`.
