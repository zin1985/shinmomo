# Stable interior L1 map sample

Updated: 2026-09-28

## Result

The first reproducible runtime map sample has been promoted to **L1 structural
map evidence**.

The scene is an indoor room loaded from save slot 1. The exact in-game location
name is intentionally not asserted here because the current runtime evidence
does not prove the canonical map ID/name.

Two independent same-room captures were compared:

- `1790519691664-3fe31160`
- `1790524923212-b2fd20a4`

A third capture taken during a different transition state was used as a control:

- `1790520426924-2a33d5df`

Raw VRAM/screenshots remain outside Git.

## Promoted resident pages

### VRAM 0x1000

Same-room captures:

- identical SHA-256:
  `d73a0a85e3d7d36b5a88098c0ee9e7489d5e8fcfb3940769ac84ea9c8ef95549`
- 0 byte differences
- 61 unique 16-bit entries
- 36 unique tile IDs
- 35 unique non-overlapping 2x2 metatiles
- 2x2 metatile repeat ratio: 0.863281
- priority=1 ratio: 0.035156

Transition control:

- 2047 / 2048 bytes differ from the stable interior page
- transition SHA-256:
  `cec8327fc5a9db7591e7b65c5edbbb989d9d074fa2bbdc11781975887a3760f3`

Interpretation: **scene-specific resident tilemap/background page**.

### VRAM 0x1800

Same-room captures:

- identical SHA-256:
  `13869125883c0c371b11ff3b6ec072fb021d4e25b928f3facb1e18fd4df4b379`
- 0 byte differences
- 25 unique 16-bit entries
- 21 unique tile IDs
- 16 unique non-overlapping 2x2 metatiles
- 2x2 metatile repeat ratio: 0.937500
- priority=1 ratio: 0.007812

Transition control:

- 2048 / 2048 bytes differ from the stable interior page
- transition SHA-256:
  `2be0d90478f0d843683b03204cdb9009db921c9f086f54a9a10e37389c57bcde`

Interpretation: **scene-specific resident tilemap/background page**, likely a
secondary/simple layer. The exact BG number is not yet proven.

## Negative controls

### VRAM 0xA000

The page looked structurally map-like in the heuristic ranker, but its SHA-256
is identical across both interior captures **and the transition control**:

`9cc156497a98a3191f79391d8dd091149572bdefdd7347ad8fbfc7a06c755d0d`

It is therefore not promoted as this interior's scene-specific map page.

### VRAM 0xC000

This page changes even while the room background remains the same:

- 64 byte differences between the two same-room captures
- 93 byte differences versus the transition control

This makes it a useful dynamic/control page but not a stable background page for
this sample.

## Why this is enough for the first L1 structural sample

The evidence now separates:

1. scene-stable background structure (`0x1000`, `0x1800`);
2. a scene-invariant false-positive candidate (`0xA000`);
3. a dynamic page that changes while the room itself is unchanged
   (`0xC000`).

The result is reproducible from raw runtime VRAM using committed tools without
putting the raw VRAM into Git.

Canonical metadata:

- `data/maps/samples/stable_interior_l1.json`
- `data/maps/samples/stable_interior_l1_evidence.json`

Reproducer:

- `tools/python/rank_vram_tilemap_pages.py`
- `tools/python/summarize_tilemap_evidence.py`

## Remaining unknowns

L1 here is structural, not yet a fully colored independent render.

Still unresolved:

- exact BG1/BG2/BG3 assignment;
- BGMODE / bpp;
- character/tile graphics base;
- palette assignment;
- scroll registers;
- whether these 32x32 resident pages are the whole room or streamed windows;
- collision / warp / event layers;
- canonical ROM-side map ID, loader, compression and source ranges.

The screenshot-correlation brute-force experiment is not strong enough to claim
the render parameters and remains negative evidence only.

## Next high-leverage target

Trace the writes that populate VRAM `0x1000..0x1FFF` during room/map load.

The desired chain is:

```
map/load state
-> DMA or CPU VRAM transfer
-> WRAM staging/source pointer
-> decompressor/decoder
-> ROM pointer/table
-> canonical map record
```

Once the ROM-side loader and record table are known, map salvage can move from
manual runtime visits toward whole-ROM enumeration for villages, world maps and
dungeon floors.
