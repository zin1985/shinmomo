# CURRENT rolling handoff

Updated: 2026-09-28

> Canonical machine-readable state: `progress/current_task.json`.
> If this file disagrees with the JSON checkpoint, the JSON wins.

## Current task

- Status: **active**
- Workstream: `map-world-reconstruction`
- Title: **Bind the L1 interior sample to exact ROM map IDs and decode its logical grid**
- Base main HEAD verified: `e36b8a1a3a1655be6bfc5ca4671d1bc796f9ac17`

Capture the stable interior sample's runtime map IDs ($139C-$139F), bind them to the catalogued CE:2000/CF:2000 entries, decode that exact CF layout record outside the emulator, expand its metatile IDs through the selected CE tileset, and compare the derived structure with the L1 runtime evidence.

## Definition of done

- A stable interior runtime capture records $139C-$139F (and relevant mode state such as $113C) without committing raw WRAM.
- The sample is bound to exact tileset/config and primary/secondary layout IDs in the derived ROM catalogs.
- A standalone decoder reproduces the selected CF layout record's logical cell grid from the canonical ROM.
- The selected CE tileset expands sample metatile IDs into SNES tile entries and is compared against the runtime-resident page evidence.
- stable_interior_l1 metadata is updated from global ROM-table candidates to exact sample-specific ROM references, with remaining collision/warp/event gaps recorded.

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

## Observed but not yet promoted

- **strong-global / sample-id-unresolved**: The L1 room is now connected to the global ROM-side map pipeline, but its exact runtime selector bytes $139C-$139F have not yet been captured.
  - Why not promoted: Exact CE/CF table entries for this particular room require one small derived WRAM capture.
- **confirmed-static**: CF:2000 contains exactly 203 valid packed 24-bit layout pointers; all records satisfy cell_count = width * height and all 202 non-final spans exactly match the inferred mode-dependent record length.
  - Why not promoted: This is promoted in the ROM-table catalog; only human place/floor naming remains unresolved.
- **confirmed-static / semantic-subrole-partial**: CE:2000 and CF:0000 each contain 60 non-FFFF word pointers and are indexed by the same tileset/config selector family.
  - Why not promoted: CE is strongly identified as metatile definitions; the exact semantic subrole of the parallel CF:0000 table remains provisional.

## In progress

- Capture $139C-$139F for the known stable interior sample under deterministic remote-lab control.
- Implement standalone decoding for the selected CF layout mode using the confirmed D157/D173 decoder dispatch.
- Compare decoded/expanded logical map structure with the sample's resident VRAM pages.

## Next actions

1. Resume the deterministic remote lab to the known stable interior scene and capture only derived values for $139C-$139F plus $113C; do not commit raw WRAM.
2. Resolve those IDs through data/maps/rom_tables catalogs to exact CF layout and CE tileset/config records, then update stable_interior_l1 metadata.
3. Implement a standalone decoder for the selected layout mode and emit a logical cell/metatile grid without exporting unrelated ROM payloads.
4. Expand the decoded metatile IDs through the selected CE metatile block and compare its tile-entry structure with VRAM 0x1000/0x1800 evidence.
5. After the sample is fully bound, trace the bank 83/84 producers of $139C-$139F and begin mapping human towns/world/dungeon floors to the 203 layout records.

## Do not redo

- Do not redesign the pause/exact-frame remote-lab model.
- Do not rerun the weak screenshot-correlation experiment as proof of BG parameters.
- Do not treat 0xA000 as the interior map page; it is unchanged across the transition control.
- Do not commit raw ROM, savestate, SRAM, VRAM, CGRAM or OAM dumps.
- Do not force older handoffs over newer main commits.
- Do not manually rescan CE:2000/CF:0000/CF:2000; use tools/python/catalog_map_rom_tables.py and the committed derived catalogs.
- Do not name the four layout decoder modes as standard compression formats until a standalone decoder reproduces a known sample.

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

## Resume instruction

On a short request such as **「続きを進めて」**:

1. verify latest `main`;
2. read `progress/current_task.json`;
3. preserve newer parallel results;
4. continue from the first unfinished `next_actions` entry;
5. do not redo `done` / `do_not_redo` items;
6. checkpoint again after the next meaningful durable result.
