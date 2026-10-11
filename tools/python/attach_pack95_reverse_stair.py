"""Bind reverse pack0x95->pack0x91 map movement to a unique existing ROM candidate.

Binds only observed source/destination and frame data, NOT exact
executed opcode PC or universal story reachability. The original
world-to-cave path involved a disclosed cheat-positioned starting cell.
"""
from __future__ import annotations
from copy import deepcopy

TARGET="catalog_transition_0194"
PROVENANCE="data/maps/transitions/omusubi_pack95_reverse_stair_verified_20261011.json"

def attach(candidates:list[dict], proof:dict):
    if (proof.get("schema_version")!=1 or
        proof.get("kind")!="verified_pack95_reverse_stair_return" or
        proof.get("source_config_id")!="cfg_t08_l096_v2" or
        proof.get("source_pack")!="0x95" or
        proof.get("prior_arrival_stair_xy")!={"x":22,"y":8} or
        proof.get("real_down_cell")!={"x":22,"y":9} or
        proof.get("return_contact_cell")!={"x":22,"y":8} or
        proof.get("return_contact_frame")!=664095 or
        proof.get("source_real_gamepad_buttons")!=["Down","Up"] or
        proof.get("source_reached_via_cheat_origin_cave_route") is not True or
        proof.get("normal_world_walk_to_cave_proven") is not False or
        proof.get("pack_switch_frame")!=664110 or
        proof.get("selector_convergence_frame")!=664145 or
        proof.get("destination_config_id")!="cfg_t08_l092_v2" or
        proof.get("destination_pack")!="0x91" or
        proof.get("settled_arrival_xy")!={"x":71,"y":26} or
        proof.get("first_settled_arrival_frame")!=664196 or
        proof.get("stable_frames",0)<120 or
        proof.get("existing_static_reverse_candidate")!=TARGET or
        proof.get("static_candidate_opcode_address")!="CC:DA1A" or
        proof.get("actual_opcode_CPU_PC_observed") is not False or
        proof.get("source_config_runtime_verified") is not True or
        proof.get("story_condition_verified") is not False or
        proof.get("pack95_stair_at_22_31_proven_as_exit") is not False or
        proof.get("new_transition_candidate_count")!=0 or
        proof.get("new_bound_edge_count")!=1 or
        proof.get("all_raw_traces_local_only") is not True):
        raise ValueError("Missing or overclaimed pack95 reverse stair proof")
    result=deepcopy(candidates)
    matches=[x for x in result if x.get("transition_id")==TARGET]
    if len(matches)!=1:raise ValueError("Exactly one existing ROM reverse candidate required")
    e=matches[0]
    if (e.get("source_config_id") is not None or
        e.get("source_pack") is not None or
        e.get("destination_config_id")!="cfg_t08_l092_v2" or
        e.get("destination_pack")!="0x91" or
        (e.get("destination_x"),e.get("destination_y"))!=(None,None) or
        e.get("trigger_addr")!="CC:DA1A" or
        e.get("script_pack")!="0x95" or
        e.get("confidence")!="strong_candidate"):
        raise ValueError("ROM reverse candidate changed or source was already bound")
    e["source_config_id"]="cfg_t08_l096_v2"
    e["source_pack"]="0x95"
    e["source_tileset"]=8
    e["source_layout"]=96
    e["destination_x"]=71
    e["destination_y"]=26
    e["destination_coordinate_origin"]="observed_after_controller_reverse_stair_with_cheat_origin_provenance"
    e["source_binding_provenance"]="unique_ROM_reverse_target_match_plus_actual_map_pack_transition_NOT_VM_PC"
    e["runtime_reverse_stair_proof"]={
      "returned_via_real_gamepad":True,
      "source_xy_after_stepping_back":{"x":22,"y":8},
      "source_reached_from_world_coordinate_cheat":True,
      "normal_world_path_proven":False,
      "switch_frame":664110,
      "selector_convergence_frame":664145,
      "first_settled_arrival_frame":664196,
      "destination_xy":{"x":71,"y":26},
      "stable_frames":proof["stable_frames"],
      "ROM_opcode_CPU_executed_proven":False,
      "story_predicates_verified":False,
      "other_pack95_stair_at_22_31_exit_proven":False,
      "static_confidence_unchanged":True,
      "provenance":PROVENANCE
    }
    return result,{
      "existing_candidate_source_and_arrival_bound_count":1,
      "new_candidate_count":0,
      "new_bound_edge_count":1,
      "existing_candidate_id":TARGET,
      "source_config_id":"cfg_t08_l096_v2",
      "destination_config_id":"cfg_t08_l092_v2",
      "exact_VM_PC_proven":False,
      "world_walkable_route_proven":False
    }
