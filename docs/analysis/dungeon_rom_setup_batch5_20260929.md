# ROM-derived dungeon/special map batch 5 — 2026-09-29

## Result

This batch extends the strict ROM-only normal-map renderer to graphics reader
dispatch 0 and adds ten more map families.

No runtime VRAM or CGRAM payload is committed. All PNGs are derived from the
canonical ROM, normal-VM setup resources, CE metatile definitions and CF layouts.

Every promoted family passes the same fail-closed coverage rules as earlier batches:
all referenced 4bpp tiles are contained in setup-selected graphics resources and
all non-transparent palette indices are covered by the setup-selected opcode-0x11
palette resource.
## Dispatch-0 decoder proof

Graphics reader dispatch 0 is initialized by `C0:BCEE` and supplies bytes through
`C0:BD28`.

It uses a 256-byte zero-filled dictionary page, write cursor `0xEF`, MSB-first
flag bits, and paired back-reference length nibbles.

A subtle runtime detail is essential: after loading nibble+1 into `$7D`, the
reader immediately copies one byte at `BD2E`; `$7D` is decremented only on
later reader calls. Therefore the effective back-reference length is
**nibble+2 (2..17 bytes)**.

The decoder is runtime-validated against the stable 旅立ちの村 sample
(pack 0x50 / tileset 4 / layout 8), whose setup is:

```text
10 04
10 05
10 06
11 06
```
All three dispatch-0 graphics resources match captured runtime VRAM byte-for-byte:

| operand | VRAM byte range | bytes | equality | SHA-256 |
|---:|---|---:|---:|---|
| `04` | `0x2000..0x3FFF` | 8192 | 8192/8192 | `5A46C7C034A1B8ED95A28B099DDFB3D8CFE847C74D1ED7628707BEAA673D5052` |
| `05` | `0x4000..0x5FFF` | 8192 | 8192/8192 | `CFF02340DCF73FB38526945452119EA5E2B20A440896599D631F735CD7A8E984` |
| `06` | `0x6000..0x6BDF` | 3040 | 3040/3040 | `04F9F6494749C1A7D10983C48CF384DEE896741937F6B1FB73301682504A50CD` |

The same runtime ranges have identical hashes across 25 stable pack-0x50
captures, independently fixing the comparison target.
## Families in this batch

| tileset | graphics setup | palette setup | layouts |
|---:|---|---|---|
| 6  | `10 04 / 10 05 / 10 07` | `11 07` | 21, 37, 38, 40 |
| 39 | `10 12` | `11 25` | 156 |
| 44 | `10 12` | `11 2B` | 167 |
| 50 | `10 17 / 10 18` | `11 30` | 178 |
| 51 | `10 17 / 10 19` | `11 31` | 180 |
| 52 | `10 17 / 10 18` | `11 32` | 182 |
| 53 | `10 17 / 10 18` | `11 33` | 184, 186, 188 |
| 54 | `10 17 / 10 19` | `11 34` | 190 |
| 55 | `10 17 / 10 19` | `11 35` | 192 |
| 60 | `10 1D` | `11 39` | 203 |

Tilesets 6 and 50..55/60 exercise the newly proven dispatch-0 reader.
Tilesets 39 and 44 use the already proven dispatch-2 reader.
## Visual sanity check

Representative outputs were inspected after strict resource validation. They form
coherent structures rather than random tile assemblies, including forest/road
facilities, mountain regions, room/building collections, sand/stone compounds,
large multi-area complexes and narrow special maps.

Some maps contain strong non-transparent palette colors. These are retained
because the used indices are explicitly covered by their ROM opcode-0x11 resource;
no appearance-based recoloring is applied.

Human-facing place names remain unresolved unless independently bound by runtime,
dialogue or other direct evidence.
## Canonical outputs

- `tools/python/render_normal_map_family_from_setup.py`
- `data/maps/rendered/dungeon_tileset_06/`
- `data/maps/rendered/dungeon_tileset_39/`
- `data/maps/rendered/dungeon_tileset_44/`
- `data/maps/rendered/dungeon_tileset_50/`
- `data/maps/rendered/dungeon_tileset_51/`
- `data/maps/rendered/dungeon_tileset_52/`
- `data/maps/rendered/dungeon_tileset_53/`
- `data/maps/rendered/dungeon_tileset_54/`
- `data/maps/rendered/dungeon_tileset_55/`
- `data/maps/rendered/dungeon_tileset_60/`

Each directory contains map-ID PNG/JSON pairs, `resources.json`,
`palette.json`, and `index.json`.

## Still unresolved

The remaining normal-map families fail closed because their selector prefix does
not yet account for every required graphics region (often opcode 0x33 or inherited
resources). Tilesets 2 and 3 use mode-0x01 layouts and require the separate
Mode-7/world-style path rather than this normal 4bpp renderer.
