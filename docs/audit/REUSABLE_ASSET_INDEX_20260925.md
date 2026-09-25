# Reusable analysis asset index — 2026-09-25

This index points future analysis to existing evidence before new scans are written.

## Address / ROM map

- `data/base_tables/shinmomo_address_master_overview_20260313.md`
- `data/base_tables/shinmomo_rom_full_block_map_20260313.md`
- `data/base_tables/shinmomo_rom_handover_master_blocks_20260313.csv`
- `data/base_tables/shinmomo_rom_handover_master_exact_20260313.csv`
- `data/csv/shinmomo_hirom_address_correction_table_v1.csv` (canonical)
- `data/csv/shinmomo_lorom_address_correction_table_v1.csv` (historical; superseded for CPU labels)
- disassembly listings under `data/disassembly/` and the legacy root listings

Use these before a new whole-ROM blind scan. Address labels must follow `docs/analysis/rom_addressing_hirom.md`; historical LoROM labels are not canonical.

## Script VM / event

- `docs/reports/vm_reader_and_f09a_blob_model_20260503.md`
- `docs/analysis/goal9_script_spec_progress_20260527.md`
- `data/csv/shinmomo_39850_vm_instruction_parse_v2.csv`
- `data/csv/shinmomo_39850_vm_macro_rows_v2.csv`
- `data/static/goal9_41a10_target_records_20260527.csv`
- `archive/previous_zip_contents/shinmomo_static_push_vol013/.../table_41A10_records_0x400.csv`
- `docs/handoff/HM_260925_41A10_section_boundary.md`

Canonical distinction: selector matcher is unknown; target script VM core is known.

## Condition / logical actor / event NPC

- `data/npc_display/shinmomo_C4_C8AA_candidate_feeder_80DA57_8586AC_20260425.md`
- `data/npc_display/shinmomo_195E_predicates_180A_bit7_followup_20260425.md`
- `data/npc_display/shinmomo_goal4_818D87_return_values_analysis_20260426.md`
- associated CSVs under `data/csv/text_decoder/`

These connect candidate resolution, entity flags, logical lists and script predicates.

## Controller / visible object / OAM

- `data/wram/object_slot_soa_schema.json`
- `docs/analysis/wram_object_pool.md`
- `docs/reports/bank87_object_slot_0759_0799_reclassification_20260503.md`
- `data/npc_display/shinmomo_goal13_0A61_linked_list_static_analysis_20260426.md`
- `data/npc_display/shinmomo_goal13_AF33_AFEC_callers_20260426.md`
- `data/npc_display/shinmomo_object_oam_work_spec_update_20260425.md`
- `data/npc_display/shinmomo_oam_path_0ba7_0c67_20260425.md`

Do not identify controller/work slots and visible-object physical nodes without an explicit handle bridge.

## Sprite / animation / graphics

- `data/npc_display/shinmomo_B294_sprite_groups_summary_20260425.csv`
- `data/npc_display/shinmomo_B2C1_animation_top_table_20260425.csv`
- `data/npc_display/shinmomo_B2C1_animation_state_scripts_20260425.csv`
- `data/npc_display/shinmomo_0E27_animation_state_caller_analysis_20260425.md`
- `docs/graphics/SPRITE_PNG_RECONSTRUCTION_PIPELINE_20260503.md`
- `docs/graphics/SPRITE_RENDERER_SYNC_SPEC_RUN10.md`
- `docs/graphics/MAPCHIP_* / MAP_* / METATILE_*`
- graphics runtime schemas under `data/csv/`

The pipeline/spec layer is substantially ahead of the complete sprite-asset corpus. The repository has many reconstruction images but no complete per-entity canonical sprite atlas yet.

## Dialogue / text

- `reports/text_decoder/shinmomo_dialogue_source_reader_static_analysis_20260427.md`
- `archive/previous_zip_contents/shinmomo_vol013_mode02_mass_dump_v33/shinmomo_dump_mode02_dialogues_v33.py`
- `.../shinmomo_mode02_chain_C8_A7DD_v33_sample.md`
- `data/csv/shinmomo_v33_scan_C8_A7D0_A960.csv` (2606 scan rows; limited window, not a complete corpus)
- `data/csv/restored_logs/*`
- lexicon/dictionary CSVs under `data/csv/text_decoder/`
- facility text analyses under `data/text_facility/`

Next step is root enumeration + full-ROM validated extraction, not another decoder rewrite.

## Item / equipment / facility

- item/equipment table dumps in `data/base_tables/`
- selector/schema tables in `data/base_tables/`
- `data/text_facility/shinmomo_goal5_goal9_joint_analysis_20260424.md`
- `handover/current_master.md` for integrated facility/ledger context

## Weapon special / battle subset

- `docs/analysis/goal7_weapon_special_progress_20260527.md`
- `data/static/goal7_weapon_script_pack_by_equipment_20260527.csv`
- `data/weapon_special/` and `data/weapon_special/vol015_trace/`

This is a well-developed subsystem, not a complete battle-engine specification.

## Recompilation / reconstruction

- `recompilable_c/`
- `tools/decompile_rom_to_c.py`
- `tools/export_shinvm_dsl.py`
- `docs/source_readmes/recompilable_decomp_README.md`
- `build/recompilable_decomp_build_test.log`

The C99 scaffold builds, but it is not a SNES ROM rebuild system.

## Major missing domains

The repository audit found no dedicated audio/APU/SPC analysis assets.

Save-system coverage is also minimal: `data/hexdumps/save_restore_state.hex.txt` is object state save/restore code, not a complete SRAM/save-file specification.

These gaps must be explicit in G1/G5 rather than hidden by high mature-subsystem percentages.
