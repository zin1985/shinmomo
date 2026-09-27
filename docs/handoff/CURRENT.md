# CURRENT rolling handoff

Updated: 2026-09-28

> Canonical machine-readable state: `progress/current_task.json`.
> If this file disagrees with the JSON checkpoint, the JSON wins.

## Current task

- Status: **active**
- Workstream: `map-world-reconstruction`
- Title: **Trace resident tilemap pages back to the ROM-side map loader**
- Base main HEAD verified: `1c27a16ca53229b1c8127dc742582612181e34d1`

Trace the load path that populates the confirmed scene-specific VRAM pages
`0x1000` and `0x1800`, through DMA/CPU VRAM transfer and any WRAM
staging/decompression, to a candidate ROM pointer/table or canonical map record.

## Completed checkpoint

The first reproducible L1 structural map sample is complete.

Two independent same-room captures preserve:

- VRAM `0x1000`: 0 byte differences, 61 unique entries, 35 2x2 metatiles
- VRAM `0x1800`: 0 byte differences, 25 unique entries, 16 2x2 metatiles

A transition control rewrites:

- `0x1000`: 2047 / 2048 bytes
- `0x1800`: 2048 / 2048 bytes

Controls:

- `0xA000` stays identical across the transition and is not promoted as this
  scene's map page.
- `0xC000` changes by 64 bytes even between same-room captures and is treated
  as dynamic/control data.

Canonical evidence:

- `data/maps/samples/stable_interior_l1.json`
- `data/maps/samples/stable_interior_l1_evidence.json`
- `docs/analysis/map_sample_stable_interior_l1.md`
- `tools/python/summarize_tilemap_evidence.py`

## Definition of done for current task

- identify at least one writer/DMA path that populates VRAM `0x1000..0x1FFF`;
- connect it to source buffer/pointer or decompressor/decoder;
- identify a ROM-side source range, table or map-record candidate;
- commit the result without raw ROM/VRAM payloads.

## Next actions

1. verify latest `main`;
2. inspect existing graphics/mapchip/DMA evidence before inventing another loader theory;
3. search disassembly for VRAM address setup / DMA transfers targeting `0x1000/0x1800`;
4. use stable-room runtime load only if static evidence leaves multiple candidates;
5. connect transfer source to WRAM/decompressor/ROM table;
6. checkpoint before broadening to whole-ROM map enumeration.

## Do not redo

- pause/exact-frame remote-lab redesign;
- weak screenshot-correlation as proof of BG parameters;
- promotion of `0xA000` as this interior map page;
- raw ROM/savestate/SRAM/VRAM/CGRAM/OAM commits;
- older handoff overwrite of newer `main`.

## Runtime-only captures

- `%LOCALAPPDATA%/shinmomo-lab/map_captures/1790519691664-3fe31160_save_point_interior`
- `%LOCALAPPDATA%/shinmomo-lab/map_captures/1790524923212-b2fd20a4_stable_interior_l1`
- `%LOCALAPPDATA%/shinmomo-lab/map_captures/1790520426924-2a33d5df_field_transition_probe`

## Resume instruction

On **「続きを進めて」**: read `progress/current_task.json`, verify latest main,
continue from the first unfinished next action, and do not redo completed work.
