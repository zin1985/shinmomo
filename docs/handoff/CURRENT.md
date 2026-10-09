# CURRENT rolling handoff

> **2026-10-10 VM56 entry CFG frontier:** Canonical ROM proves exact entry bounds for ten framed VM56 terminals; six have possible CFG paths under proven grammar, four have unresolved opcode/A0 blockers. No A4 selected-source site occurs within any matching substream; these are NOT actual caller proofs. Source-map bindings/Viewer edges unchanged. See docs/analysis/vm56_entry_cfg_frontier_20261010.md and progress/current_task.json.

> **2026-10-10 VM56 exact ROM verification:** 722/722 terminal opcode 0x56 pack/entry/B0 sequences verified against canonical ROM. Of 721 source-unbound VM56 rows, 10 have framed event records and 7 have validated source-selection callsite evidence. No new source-map links promoted. See docs/analysis/vm56_source_owner_audit_20261010.md, data/maps/transitions/vm56_source_ownership_audit.json and progress/current_task.json.

> **2026-10-10 spatial and phase gate:** 54 independent VM source regions now have conservative research-coordinate predicates, CC:1160 retains a five-config destination ambiguity, and 1,238 source-unbound transitions are triaged (721 opcode0x56 terminal). See docs/analysis/transition_spatial_phase_source_triage_20261010.md and progress/current_task.json; confirmed edges remain 3 of 56.

> **2026-10-10 native return and graph gate:** Two native return contexts attached to existing bound edges; all 1,295 transitions preserve unresolved current-state activation. 56 edges and 3 confirmed unchanged. World graph audit: only 3/149 maps have bound outgoing edges. Read docs/analysis/native_saved_return_graph_gate_20261010.md and progress/current_task.json.

> **2026-10-10 bounds graph update:** Viewer now has 56 edges (3 confirmed + 53 candidate), 110 new uniquely bounded destination configs, 1,173 resolved destination configs total. Resume from native-boundary context and phase-aware VM predicates; see docs/analysis/destination_bounds_viewer_overlay_20261010.md.

> **2026-10-10 graph continuation:** Exact address joining yielded 54 source bindings and 49 new strong-candidate edges, bringing Viewer edges to 52; confirmed stays 3. See docs/analysis/transition_source_hotspot_crosslink_20261010.md and progress/current_task.json.

> **2026-10-09 restart:** Current continuation is the canonical-ROM pack96 arrival frontier. Read progress/current_task.json and docs/handoff/HM_261009_analysis_resume.md first. The historical 2026-09-28 map-world task below is kept as evidence, not the next action.

Updated: 2026-09-28

> Canonical machine-readable state: `progress/current_task.json`.
> If this file disagrees with the JSON checkpoint, the JSON wins.

## Current task

- Status: **active**
- Workstream: `map-world-reconstruction`
- Title: **Render and identify ROM map layouts from canonical map-chip data**
- Base main HEAD verified: `2d38f9afc6efcd6dc760a0b7699b03a430b7bf9b`

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
- The single remaining fully aligned state0 record0/entry1 prefix containing opcode 0x15 is now promoted. CC:23D9 uses terminal 15 00 03; the synchronous C4:8AE0 -> 80:BAB8 -> 80:AC1E path does not mutate $1398/$1399 or re-enter C0:C9E7, and 0x15 is admitted only as the final instruction before 0x50 because its later callback may change $035F. Confirmed primary rises 181->182; unresolved 82->81; the immediate secondary CC:23DD is also promoted, raising confirmed pairs 84->85.
  - `tools/python/catalog_map_selectors.py`
  - `data/maps/selectors/state0_safe_prefix_promotions.csv`
  - `data/maps/selectors/primary_map_selector_catalog.csv`
  - `data/maps/selectors/secondary_map_selector_candidates.csv`
  - `data/maps/selectors/primary_map_selector_summary.json`
  - `docs/analysis/map_selector_opcode15_promotion_20260928.md`
- The C4 scheduler upper-range VM grammar is now reconstructed enough to treat A3/B2/B3/B4 correctly as meta control instructions rather than ordinary dispatch-table opcodes. A3 is a bit-test boolean producer; B2 is unconditional signed-rel8 branch; B3/B4 are zero/nonzero conditional signed-rel8 branches. Together with mode-safe 0x08/0x2D conditions and the existing state0 descriptor proof, a CFG promotes 43 more record0/entry1 selectors. Confirmed primary rises 182->225, unresolved falls 81->38, and 16 immediate 0x51 pairs rise confirmed secondary 85->101.
  - `tools/python/catalog_map_selectors.py`
  - `data/maps/selectors/primary_map_selector_catalog.csv`
  - `data/maps/selectors/secondary_map_selector_candidates.csv`
  - `data/maps/selectors/state0_safe_prefix_promotions.csv`
  - `data/maps/selectors/primary_map_selector_summary.json`
  - `docs/analysis/map_selector_upper_vm_cfg_promotion_20260928.md`
- Residual state0 VM grammar is expanded with anchored E0/E1/E7/E8 expression operators, C2 literal, subtype-2 opcode 0x3D, concrete D0:$1984 and D5:$035E forms, descriptor-preserving 13 02, and 64 00. Canonical confirmed primary rises 225->240, unresolved falls 38->23, and confirmed immediate secondary pairs rise 101->104. Only four record0/entry1 primaries remain, all blocked exclusively by A0 nested-call semantics.
  - `tools/python/catalog_map_selectors.py`
  - `data/maps/selectors/primary_map_selector_catalog.csv`
  - `data/maps/selectors/secondary_map_selector_candidates.csv`
  - `data/maps/selectors/state0_safe_prefix_promotions.csv`
  - `data/maps/selectors/primary_map_selector_summary.json`
  - `docs/analysis/map_selector_residual_vm_promotion_20260928.md`
- A fail-closed A0/B0 nested-call evaluator now closes the final four record0/entry1 selectors. A0 is modeled as a real call through C4:846F/C4:84B9, nested targets are exact SHA-bounded substreams, and B0 return is proven through C4:81EA -> C4:80C5 -> C4:84D9. CC:0929, CC:0931, CD:EF0A and CD:EF1C are promoted. Confirmed primary rises 240->244, unresolved falls 23->19, and record0/entry1 unresolved is now zero.
  - `tools/python/catalog_map_selectors.py`
  - `data/maps/selectors/primary_map_selector_catalog.csv`
  - `data/maps/selectors/state0_safe_prefix_promotions.csv`
  - `data/maps/selectors/primary_map_selector_summary.json`
  - `docs/analysis/map_selector_a0_nested_promotion_20260928.md`
- `data/maps/samples/stable_interior_runtime_identity.json`
- `data/maps/samples/stable_interior_runtime_resolution.json`
- `data/maps/samples/pack50_shrine_exterior_runtime_identity.json`
- `data/maps/samples/pack50_shrine_exterior_runtime_resolution.json`
- `data/maps/transitions/stable_interior_to_pack50_shrine_exterior_20260928.json`
- `docs/analysis/map_runtime_transition_pack2e_to_pack50_20260928.md`


- State0-reachable A0 nested-entry seeding now promotes 16 later-record selectors in packs 0xED/0xEE/0xF0/0xF1. Confirmed primary rises 244->260, unresolved falls 19->3, and CD:E353/CD:E357 closes the final unresolved immediate pair so all 105/105 immediate secondary pairs are confirmed.
  - tools/python/catalog_map_selectors.py
  - data/maps/selectors/state0_a0_nested_promotions.csv
  - data/maps/selectors/primary_map_selector_catalog.csv
  - data/maps/selectors/secondary_map_selector_candidates.csv
  - data/maps/selectors/primary_map_selector_summary.json
  - docs/analysis/map_selector_later_a0_promotion_20260928.md

- Instruction-boundary closure resolves the final three historical primary shapes as false positives rather than map commands. CC:A71F is operand 3 of five-byte opcode 0x63; CC:FD5C and CC:FE6D are operand 1 of six-byte opcode 0x59. The canonical primary corpus is therefore 260 instruction-level selectors, all 260/260 confirmed normal, with zero unresolved.
  - `tools/python/catalog_map_selectors.py`
  - `data/maps/selectors/non_opcode_primary_50_shapes.csv`
  - `data/maps/selectors/primary_map_selector_catalog.csv`
  - `data/maps/selectors/primary_map_selector_summary.json`
  - `docs/analysis/map_selector_instruction_boundary_closure_20260928.md`

- The 260 confirmed primary occurrences are now grouped into 149 deterministic map configurations. A same-index join to the proven dialogue source-family crosswalk attaches provenance to all 260 occurrences; two configurations have curated semantic contexts but remain context_only because pack-level text spans multiple locations.
  - `tools/python/build_map_configuration_index.py`
  - `data/maps/configurations/map_configuration_index.csv`
  - `data/maps/configurations/map_configuration_summary.json`
  - `tools/python/build_map_dialogue_context_crosslink.py`
  - `data/maps/context/map_dialogue_pack_crosslink.csv`
  - `data/maps/context/map_dialogue_pack_crosslink_summary.json`
  - `docs/analysis/map_configuration_context_index_20260928.md`
- Remote map-capture manifest schema v2 now records derived map identity scalars ($0305/$126E/$12B4/$1398/$1399/$139B..$139F) while raw WRAM remains local-only.
  - `tools/remote_lab/shinmomo_remote_bridge.lua`
  - `tools/remote_lab/README.md`

- Frame-3253 runtime scalar evidence closes the stable-interior occurrence identity: $0305=$126E=$12B4=0x2E, $1398=0 and selector 7/15/variant2. The three same-configuration selector rows are therefore narrowed to pack 0x2E / record0 / entry1 / CB:DE70. Raw WRAM remains local-only.
  - `data/maps/samples/stable_interior_runtime_identity.json`
  - `data/maps/samples/stable_interior_runtime_resolution.json`
  - `tools/python/resolve_map_runtime_identity.py`
  - `docs/analysis/stable_interior_runtime_identity_20260928.md`
  - `data/maps/samples/stable_interior_l1.json`
- The configuration index now imports runtime identity records fail-closed. `cfg_t07_l015_v2` records runtime pack 0x2E and exact command CB:DE70; current totals are one runtime-bound configuration / one runtime-bound unique occurrence. The resolver also reproduces the same join from a schema-v2 manifest fixture.
  - `tools/python/build_map_configuration_index.py`
  - `data/maps/configurations/map_configuration_index.csv`
  - `data/maps/configurations/map_configuration_summary.json`

- Active BizHawk was refreshed to the current Lua bridge and schema-v2 map_state embedding was validated on the running core. A fresh frame-3253 capture reproduces pack 0x2E / selector 7/15/2 and resolves again to CB:DE70.
  - `data/maps/samples/stable_interior_runtime_identity.json`
  - `docs/analysis/stable_interior_runtime_identity_20260928.md`
- A second visited map is exact at occurrence level: the forest shrine/village exterior is cfg_t04_l008_v2, runtime pack 0x50, uniquely resolving to CC:1C3F. Runtime-bound totals are now 2 configurations / 2 unique occurrences.
  - `data/maps/samples/pack50_shrine_exterior_runtime_identity.json`
  - `data/maps/samples/pack50_shrine_exterior_runtime_resolution.json`
  - `data/maps/configurations/map_configuration_index.csv`
- The first runtime-confirmed transition edge is recorded as CB:DE70 -> CC:1C3F. The observed order is destination $0305 switch, pack-context convergence plus selector clear, new selector install while black, then visible destination.
  - `data/maps/transitions/stable_interior_to_pack50_shrine_exterior_20260928.json`
  - `docs/analysis/map_runtime_transition_pack2e_to_pack50_20260928.md`

- Full static render batch for primary tileset 4 is committed: 29 distinct layout IDs are stored as `map_###.png`, each with same-ID JSON metadata plus batch CSV/JSON indexes.
  - `tools/python/render_map_layout_images.py`
  - `data/maps/rendered/tileset_04/index.json`
  - `data/maps/rendered/tileset_04/index.csv`
  - `docs/analysis/map_layout_render_batch_20260928.md`
  - commit: `2d38f9a Render tileset4 maps by map id`

- Tileset-4 CHR basis corrected by direct comparison against the live ????? screen: 4bpp VRAM byte base 0x0000 reproduces coherent buildings, trees, fields, ponds, roads and shrine graphics. The earlier 0x8000 basis was wrong, and all 29 tileset-4 map renders were regenerated.
  - `docs/analysis/mapchip_chr_trace_20260928.md`
  - `data/maps/rendered/tileset_04/index.json`
  - `tools/python/render_map_layout_images.py`
- Static source exclusions tightened: DA:3800 is glyph/font-like rather than terrain CHR; CF:0000 is predominantly one parallel attribute byte per CE metatile rather than a CHR bitmap pointer table.

## Observed but not yet promoted

- **confirmed_runtime_join_and_transition**: pack 0x50 / cfg_t04_l008_v2 / CC:1C3F is a forest shrine/village exterior directly connected to the stable save/shrine interior.
  - Why not named: direct in-game place-name text has not yet been captured.
- **strong_external_corroboration**: ????? is the current label candidate because the playlog state ???1????1??100? matches published opening walkthroughs and published ????? descriptions include a shrine and fields.
  - Why not promoted: keep `display_name` blank until game text/event/location data names it directly.
- **confirmed_runtime_validation**: the old bridge-version gap is closed; active-core schema-v2 map_state capture now works.

- **confirmed_capture_limitation**: current Snes9x `cgram.bin` is exactly 512 zero bytes, so committed tileset-4 renders intentionally use 4bpp tile-index grayscale rather than invented color.
- **confirmed_negative_render_test**: tileset-7 / char-base 0xC000 fits a subset of tile indices but fails the runtime visual check on known layout 15, so that basis is rejected and no tileset-7 PNGs are committed.

## In progress

- Connect the corrected tileset-4 resident CHR at VRAM 0x0000 back to its compressed ROM asset source/decompression loader.
- Continue YMA + ROM-dialogue identification against the corrected full-map renders.

## Next actions

1. Trace the ROM graphics loader/decompressor that populates field/town CHR at VRAM 0x0000 and identify its source pointer table/asset boundaries.
2. Reproduce the resident tileset-4 CHR directly from ROM without relying on runtime VRAM.
3. Resolve additional tilesets' CHR sources and add their map render batches only after known-map visual validation.
4. Attach human-facing map names from corrected renders plus YMA/ROM-dialogue/runtime evidence.

## Do not redo

- Do not use tileset-4 4bpp char-base 0x8000; it is disproven. The corrected field/town basis is VRAM byte base 0x0000.
- Do not classify DA:3800 as map-chip CHR; decoded samples are glyph/font-like.
- Do not classify CF:0000 as a CHR bitmap pointer table; its normal form tracks one attribute byte per CE metatile.
- Do not treat the current all-zero CGRAM capture as palette evidence.
- Do not use tileset-7 char-base 0xC000 as canonical; the known layout-15 visual validation failed.
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
- Do not allow opcode 0x15 as a general safe prefix instruction. Its BAB8 callback can later change $035F; it is only proven safe here when 0x15 is the final instruction immediately before candidate 0x50.
- Do not use 181/82 as the current selector count after the terminal opcode-0x15 proof; canonical counts are now 182 confirmed / 81 unresolved.
- Do not interpret A3/B2/B3/B4 through the ordinary C4:87D4 opcode table; the scheduler intercepts A0..AF and B0..BF first.
- Do not use the old 182/81 selector counts after the upper-range CFG proof; canonical counts are now 225 confirmed / 38 unresolved.
- Do not linearize B3/B4; both runtime branch outcomes must be represented in the safe CFG.
- Do not use the old 225 confirmed / 38 unresolved counts after the residual state0 grammar pass; that intermediate pass yielded 240 confirmed / 23 unresolved.
- Do not use the old 240 confirmed / 23 unresolved counts after the A0/B0 nested-call proof; canonical counts are now 244 confirmed / 19 unresolved, with record0/entry1 fully closed.
- Do not use the old 244 confirmed / 19 unresolved counts after later-record A0 nested-entry seeding; canonical counts are now 260 confirmed / 3 unresolved, with all 105 immediate secondary pairs confirmed.
- Do not use the intermediate 260 confirmed / 3 unresolved state as final. The three residual rows are proven operand bytes; canonical primary selector count is 260 / 260 confirmed with zero unresolved.
- Do not reintroduce CC:A71F, CC:FD5C or CC:FE6D as primary selectors; keep them only as negative evidence.
- Do not treat the raw pack-0x9D A0 references as mode proof until the source entry 0x76/0x7C activation context and instruction boundary are independently established.
- Do not flatten opcode A0 as a simple four-byte instruction. It changes $98/$99/$9A to a nested 24-bit target and uses B0/$1266/C4:84D9 return machinery.
- Do not generalize 0x3D, D0/D5, 0x13 or 0x64 beyond the concrete operand/subtype forms anchored by the current state0 proof.
- Do not leave the old schema-v2 runtime-version gap open; the active bridge was refreshed and validated with a fresh frame-3253 schema-v2 capture.
- Do not leave cfg_t04_l008_v2 unbound for the observed exterior; runtime pack 0x50 uniquely resolves CC:1C3F.
- Do not promote the ????? candidate to `display_name` from external walkthrough/state/visual corroboration alone; require direct in-game evidence.

## Runtime-only artifacts

- `%LOCALAPPDATA%/shinmomo-lab/map_captures/1790519691664-3fe31160_save_point_interior`
  - First same-room raw capture used for L1 page stability.
- `%LOCALAPPDATA%/shinmomo-lab/map_captures/1790524923212-b2fd20a4_stable_interior_l1`
  - Fresh stable-room capture at frame 3253 used for L1 page stability.
- `%LOCALAPPDATA%/shinmomo-lab/map_captures/1790520426924-2a33d5df_field_transition_probe`
  - Transition control used to prove that pages 0x1000/0x1800 are scene-specific.

- `%LOCALAPPDATA%/shinmomo-lab/map_captures/1790586092190-25934fb7_schema_v2_reloadtest`
  - Fresh schema-v2 stable-interior map_state validation.
- `%LOCALAPPDATA%/shinmomo-lab/map_captures/1790586286976-e56502b3_exit_transition_step150`
  - Visible pack-0x50 shrine/village exterior runtime capture.
- `%LOCALAPPDATA%/shinmomo-lab/map_captures/1790586206665-a0cf2d8f_exit_probe_down24`
  - Transition phase with destination pack selected before selector replacement.
- `%LOCALAPPDATA%/shinmomo-lab/map_captures/1790586225731-87ee48d9_exit_transition_step30`
  - Black/clear transition phase.
- `%LOCALAPPDATA%/shinmomo-lab/map_captures/1790586245967-3d0e1449_exit_transition_step60`
  - New selector installed while screen remained black.

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
- `docs/analysis/map_selector_opcode15_promotion_20260928.md`
- `docs/analysis/map_selector_upper_vm_cfg_promotion_20260928.md`
- `docs/analysis/map_selector_residual_vm_promotion_20260928.md`
- `docs/analysis/map_selector_a0_nested_promotion_20260928.md`

## Dungeon ROM reconstruction checkpoint — 2026-09-29 batch 5

- Latest verified base before this checkpoint: `88ff9a867f733b4df73998eea77e8482e81c3963` (`Render fourth ROM-derived dungeon batch`).
- Batches 1-4 are already canonical. Do not regenerate or replace them from older runtime captures.
- Graphics reader dispatch 0 (`C0:BCEE` / `C0:BD28`) is now proven. Effective back-reference length is **nibble+2 (2..17 bytes)**.
- Runtime proof on 旅立ちの村 / pack `0x50`: operand `04` = 8192/8192 exact, `05` = 8192/8192 exact, `06` = 3040/3040 exact.
- New strict ROM-only render families pass for tilesets `6,39,44,50,51,52,53,54,55,60`, producing 15 map-ID images.
- Canonical batch-5 analysis: `docs/analysis/dungeon_rom_setup_batch5_20260929.md`.
- Remaining normal-map failures stay fail-closed. Most need opcode-`0x33` graphics descriptors and/or inherited setup state.
- Tilesets `2` and `3` are mode-`0x01`; keep them on the Mode-7/world-style path.
- Tileset `42` needs inherited palette-state proof before rendering.
- User-reported world-map forest/tree color and transparency issue remains open; dungeon reconstruction stays the active priority.

### Immediate next actions

1. model opcode `0x33` graphics-resource selection and inherited setup state;
2. rerun strict coverage for tilesets `5,22-30,32,37,58`;
3. resolve tileset `42` palette inheritance;
4. adapt the Mode-7 path for tilesets `2/3`;
5. then return to world-map palette/transparency cleanup.

## Dungeon ROM reconstruction checkpoint — 2026-09-29 batch 6

- Opcode `0x33` is now modeled: `33 <VRAM word low> <VRAM word high> <graphics descriptor>`.
- `C4:8A5E` stores the explicit destination in `$0F/$10`; `B557` resolves the descriptor but restores that destination before the common transfer path.
- Strict ROM-only coverage now passes for tilesets `22,23,24,25,28,29,30,37`, producing 9 additional maps.
- Canonical batch-6 analysis: `docs/analysis/dungeon_rom_setup_batch6_20260929.md`.
- Remaining immediate normal-map gaps are tilesets `5,32,42,58`; tilesets `2/3` stay on the Mode-7 path.

### Batch-6 next actions

1. resolve inherited/setup graphics for tilesets `5,32,58`;
2. prove tileset `42` inherited palette/setup state;
3. adapt Mode-7 reconstruction for tilesets `2/3`.

## Resume instruction

On a short request such as **「続きを進めて」**:

1. verify latest `main`;
2. read `progress/current_task.json`;
3. preserve newer parallel results;
4. continue from the first unfinished `next_actions` entry;
5. do not redo `done` / `do_not_redo` items;
6. checkpoint again after the next meaningful durable result.

## Rolling override — 2026-10-02 23:14 JST
Canonical machine state remains `progress/project_progress.json`. Latest completed frontier: event-trigger region structure normalized across 57 committed hotspot rows. Next priority is transition -> event/trigger crosslink expansion, starting with 5 missing destination configs and 10 missing arrival-coordinate pairs. See `HM_261002_event_trigger_regions.md`.

- 2026-10-04 rolling cycle: pack 0x96 record0 entry 0x02 structural decode start is confirmed at CC:DBF2 from record0 CC:DBCB..CC:DC5C and entry01 CC:DBDB..CC:DBF2. Arrival XY/opcode remain unconfirmed; designated Drive ROM was inaccessible and no substitute ROM was used. See docs/analysis/entry02_pack_96_structural_boundary_20261004.md.

