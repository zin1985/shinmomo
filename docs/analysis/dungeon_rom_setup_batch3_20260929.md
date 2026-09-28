# ROM-derived dungeon/special map batch 3 — 2026-09-29

## Scope

This batch records ten additional normal-map families that are fully covered by their
ROM setup resources and pass the strict renderer checks introduced after the tileset-8
proof.

The output should be understood as dungeon/interior/special-map reconstruction. Human
location names are intentionally unresolved until pack/event/dialogue evidence supplies
them.
## Families

| tileset | graphics setup | palette setup | layout |
|---:|---|---|---:|
| 31 | `10 1B / 10 0D` | `11 1E` | 142 |
| 33 | `10 10 / 10 11` | `11 20` | 146 |
| 35 | `10 10 / 10 11` | `11 22` | 149 |
| 36 | `10 10 / 10 11` | `11 23` | 150 |
| 38 | `10 1B / 10 0D` | `11 1E` | 154 |
| 43 | `10 12 / 10 15` | `11 25` | 165 |
| 46 | `10 13 / 10 14` | `11 2C` | 170 |
| 47 | `10 13 / 10 16` | `11 2D` | 172 |
| 48 | `10 13 / 10 16` | `11 2E` | 174 |
| 49 | `10 13 / 10 16` | `11 2F` | 176 |
## Validation policy

For every rendered layout:

1. all referenced 4bpp tile IDs must fall entirely within the VRAM byte ranges loaded
   by the specified opcode-0x10 graphics resources;
2. all used non-zero palette indices must be contained by the selected opcode-0x11
   palette resource;
3. color index 0 is transparent for normal SNES BG rendering.

The renderer rejects the map instead of producing a PNG when either CHR or palette
coverage is incomplete.

The same graphics decoder remains independently proven by exact equality against the
known runtime tileset-7 VRAM sample.
## Visual sanity checks

Representative maps in this batch form coherent structures including:

- pale cave chambers with vegetation/debris;
- large building/interior room sequences;
- shrine/ritual-room-like architecture;
- dark stone corridors;
- cliff/plateau maps and bridge structures;
- water-side cave/settlement-like areas;
- compact cave room groups.

These are structural descriptions only and are not canonical place-name assignments.

## Canonical directories

- `data/maps/rendered/dungeon_tileset_31/`
- `data/maps/rendered/dungeon_tileset_33/`
- `data/maps/rendered/dungeon_tileset_35/`
- `data/maps/rendered/dungeon_tileset_36/`
- `data/maps/rendered/dungeon_tileset_38/`
- `data/maps/rendered/dungeon_tileset_43/`
- `data/maps/rendered/dungeon_tileset_46/`
- `data/maps/rendered/dungeon_tileset_47/`
- `data/maps/rendered/dungeon_tileset_48/`
- `data/maps/rendered/dungeon_tileset_49/`

Each directory contains a map-ID PNG/JSON pair plus `resources.json`,
`palette.json`, and `index.json`.
