# CURRENT rolling handoff

Updated: 2026-09-28

> Canonical machine-readable state: `progress/current_task.json`.
> If this file disagrees with the JSON checkpoint, the JSON wins.

## Current task

- Status: **active**
- Workstream: `map-world-reconstruction`
- Title: **Enumerate map-selector bytecode and build the ROM map corpus index**
- Base main HEAD verified: `239bde84871231f256491527de610527dfdf9a11`

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
- Structurally bounded CA:C000 script-pack records expose a confirmed 65-command primary map-selector family: all use tileset 7 / variant 2 across 41 layouts; the stable interior's three occurrences are now proven inside valid record boundaries.
  - `data/maps/selectors/primary_map_selector_summary.json`
  - `docs/analysis/map_selector_family_20260928.md`
- A reproducible same-bank pack/record/substream parser now reproduces the 4,092-record corpus and expands the map-selector evidence to 261 structurally strong primary 0x50 candidates (65 previously confirmed signature rows), spanning 152 configurations / 149 layouts / 56 tilesets. 103 candidates have an immediate valid secondary 0x51 pair; 77 additional standalone 0x51 shapes remain mode-ambiguous because $1398 can route opcodes >=0x50 to the bank82 special VM.
  - `tools/python/catalog_map_selectors.py`
  - `data/maps/selectors/primary_map_selector_catalog.csv`
  - `data/maps/selectors/secondary_map_selector_candidates.csv`
  - `data/maps/selectors/primary_map_selector_summary.json`
  - `docs/analysis/map_selector_corpus_20260928.md`
- Special-dispatch instruction-boundary analysis promotes the map-selector corpus further: bank82-special opcode 0x50 advances exactly 2 bytes via C4:9BC5 -> C4:8410, so 70 of the 261 primary shapes have an impossible next opcode under special mode. Unioned with the 65 setup-signature rows, 126 primary selectors are now confirmed normal; 135 remain mode-gate unresolved. 53 immediate 0x51 rows are consequently confirmed normal secondary pairs.
  - `tools/python/catalog_map_selectors.py`
  - `data/maps/selectors/primary_map_selector_catalog.csv`
  - `data/maps/selectors/secondary_map_selector_candidates.csv`
  - `data/maps/selectors/primary_map_selector_summary.json`
  - `docs/analysis/map_selector_corpus_20260928.md`
  - `docs/hexdumps/shinmomo_82_8000_special_vm_handler_disasm_v1.txt`
- The four bank-crossing packs 0x15/0x48/0x9E/0xF2 are now parsed with the same 16-bit pointer-table grammar by incrementing the implied bank whenever record pointer words wrap. All 230 real packs parse with zero failures, expanding the bounded corpus from 4,092 to 4,324 VM records / 3,832 valid entry headers / 8,039 substreams. Two additional primary shapes and four secondary shapes are found; confirmed-normal counts remain 126 primary and 53 secondary pairs.
  - `tools/python/catalog_map_selectors.py`
  - `data/maps/selectors/primary_map_selector_catalog.csv`
  - `data/maps/selectors/secondary_map_selector_candidates.csv`
  - `data/maps/selectors/primary_map_selector_summary.json`
  - `docs/analysis/map_selector_corpus_20260928.md`
- Map mode-state dispatch is statically bounded: C0:CA04 copies $1399->$1398; C0:CA1A indexes C0:CA69 by 3*$1398; non-null states are 0,1,2,3,5,6 with routines 81:964E,82:8F1B,83:B7CD,86:82E2,85:CAA3,81:E331. State 4 is null/unwritten, and all six non-null states participate in one connected transition graph.
  - `docs/analysis/map_mode_state_dispatch_20260928.md`
- Full-pack unresolved-selector distribution is recomputed after adding the four bank-wrap packs: 263 primary shapes total, 126 confirmed normal and 137 unresolved; 118/137 unresolved rows (86.1%) are record 0, while later-record unresolved remains 19.
  - `docs/analysis/map_selector_unresolved_concentration_20260928.md`
  - `data/maps/selectors/primary_map_selector_catalog.csv`
- Pack reachability storage/inheritance is now concrete. The instruction-aligned master-pack loader entry is 84:8508 (not historical 8509), with five direct JSL callers. Mode 0 normalizes dynamic pack $0305, mode 1 fixed pack 0x19, mode 5 fixed pack 0x14, while modes 2/3/6 transition to 5/0/5. In the C4 VM scheduler, $126E is saved to and restored from per-slot $0759,X; nested execution inherits it, and normal opcode 0x04 explicitly replaces $126E and persists the new pack id to the current slot.
  - `tools/python/catalog_map_pack_context.py`
  - `data/maps/selectors/map_pack_context_summary.json`
  - `docs/analysis/map_pack_context_reachability_20260928.md`
  - `docs/analysis/map_pack_inverse_resolver_20260928.md`

## Observed but not yet promoted

- **confirmed_architecture**: 137 primary 0x50 rows remain mode-unresolved. Pack id alone cannot resolve them because $126E is per-C4-VM-slot context, survives scheduler resumes, is inherited by nested VM execution, and can be changed by normal opcode 0x04.
  - Why not promoted: Need to pair first/current slot script pointer and pack context with $1398 at dispatch, not assign one mode globally to a pack.
- **confirmed_catalog_distribution**: 118/137 unresolved primary selectors are record 0. Primary selector packs begin at 0x28; fixed mode-normalization packs 0x14 and 0x19 contain no primary candidates.
  - Why not promoted: Live slots can retain or switch pack context across mode transitions, so absence from the fixed seed packs does not prove state 0.
- **strong_structural_mode_unresolved**: 52 immediate 0x50+0x51 pairs and 79 standalone 0x51 shapes remain mode-unresolved after full-pack filtering.
  - Why not promoted: Their opcode meaning still depends on $1398 at execution.

## In progress

- Trace the C4 VM slot seed path from selected script pointer into first dispatch, pairing $98/$99/$9A, $126E/$0759,X and $1398 for each newly started slot.
- Emit reachable mode-state sets per pack/record/substream, prioritizing the 118 unresolved record-0 selectors and preserving multi-state reachability.
- Use those mode sets plus safe special-parser contradictions to classify remaining primary/secondary selector candidates.

## Next actions

1. Analyze the C4:8021..8090 slot creation/runner path and its callers to determine exactly where a fresh slot receives its initial script pointer and first $1398 dispatch state.
2. Catalog normal opcode 0x04 pack-context switches and nested-slot creation edges so pack reachability can be propagated per VM slot rather than per pack.
3. Emit per-pack/per-record/substream reachable mode-state metadata for the 118 unresolved record-0 selectors first; retain multiple states when control flow permits them.
4. Propagate confirmed normal-mode evidence into the 52 unresolved immediate 0x51 pairs and investigate the 79 standalone 0x51 shapes.
5. Cross-link confirmed selector pack/record/substream addresses with dialogue/event/location evidence to assign town/interior/dungeon/world labels.

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
- Do not treat all byte-shaped 0x50/0x51 rows as map selectors when $1398 mode is unresolved; opcode >=0x50 has a separate bank82 special dispatcher.
- Do not rederive the 4,092 record corpus manually; use tools/python/catalog_map_selectors.py.
- Do not include pack 0x14 record 0 (CA:CBF6..CA:D086) as a VM record; it is the one pointer/table blob excluded to reproduce 4,092.
- Do not assume a bank82-special 0x50 consumes four bytes; it is confirmed 2 bytes via C4:9BC5 -> C4:8410.
- Do not leave the map-selector confirmed count at 65; the static special-parse impossibility test raises the confirmed normal primary union to 126.
- Do not exclude packs 0x15/0x48/0x9E/0xF2 from selector enumeration; their 16-bit record pointers wrap into the next bank and the full parser handles them.
- Do not use 4,092 as the complete record-corpus size; it is the same-bank subset. The full 230-pack corpus has 4,324 bounded VM records after excluding pack 0x14 record 0.
- Do not model $1398/$1399 as a boolean flag; six non-null states 0,1,2,3,5,6 form a connected finite-state graph and state 4 is null.
- Do not use the old 261/135 selector backlog after full-pack parsing; canonical full-pack counts are 263 total, 126 confirmed normal, 137 unresolved.
- Do not use historical C4/84:8509 as the master-pack loader entry; the instruction-aligned entry is 84:8508 (file mirror C4:8508).
- Do not give $0759 a universal pack-id meaning. Only the C4 VM scheduler path at 84:8016/8070 is confirmed to overlay $0759,X with $126E; other object families reuse the column differently.
- Do not assign one mode state to an entire pack. C4 VM slots preserve/inherit $126E independently and normal opcode 0x04 can switch the current slot pack context.

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
- `data/maps/selectors/primary_map_selector_summary.json`
- `docs/analysis/map_selector_family_20260928.md`
- `tools/python/catalog_map_selectors.py`
- `data/maps/selectors/primary_map_selector_catalog.csv`
- `data/maps/selectors/secondary_map_selector_candidates.csv`
- `docs/analysis/map_selector_corpus_20260928.md`
- `docs/analysis/map_mode_state_dispatch_20260928.md`
- `docs/analysis/map_selector_unresolved_concentration_20260928.md`
- `tools/python/catalog_map_pack_context.py`
- `data/maps/selectors/map_pack_context_summary.json`
- `docs/analysis/map_pack_context_reachability_20260928.md`
- `docs/analysis/map_pack_inverse_resolver_20260928.md`

## Resume instruction

On a short request such as **「続きを進めて」**:

1. verify latest `main`;
2. read `progress/current_task.json`;
3. preserve newer parallel results;
4. continue from the first unfinished `next_actions` entry;
5. do not redo `done` / `do_not_redo` items;
6. checkpoint again after the next meaningful durable result.
