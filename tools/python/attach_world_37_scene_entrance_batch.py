"""Attach 37 controller-verified world entry events without overstating the source.

Every source world coordinate was positioned with a clearly disclosed
research cheat BEFORE an ordinary SNES Up press. This is runtime proof
that these 37 entrances fire in that isolated story state, not a
universal path or proof of executing a particular ROM VM instruction.
"""
from __future__ import annotations
from copy import deepcopy

LEDGER_PATH="data/maps/transitions/world_37_gamepad_entrances_after_cheat_20261011.json"

def attach(candidates:list[dict], ledger:dict):
    if (ledger.get("schema_version")!=1 or
        ledger.get("kind")!="strict_37_world_scene_entrance_batch_replay_20261011" or
        ledger.get("source_map_config_id")!="cfg_t01_l001_v1" or
        ledger.get("world_pack")!="0x4C" or
        ledger.get("source_world_xy_cheat_positioned") is not True or
        ledger.get("map_switch_triggered_by_real_controller") is not True or
        ledger.get("normal_world_walking_routes_proven") is not False or
        ledger.get("SNES_CPU_opcode_pc_observed") is not False or
        ledger.get("all_story_states_accessible_proven") is not False or
        ledger.get("total_attempted_hotspots")!=40 or
        ledger.get("successful_gamepad_world_to_ROM_pack")!=37 or
        ledger.get("failed_to_switch_this_local_attempt")!=3 or
        ledger.get("unique_runtime_scene_packs")!=36 or
        ledger.get("unique_runtime_map_configs")!=32 or
        ledger.get("distinct_onscreen_named_pack_contexts")!=25 or
        ledger.get("new_onscreen_named_pack_contexts_for_viewer")!=23 or
        ledger.get("no_raw_image_savestate_ROM_or_frame_json_committed") is not True or
        ledger.get("underlying_emulator_restored_after_each_of_6_batches") is not True):
        raise ValueError("Strict full world-entry batch provenance or counts missing")
    entries=ledger.get("entries")
    failed=ledger.get("local_no_switch_observations")
    if not isinstance(entries,list) or len(entries)!=37 or not isinstance(failed,list) or len(failed)!=3:
        raise ValueError("Expected complete 37 successes and three local negative probes")
    by_id={e.get("transition_id"):e for e in candidates}
    if len(by_id)!=len(candidates):raise ValueError("Cannot bind to duplicate transition IDs")
    result=deepcopy(candidates)
    out_by_id={e["transition_id"]:e for e in result}
    seen=set();packs=set();configs=set();coordinate_resolved=[]
    for obs in entries:
        tid=obs.get("transition_id")
        e=out_by_id.get(tid)
        if tid in seen or e is None:
            raise ValueError(f"Duplicate/unmatched world entry observation: {tid}")
        seen.add(tid)
        h=e.get("source_hotspot_binding") or {}
        region=obs.get("source_hotspot_xy") or {}
        approach=obs.get("cheat_positioned_approach_xy") or {}
        arrival=obs.get("settled_arrival_xy") or {}
        if (e.get("source_config_id")!="cfg_t01_l001_v1" or
            obs.get("source_config_id")!="cfg_t01_l001_v1" or
            obs.get("source_world_pack")!="0x4C" or
            e.get("destination_config_id")!=obs.get("destination_config_id") or
            e.get("destination_pack")!=obs.get("destination_pack") or
            e.get("confidence") not in ("strong_candidate","confirmed") or
            e.get("runtime_world_entry_batch_probe") is not None or
            not all(h.get("source_grid_"+k)==region.get(k) for k in ("x","y")) or
            h.get("source_width")!=region.get("width") or
            h.get("source_height")!=region.get("height") or
            (approach.get("x"),approach.get("y"))!=(region.get("x"),region.get("y")+1) or
            obs.get("source_position_supplied_by_analysis_cheat") is not True or
            obs.get("normal_world_walking_route_to_source_proven") is not False or
            obs.get("real_snes_gamepad_input")!="Up" or
            obs.get("scene_pack_matches_rom_candidate") is not True or
            obs.get("cpu_rom_opcode_PC_observed") is not False or
            obs.get("all_story_states_accessible_proven") is not False or
            not isinstance(obs.get("source_hotspot_contact_frame"),int) or
            not isinstance(obs.get("map_switch_frame"),int) or
            not isinstance(arrival.get("x"),int) or
            not isinstance(arrival.get("y"),int) or
            not (0<=arrival["x"]<=255 and 0<=arrival["y"]<=255) or
            obs.get("screenshot_raw_committed") is not False or
            obs.get("local_savestate_raw_committed") is not False or
            any(len(obs.get(k,""))!=64 for k in
                ("screenshot_sha256","local_raw_input_sha256",
                 "local_raw_neutral_sha256","local_raw_second_neutral_sha256"))):
            raise ValueError(f"World entrance event not backed by exact ROM region, gamepad and cheat limit: {tid}")
        if obs["source_hotspot_contact_frame"]>=obs["map_switch_frame"]:
            raise ValueError(f"Map switch occurred before touching trigger: {tid}")
        x,y=arrival["x"],arrival["y"]
        if e.get("destination_x") not in (None,x) or e.get("destination_y") not in (None,y):
            raise ValueError(f"Contradictory ROM destination coordinates {tid}")
        originally_unknown=e.get("destination_x") is None or e.get("destination_y") is None
        e["destination_x"]=x
        e["destination_y"]=y
        if originally_unknown:
            e["destination_coordinate_origin"]="runtime_arrival_after_cheat_adjacent_gamepad_world_entry"
            coordinate_resolved.append(tid)
        e["runtime_world_entry_batch_probe"]={
            "status":"actual_gamepad_triggered_world_entrance_in_one_cheat_seeded_story_state",
            "source_hotspot_xy":region,
            "source_world_position_supplied_by_cheat":True,
            "actual_SNES_gamepad_triggered_event":True,
            "normal_world_walking_route_proven":False,
            "source_hotspot_contact_frame":obs["source_hotspot_contact_frame"],
            "map_switch_frame":obs["map_switch_frame"],
            "destination_pack":obs["destination_pack"],
            "settled_arrival_xy":{"x":x,"y":y},
            "ROM_opcode_CPU_executed_proven":False,
            "all_story_states_reachable_proven":False,
            "visible_name_if_verified":obs.get("inferred_onscreen_title"),
            "screenshot_sha256":obs["screenshot_sha256"],
            "provenance":LEDGER_PATH,
        }
        packs.add(obs["destination_pack"])
        configs.add(obs["destination_config_id"])
    if len(seen)!=37 or len(packs)!=36 or len(configs)!=32:
        raise ValueError("36 distinct scene packs / 32 structural configs not recovered")
    negatives=set()
    for obs in failed:
        tid=obs.get("transition_id")
        e=out_by_id.get(tid)
        if (tid in seen or tid in negatives or e is None or
            e.get("source_config_id")!="cfg_t01_l001_v1" or
            obs.get("did_not_switch_this_local_state") is not True or
            obs.get("all_story_states_blocked_proven") is not False or
            obs.get("ROM_candidate_still_valid") is not True):
            raise ValueError(f"Invalid local negative trial: {tid}")
        negatives.add(tid)
        e["runtime_world_entry_batch_negative_trial"]={
            "status":"no_pack_switch_on_south_approach_in_this_lab_state_only",
            "source_contact_observed":obs["source_hotspot_contact_observed"],
            "final_world_xy":obs["observed_final_world_xy"],
            "activation_other_positions_or_story_states":"unresolved",
            "static_ROM_candidate_invalidated":False,
            "provenance":LEDGER_PATH,
        }
    if len(negatives)!=3:raise ValueError("Three local blocked/no-trigger cases required")
    return result,{
      "attempted_world_entrances":40,
      "actual_gamepad_matched_destination_pack":37,
      "distinct_destination_scene_packs":36,
      "distinct_destination_structural_configs":32,
      "local_unconfirmed_entries":3,
      "coordinate_resolved_existing_edges_count":len(coordinate_resolved),
      "coordinate_resolved_existing_edge_ids":sorted(coordinate_resolved),
      "new_graph_edges":0,
      "source_walking_reachability_generalized":False,
      "story_conditions_fully_proven":False,
      "exact_VM_instruction_PCs_observed":False,
      "evidence":LEDGER_PATH
    }
