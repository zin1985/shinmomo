# CURRENT rolling handoff

Updated: 2026-09-28

> Canonical machine-readable state: `progress/current_task.json`.
> If this file disagrees with the JSON checkpoint, the JSON wins.

## Current task

- Status: **active**
- Workstream: `map-world-reconstruction`
- Title: **Enumerate map-selector bytecode and build the ROM map corpus index**
- Base main HEAD verified: `b45743d1de57a0c712719a8d46bfdc36666123f6`

Enumerate opcode 0x50/0x51 map-selection commands through the bank-C4 record interpreter, join each command to the 60-entry tileset/config and 203-entry layout catalogs, and build a derived ROM map corpus index suitable for classifying villages, world-map regions, interiors and dungeon floors.

## Definition of done

- The bank-C4 interpreter path supplying the $98 script pointer is identified well enough to distinguish valid opcode streams from blind byte-pattern matches.
- A reproducible tool enumerates valid 0x50 primary and 0x51 secondary map-selection commands with ROM addresses and argument IDs.
- The command catalog is joined to exact CE tileset and CF layout pointers, dimensions, flags and decoder metadata.
- The stable interior's three known 50 07 0F 02 occurrences are represented in the catalog without duplicate false interpretation.
- Derived corpus metadata is committed and the next classification step for towns/world/dungeons is recorded.

## Done

- Map/world reconstruction workstream and completion levels L0..L5 defined.
  - `docs/analysis/map_world_reconstruction.md`
  - `data/maps/map_inventory_schema.json`
- Deterministic remote lab pauses between commands and advances only explicitly requested frames.
  - `tools/remote_lab/shinmomo_remote_bridge.lua`
  - `tools/remote_lab/shinmomo_lab.ps1`
- Remote-lab launcher supports unthrottled maximum-speed execution while preserving exact frame counts; normal speed remains available explicitly.
  - `tools/remote_lab/launch_bizhawk_remote_lab.ps1`
  - `tools/remote_lab/README.md`
- Runtime map capture command implemented for VRAM/CGRAM/OAM/screenshot/manifest where the active core exposes the relevant domains.
  - `tools/remote_lab/shinmomo_remote_bridge.lua`
  - `tools/remote_lab/shinmomo_lab.ps1`
- PPU-independent VRAM tilemap-page ranker implemented with fill/high-priority false-positive penalties.
  - `tools/python/rank_vram_tilemap_pages.py`
- VRAM plus screenshot BG-parameter inference prototype implemented; current correlations are candidate evidence only.
  - `tools/python/infer_bg_render_from_capture.py`
- PPU/CGRAM mirroring path was corrected to follow the proven BizHawk onmemorywrite call convention, but the active Snes9x core still needs a fresh stable-map validation capture.
  - `tools/remote_lab/shinmomo_remote_bridge.lua`
- First reproducible L1 structural map sample completed: same-scene captures preserve VRAM pages 0x1000 and 0x1800 byte-for-byte, while a transition control rewrites 2047/2048 bytes respectively.
  - `data/maps/samples/stable_interior_l1.json`
  - `data/maps/samples/stable_interior_l1_evidence.json`
  - `docs/analysis/map_sample_stable_interior_l1.md`
  - `tools/python/summarize_tilemap_evidence.py`
- Static C0:A0BA..A150 path classified as queued VRAM-to-VRAM copy via $7E:2000 staging; it is not yet the ROM-side map loader.
  - `docs/analysis/map_vram_transfer_path_20260928.md`
- ROM-side map loader path resolved to concrete CE/CF tables: CF:2000 has 203 packed 24-bit layout pointers with a verified 5-byte header and exact mode-dependent record sizes; CE:2000 has 60 tileset/metatile pointers; D0AE decodes layout data into a $7F staging grid before D19E expansion and $7E:8000/A1B9 VRAM upload.
  - `docs/analysis/map_rom_loader_tables_20260928.md`
  - `tools/python/catalog_map_rom_tables.py`
  - `data/maps/rom_tables/map_rom_table_summary.json`
  - `data/maps/rom_tables/tileset_pointer_catalog.csv`
  - `data/maps/rom_tables/layout_record_catalog.csv`
- The L1 interior sample is bound to exact ROM IDs: tileset 7 -> CE:44C0 and layout 15 -> CF:2E1D. A standalone four-selector decoder reproduces the layout's four $7F staging pages 1024/1024 bytes exactly; CE expansion yields a 64x32 tilemap matching 1934/2048 runtime VRAM words, with all 114 remaining differences equal to runtime blank value 0x0100.
  - `data/maps/samples/stable_interior_rom_binding.json`
  - `docs/analysis/stable_interior_rom_binding_20260928.md`
  - `tools/python/decode_map_layout.py`
  - `data/maps/samples/stable_interior_l1.json`
  - `data/maps/samples/stable_interior_l1_evidence.json`

## Observed but not yet promoted

- **confirmed-static**: C4:87BC dispatches one-byte record opcodes through the C4:87D4 word table; opcode 0x50 -> C4:8AF0 and opcode 0x51 -> C4:8B06.
  - Why not promoted: Promoted in the stable-interior binding analysis; the remaining issue is enumerating valid script-stream boundaries.
- **confirmed-static**: Opcode 0x50 format is [50, primary_tileset_id, primary_layout_id, map_variant], while 0x51 is [51, secondary_tileset_id, secondary_layout_id].
  - Why not promoted: Need a stream-aware corpus scanner rather than blind raw-byte enumeration.
- **confirmed-by-raw-search / entry-context-unresolved**: The exact stable-interior command 50 07 0F 02 occurs at CB:DE70, CC:5391 and CE:0F2B.
  - Why not promoted: These likely represent multiple entry scripts selecting the same map, but human entry-point labels remain unresolved.

## In progress

- Trace how the bank-C4 interpreter establishes and advances the $98 long pointer for valid bytecode streams.
- Build a stream-aware catalog of opcode 0x50/0x51 map-selector records.
- Join selector records to the existing ROM layout/tileset catalogs.

## Next actions

1. Trace C4:87BC/C4:87D4 interpreter callers and the $98-$9A long-pointer setup so valid command-stream boundaries can be enumerated.
2. Implement a derived-only map-selector catalog tool for opcodes 0x50/0x51; do not use blind global byte search as the final corpus.
3. Join selector arguments to data/maps/rom_tables layout and tileset catalogs and emit dimensions/flags/pointers for each map configuration.
4. Cross-link selector ROM addresses with existing event/dialogue/location evidence to begin assigning human town/interior/dungeon/world labels.
5. After the map corpus is stable, add collision/warp/event-trigger layers and export reproducible per-map metadata.

## Do not redo

- Do not redesign the pause/exact-frame remote-lab model.
- Do not rerun the weak screenshot-correlation experiment as proof of BG parameters.
- Do not treat 0xA000 as the interior map page; it is unchanged across the transition control.
- Do not commit raw ROM, savestate, SRAM, VRAM, CGRAM or OAM dumps.
- Do not force older handoffs over newer main commits.
- Do not manually rescan CE:2000/CF:0000/CF:2000; use tools/python/catalog_map_rom_tables.py and the committed derived catalogs.
- Do not name the four layout decoder modes as standard compression formats until a standalone decoder reproduces a known sample.
- Do not treat VRAM 0x1000 and 0x1800 as separate BG layers for the stable interior; they are confirmed left/right 32x32 screens of one 64x32 tilemap.
- Do not re-derive layout15/tileset7 by heuristic ranking; exact runtime selectors and ROM records are now confirmed.
- Do not catalog opcode 0x50/0x51 by blind byte search alone; require interpreter-stream boundaries or equivalent structural evidence.

## Runtime-only artifacts

- `%LOCALAPPDATA%/shinmomo-lab/map_captures/1790519691664-3fe31160_save_point_interior`
  - First same-room raw capture used for L1 page stability.
- `%LOCALAPPDATA%/shinmomo-lab/map_captures/1790524923212-b2fd20a4_stable_interior_l1`
  - Fresh stable-room capture at frame 3253 used for L1 page stability.
- `%LOCALAPPDATA%/shinmomo-lab/map_captures/1790520426924-2a33d5df_field_transition_probe`
  - Transition control used to prove that pages 0x1000/0x1800 are scene-specific.

## Canonical evidence / save locations

- `docs/project/ROLLING_WORK_PROTOCOL.md`
- `docs/analysis/map_world_reconstruction.md`
- `data/maps/map_inventory_schema.json`
- `tools/remote_lab/README.md`
- `tools/remote_lab/shinmomo_lab.ps1`
- `tools/remote_lab/shinmomo_remote_bridge.lua`
- `tools/remote_lab/launch_bizhawk_remote_lab.ps1`
- `tools/python/reconstruct_map_capture.py`
- `tools/python/rank_vram_tilemap_pages.py`
- `tools/python/infer_bg_render_from_capture.py`
- `data/maps/samples/stable_interior_l1.json`
- `data/maps/samples/stable_interior_l1_evidence.json`
- `docs/analysis/map_sample_stable_interior_l1.md`
- `tools/python/summarize_tilemap_evidence.py`
- `docs/analysis/map_rom_loader_tables_20260928.md`
- `tools/python/catalog_map_rom_tables.py`
- `data/maps/rom_tables/map_rom_table_summary.json`
- `data/maps/rom_tables/tileset_pointer_catalog.csv`
- `data/maps/rom_tables/layout_record_catalog.csv`
- `data/maps/samples/stable_interior_rom_binding.json`
- `docs/analysis/stable_interior_rom_binding_20260928.md`
- `tools/python/decode_map_layout.py`

## Resume instruction

On a short request such as **「続きを進めて」**:

1. verify latest `main`;
2. read `progress/current_task.json`;
3. preserve newer parallel results;
4. continue from the first unfinished `next_actions` entry;
5. do not redo `done` / `do_not_redo` items;
6. checkpoint again after the next meaningful durable result.
