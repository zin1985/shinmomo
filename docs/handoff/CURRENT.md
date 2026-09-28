# CURRENT rolling handoff

Updated: 2026-09-28

> Canonical machine-readable state: `progress/current_task.json`.
> If this file disagrees with the JSON checkpoint, the JSON wins.

## Current task

- Status: **active**
- Workstream: `map-world-reconstruction`
- Title: **Enumerate map-selector bytecode and build the ROM map corpus index**
- Base main HEAD verified: `f3d05c32197affb274005fc54b6d0add87e954ba`

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
- State-0 map-entry reachability is now explicit: 81:964E calls 81:98D1, which loads current pack id $0305 through 84:8508 and immediately requests entry_id 0x01 through 84:858D. 84:859A starts scanning the pack record table at record index 0, and 84:8699 is the runtime reader for the proven [entry_id][ptr16]...00 record header. All 226 primary selectors in record 0 are entry 0x01, including all 118 unresolved record-0 rows.
  - `docs/analysis/map_pack_entry_paths_20260928.md`
  - `data/maps/selectors/primary_map_selector_catalog.csv`
- CA:C2F4 is fully reconstructed as a 250-entry per-pack seed index. IDs 0x01..0x13 are null; 231 list pointers cover 0x14..0xFA; 55 packs have 90 non-zero seed scripts. Every seed is inside the same-numbered CA:C000 pack and exactly at a valid entry_id 0x79 substream start, with zero malformed lists or pack mismatches. This seed family is separate from record0/entry1 map initialization.
  - `tools/python/catalog_map_pack_seeds.py`
  - `data/maps/selectors/map_pack_entry79_seed_catalog.csv`
  - `data/maps/selectors/map_pack_entry79_seed_summary.json`
  - `docs/analysis/map_pack_entry_paths_20260928.md`
- A conservative normal-mode prefix decoder now walks all 118 unresolved record0/entry1 selectors using only independently proven opcode lengths. 56 prefixes in 56 packs reach the candidate 0x50 with exact instruction alignment; 62 stop at the first unapproved opcode. No selector is promoted yet because mode-state mutation through decoded handler call graphs still needs proof.
  - `tools/python/analyze_map_selector_prefixes.py`
  - `data/maps/selectors/record0_entry1_prefix_analysis.csv`
  - `data/maps/selectors/record0_entry1_prefix_summary.json`
  - `docs/analysis/map_selector_prefix_decode_20260928.md`
- Mode-safety analysis of the 56 fully aligned record0/entry1 prefixes narrows the static blocker sharply. Opcode 0x96 and 0x11 chains have no direct $1398/$1399/C0:C9E7 references in their bounded callees. Opcodes 0x10/0x33 converge on B7A7/B7FA; their bounded direct call graph is also clean, leaving B910's descriptor-indexed indirect JSR as the specific unresolved mode-safety edge.
  - `docs/analysis/map_selector_prefix_mode_safety_20260928.md`
  - `docs/analysis/map_selector_prefix_decode_20260928.md`
- State-0 prefix mode persistence is now strong enough to promote 55 previously unresolved record0/entry1 primary selectors. The entry1 helper 81:98D1 explicitly seeds $035F=2; the 55 prefixes use only 0x96/0x10/0x11/0x33, preserve $035F/$1398/$1399, and every descriptor-resolved B910 indirect target collapses to the cleared B924/B944 routines. Confirmed primary rises 126->181 and unresolved falls 137->82; 31 immediate 0x51 rows are promoted, raising confirmed secondary pairs 53->84.
  - `tools/python/catalog_map_selectors.py`
  - `data/maps/selectors/primary_map_selector_catalog.csv`
  - `data/maps/selectors/secondary_map_selector_candidates.csv`
  - `data/maps/selectors/state0_safe_prefix_promotions.csv`
  - `data/maps/selectors/primary_map_selector_summary.json`
  - `docs/analysis/map_selector_state0_promotion_20260928.md`
  - `docs/analysis/map_selector_prefix_mode_safety_20260928.md`

## Observed but not yet promoted

- **confirmed_alignment**: One instruction-aligned record0/entry1 primary selector still uses opcode 0x15 in addition to the now-proven 0x96/0x10/0x11/0x33 family.
  - Why not promoted: Opcode 0x15 writes $1134 and calls 80:BAB8; its effect on $035F/render state must be bounded before state0 persistence can be claimed.
- **confirmed_decoder_backlog**: The conservative prefix decoder still stops 62 original rows at A3/B3/E8/3D/A0/E1/D0/B4/64. After the 55-row promotion, those families plus the 0x15 row dominate the record0/entry1 static backlog.
  - Why not promoted: Each stopped opcode family needs an independently proven length/control-flow/mode-safety model.
- **strong_structural_mode_unresolved**: 21 immediate 0x50+0x51 pairs and 79 standalone 0x51 shapes remain mode-unresolved after the new primary promotion.
  - Why not promoted: Their opcode meaning still depends on $1398 at execution.

## In progress

- Bound opcode 0x15 and its BAB8-side effects for the single remaining fully aligned record0/entry1 prefix.
- Then add safe length/control-flow handling for the largest blocked prefix families, starting with A3 and B3.
- Propagate every new primary confirmation into immediate 0x51 pair status.

## Next actions

1. Analyze opcode 0x15 (84:8AE0) and 80:BAB8/related $1134->$035F paths; promote the one aligned row only if state0 normal-mode persistence remains proven.
2. Reverse the A3 prefix opcode family enough to establish exact instruction length/control flow and mode-state side effects; rerun the conservative prefix decoder.
3. Do the same for B3, then E8/3D/A0/E1/D0/B4/64 in descending backlog size.
4. Use runtime trace hooks only for residual branch/wait/multi-mode cases.
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
- Do not merge CA:C2F4 entry-0x79 seed scripts with record0/entry-0x01 map initialization; they are separate dispatch families.
- Do not bulk-promote the 118 record0 unresolved selectors merely because state0 seeds entry1. VM commands are scheduled discretely and global $1398 is not stored per slot; prove mode persistence to each 0x50 boundary.
- Do not promote record0/entry1 selectors solely because the prefix decoder reaches 0x50; mode-state safety of every decoded handler/callee still has to be proven.
- Do not guess lengths for A3/B3/E8/3D/A0/E1/D0/B4/64; the safe decoder must stop until each family is independently bounded.
- Do not treat the raw B91C bytes as a flat valid code-pointer table without resolving the descriptor-derived $1123 index domain.
- Do not promote the 55 aligned 0x96/0x10/0x11/0x33 prefixes until the reachable B910 indirect targets are bounded.
- Do not keep the old canonical map-selector counts 126 confirmed / 137 unresolved after the state0 safe-prefix proof; the reproducible catalog now yields 181 confirmed / 82 unresolved.
- Do not treat all possible game-wide $035F values as relevant to state0 record0/entry1. 81:98D1 explicitly seeds $035F=2 immediately before the entry1 VM is started.
- Do not treat B91C as an unresolved wide indirect table for the promoted state0 family; descriptor resolution restricts it to B924/B944 only.

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
- `tools/python/catalog_map_pack_seeds.py`
- `data/maps/selectors/map_pack_entry79_seed_catalog.csv`
- `data/maps/selectors/map_pack_entry79_seed_summary.json`
- `docs/analysis/map_pack_entry_paths_20260928.md`
- `tools/python/analyze_map_selector_prefixes.py`
- `data/maps/selectors/record0_entry1_prefix_analysis.csv`
- `data/maps/selectors/record0_entry1_prefix_summary.json`
- `docs/analysis/map_selector_prefix_decode_20260928.md`
- `docs/analysis/map_selector_prefix_mode_safety_20260928.md`
- `data/maps/selectors/state0_safe_prefix_promotions.csv`
- `docs/analysis/map_selector_state0_promotion_20260928.md`

## Resume instruction

On a short request such as **「続きを進めて」**:

1. verify latest `main`;
2. read `progress/current_task.json`;
3. preserve newer parallel results;
4. continue from the first unfinished `next_actions` entry;
5. do not redo `done` / `do_not_redo` items;
6. checkpoint again after the next meaningful durable result.
