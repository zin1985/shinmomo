"""Only actual reverse world map switches from 14 isolated SNES controller trials.

These routes are saved-world-origin-context-specific. They do not
prove unconditional reachability, CPU ROM opcode PC, walkable
world->source routes, or exact source trigger tile.
"""
from __future__ import annotations
from copy import deepcopy

PROVENANCE="data/maps/transitions/world_14_reverse_returns_after_cheat_arrivals_20261011.json"
PREFIX="runtime_reverse_down_"

def inject(candidates:list[dict],proof:dict,maps:list[dict]):
    if (proof.get("schema_version")!=1 or
        proof.get("kind")!="fourteen_verified_original_scene_return_events_from_real_controller" or
        proof.get("source_entrance_ledger")!="data/maps/transitions/world_37_gamepad_entrances_after_cheat_20261011.json" or
        proof.get("research_isolated_hidden_emulator") is not True or
        proof.get("all_batches_original_emulator_restored") is not True or
        proof.get("source_original_world_entrances_cheat_seeded") is not True or
        proof.get("reverse_scene_controller_path_Wram_XY_cheat_used") is not False or
        proof.get("normal_walkable_world_access_all_scenes_proven") is not False or
        proof.get("story_condition_gate_universal") is not False or
        proof.get("actual_native_or_VM_CPU_instruction_PC_observed") is not False or
        proof.get("attempts")!=20 or proof.get("confirmed_world_returns")!=14 or
        proof.get("local_nonreturns")!=6 or
        proof.get("new_graph_edges_to_add")!=14 or
        proof.get("raw_frame_screenshots_states_or_ROM_committed") is not False or
        len(proof.get("verified_reverse_returns",[]))!=14 or
        len(proof.get("unconfirmed_local_direction_returns",[]))!=6):
        raise ValueError("Invalid 14-return evidence and safety scope")
    map_by_id={m["config_id"]:m for m in maps}
    by_id={c["transition_id"]:c for c in candidates}
    if len(by_id)!=len(candidates) or len(map_by_id)!=len(maps):
        raise ValueError("Input graph has duplicate objects")
    world=map_by_id.get("cfg_t01_l001_v1")
    if not world or world.get("tileset_id")!=1 or world.get("layout_id")!=1:
        raise ValueError("Verified world map config unavailable")
    incoming={c["transition_id"]:c for c in candidates if c.get("runtime_world_entry_batch_probe")}
    out=deepcopy(candidates)
    seen_packs=set()
    for item in proof["verified_reverse_returns"]:
        pack=item.get("source_scene_pack")
        input_id=item.get("source_world_transition_id")
        source=incoming.get(input_id)
        cfg=item.get("source_config_id")
        m=map_by_id.get(cfg)
        arrival=item.get("world_arrival_xy_in_this_saved_origin_context") or {}
        last=item.get("last_observed_source_xy_before_switch") or {}
        spawn=item.get("scene_spawn_xy") or {}
        if (not isinstance(pack,str) or pack in seen_packs or
            not source or source.get("destination_pack")!=pack or
            source.get("destination_config_id")!=cfg or
            source.get("destination_x")!=spawn.get("x") or
            source.get("destination_y")!=spawn.get("y") or
            not m or m.get("tileset_id") is None or m.get("layout_id") is None or
            item.get("verified_reverse_result")!="observed_direct_return_from_destination_scene_to_saved_world" or
            item.get("world_destination_pack")!="0x4C" or
            item.get("world_destination_config_id")!="cfg_t01_l001_v1" or
            item.get("source_world_entrance_cheat_positioned") is not True or
            item.get("return_route_did_not_cheat_coordinates") is not True or
            item.get("normal_world_route_to_original_entrance_proven") is not False or
            item.get("universal_story_gate_proven") is not False or
            item.get("CPU_handler_PC_observed") is not False or
            item.get("requires_saved_world_origin_context") is not True or
            item.get("world_arrival_same_for_other_saves_proven") is not False or
            item.get("frame_capture_raw_not_committed") is not True or
            item.get("world_stable_observed_frames",0)<8 or
            not isinstance(item.get("first_world_pack_switch_frame"),int) or
            not all(isinstance(arrival.get(k),int) and 0<=arrival[k]<=255 for k in ("x","y")) or
            not all(isinstance(last.get(k),int) and 0<=last[k]<=255 for k in ("x","y")) or
            not isinstance(item.get("underlying_source_file_digest"),list) or
            len(item["underlying_source_file_digest"])!=4 or
            any(not isinstance(h,str) or len(h)!=64 for h in item["underlying_source_file_digest"]) or
            not isinstance(item.get("screenshot_sha256"),str) or
            len(item["screenshot_sha256"])!=64):
            raise ValueError(f"Reverse route lacks exact source pack, integrity or story limitation: {pack}")
        seen_packs.add(pack)
        unique_id=f"{PREFIX}{pack[2:]}_world_saved_20261011"
        if unique_id in by_id:
            raise ValueError("Duplicate injected world return")
        edge={
            "transition_id":unique_id,
            "tier":"tier1_confirmed",
            "source_config_id":cfg,
            "source_pack":pack,
            "source_layout":m["layout_id"],
            "source_tileset":m["tileset_id"],
            "script_pack":None,"script_record":None,"script_entry":None,
            "trigger_type":"runtime_scene_down_to_contextual_saved_world",
            "trigger_addr":None,
            "source_hotspot_binding":None,
            "destination_pack":"0x4C",
            "destination_entry_id":None,
            "destination_config_id":"cfg_t01_l001_v1",
            "destination_tileset":world["tileset_id"],
            "destination_layout":world["layout_id"],
            "destination_variant":1,
            "destination_x":arrival["x"],
            "destination_y":arrival["y"],
            "destination_secondary_x":None,
            "destination_secondary_y":None,
            "destination_coordinate_addr":None,
            "confidence":"confirmed",
            "condition":"Observational only: Down from one cheat-origin-entered scene returned to the prior saved world context in this game state; other saved worlds/story flags unknown.",
            "evidence":"Frame-end validated ordinary SNES Down and no XY writes; observed direct source-pack -> world-pack switch, 2 neutral windows, local screenshot SHA256",
            "provenance":PROVENANCE,
            "runtime_scene_saved_world_return_proof":{
                "observed_runtime_map_switch":True,
                "source_scene_pack":pack,
                "source_scene_spawn_xy":spawn,
                "last_observed_source_xy_before_switch":last,
                "exact_trigger_cell_CPU_proven":False,
                "source_reached_via_cheat_positioned_world_entrance":True,
                "reverse_control_used_coordinate_warp":False,
                "reverse_controller_input":"Down",
                "reverse_controller_frames":72,
                "return_world_xy_in_this_saved_context":arrival,
                "return_world_xy_for_other_saves_verified":False,
                "source_world_walkability_proven":False,
                "actual_native_CPU_PC_observed":False,
                "all_story_gates_proven":False,
                "first_pack_switch_frame":item["first_world_pack_switch_frame"],
                "world_stable_through_frame":item["world_stable_through_frame"],
                "world_stable_observed_frames":item["world_stable_observed_frames"],
                "screenshot_sha256":item["screenshot_sha256"],
                "incoming_world_transition_id":input_id,
                "provenance":PROVENANCE,
            },
        }
        out.append(edge)
    for item in proof["unconfirmed_local_direction_returns"]:
        if (item.get("source_scene_pack") in seen_packs or
            item.get("verified_reverse_result")!="no_map_change_under_72_frame_down_then_120_neutral" or
            item.get("absence_of_exit_globally_proven") is not False or
            item.get("other_directions_not_checked") is not True):
            raise ValueError("Overclaimed/duplicate local negative return")
    if len(seen_packs)!=14 or len(out)!=len(candidates)+14:
        raise ValueError("14 distinct scene reverse map edges required")
    return out,{
        "original_20_scene_return_probes":20,
        "new_confirmed_contextual_saved_world_edges":14,
        "local_direction_nonreturns":6,
        "story_phase_universality_proven":False,
        "world_walkable_access_proven":False,
        "CPU_opcode_pc_observed":False,
        "evidence":PROVENANCE
    }
