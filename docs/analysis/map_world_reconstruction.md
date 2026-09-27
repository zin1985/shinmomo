# Map / World Reconstruction Workstream

Updated: 2026-09-27

## Goal

Salvage the world map, villages/towns/castles, interiors and dungeon floors as
machine-readable map data, not only screenshots.

Target reconstruction layers:

1. resident BG tilemap and palettes;
2. canonical tiles / 2x2 metatiles / larger reusable chunks;
3. complete map layout;
4. map identity and inter-map topology;
5. collision / passability;
6. entrances, exits and warps;
7. NPC / object spawn positions;
8. event trigger coordinates and conditions;
9. encounter regions or map-specific battle metadata;
10. ROM-side source format / compression / loader so all maps can be extracted
    without manually visiting every coordinate.

## Evidence already present

Existing graphics work already established the runtime reconstruction path:

```
VRAM tilemap
-> tile / palette / priority / hflip / vflip
-> repeated 2x2 metatile
-> chunk
-> reconstructed map preview
```

Relevant pre-existing assets:

- `docs/mapchip/FIELD_TILEMAP_METATILE_PIPELINE_AFTER_MERGE.md`
- `docs/graphics/MAPCHIP_CANONICALIZATION_SPEC_20260503.md`
- `docs/graphics/MAP_LAYOUT_RECONSTRUCTION_SPEC_20260503.md`
- `docs/graphics/MAP_VALIDATION_SPEC_20260503.md`
- `tools/python/build_field_metatiles_from_tilemap_v1.py`
- `tools/python/build_tile_adjacency_v2.py`
- `tools/python/infer_tilemap_layout_v2.py`
- legacy full graphics/mapchip BizHawk probes.

The missing step was turning this into a repeatable scene-by-scene inventory and
then tracing the resident tilemap back to its ROM-side loader/source.

## Canonical acquisition path

Current acquisition uses the deterministic remote lab:

```
tools/remote_lab/shinmomo_lab.ps1 map-capture -SceneTag <tag>
```

It stores outside Git:

- `vram.bin`
- `cgram.bin`
- `oam.bin`
- current game screenshot
- `manifest.json` containing frame number, memory-domain names and mirrored
  PPU BG registers.

Raw ROM-derived memory dumps remain local and are not committed.

Derived reconstruction:

```
python tools/python/reconstruct_map_capture.py <capture_dir>
```

Output:

- `scene_summary.json`
- `bg1..bg4_tilemap.csv`
- `bg1..bg4_metatile_2x2.csv`
- `bg1..bg4_preview.ppm`

Only derived metadata/inventory needed for reverse engineering is promoted into
GitHub.

## Identity model

Do not equate a screenshot with a complete map.

- **scene_capture**: one deterministic runtime snapshot.
- **map_variant**: one logical loaded map state / palette / season / story
  variant.
- **map**: one traversable logical map such as a village, indoor room or dungeon
  floor.
- **map_group**: multi-floor dungeon, town plus interiors, castle complex, etc.
- **world_region**: overworld/world-map region or mode.

The same map may require multiple scene captures because the game can stream
tilemap/chunk data while scrolling.

## Scene classes

Use one of:

- `world`
- `field`
- `town`
- `castle`
- `indoor`
- `dungeon`
- `special`
- `unknown`

Dungeon floors are separate maps unless loader evidence proves a shared map with
a floor parameter.

## Completion levels

### L0 screenshot only
Visible screen recorded. No structural claim.

### L1 resident BG recovered
VRAM/CGRAM/PPU-backed tilemap reconstruction succeeds.

### L2 streamed map stitched
Multiple scroll positions are joined into a stable layout.

### L3 logic layers attached
Collision, warp, object/NPC and event trigger coordinates are attached.

### L4 canonical ROM source identified
Loader, pointer/table, compression and source range are known.

### L5 corpus complete
Every map/floor/variant is enumerable and reproducibly exported without manual
play traversal.

## Immediate high-leverage experiment

1. capture the currently reachable field map with `map-capture`;
2. verify BG register mirror and reconstruct resident tilemap;
3. move exactly one screen in four directions under deterministic frame control;
4. capture again and compare tilemap pages / DMA sources;
5. determine whether scrolling is:
   - fixed full-map resident tilemap,
   - ring-buffer/streamed tilemap,
   - chunk/page swapped;
6. use changed VRAM ranges and DMA source addresses to identify the map loader;
7. follow loader pointers back into ROM and derive the canonical map table.

This is the shortest path from visible map recovery to whole-ROM automatic map
salvage.

## Progress policy

This workstream contributes primarily to:

- G1: ROM/data format and loader reconstruction;
- G4: event/trigger spatial linkage;
- G5: portable map specification.

Do not increase top-level progress from screenshot counts alone. Promotion
requires reusable structural evidence or new canonical extraction coverage.
