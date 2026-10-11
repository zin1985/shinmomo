"""Attach gamepad-proven source map to one existing pack0x95 ROM candidate.

This binds the map source of an already cataloged destination, not the
actual SNES VM opcode execution PC or all story predicates.
"""
from __future__ import annotations
from copy import deepcopy
TARGET="catalog_transition_0171"
PROOF="data/maps/transitions/omusubi_pack91_to_pack95_verified_20261011.json"

def attach(candidates:list[dict],proof:dict):
    if (proof.get("schema_version")!=1 or
        proof.get("kind")!="verified_cave_source_bound_pack95_transfer" or
        proof.get("prior_hole_shaft_proof")!="data/maps/transitions/omusubi_hole_shaft_verified_20261011.json" or
        proof.get("source_config_id")!="cfg_t08_l092_v2" or
        proof.get("source_pack")!="0x91" or
        proof.get("destination_config_id")!="cfg_t08_l096_v2" or
        proof.get("destination_pack")!="0x95" or
        proof.get("destination_xy")!={"x":22,"y":8} or
        proof.get("source_shafts_final_xy")!={"x":70,"y":26} or
        proof.get("source_real_input_contact_cell")!={"x":71,"y":26} or
        proof.get("source_contact_frame")!=663918 or
        proof.get("switch_frame")!=663933 or
        proof.get("selector_convergence_frame")!=663967 or
        proof.get("arrival_stable_frame")!=664018 or
        proof.get("destination_stable_through_frame",0)<664076 or
        proof.get("existing_rom_candidate_id")!=TARGET or
        proof.get("existing_rom_candidate_opcode_PC")!="CC:D377" or
        proof.get("static_candidate_was_source_unbound") is not True or
        proof.get("ROM_candidate_opcode_executed_PC_proven") is not False or
        proof.get("runtime_source_map_config_proven") is not True or
        proof.get("source_reached_from_cheat_origin_cave_path") is not True or
        proof.get("normal_world_walkable_route_proven") is not False or
        proof.get("universal_story_gate_proven") is not False or
        proof.get("new_candidate_count")!=0 or
        proof.get("new_source_bound_edge_count")!=1):
        raise ValueError("Pack0x95 source proof invalid or overclaims VM execution")
    result=deepcopy(candidates)
    matches=[e for e in result if e.get("transition_id")==TARGET]
    if len(matches)!=1:
        raise ValueError("No unique ROM pack0x95 candidate")
    e=matches[0]
    if (e.get("source_config_id") is not None or e.get("source_pack") is not None or
        e.get("source_hotspot_binding") is not None or
        e.get("destination_config_id")!="cfg_t08_l096_v2" or
        e.get("destination_pack")!="0x95" or
        e.get("trigger_addr")!="CC:D377" or
        (e.get("destination_x"),e.get("destination_y"))!=(22,8) or
        e.get("confidence")!="strong_candidate"):
        raise ValueError("ROM pack0x95 candidate changed or was bound already")
    e["source_config_id"]="cfg_t08_l092_v2"
    e["source_pack"]="0x91"
    e["source_tileset"]=8
    e["source_layout"]=92
    e["source_binding_provenance"]="unique_runtime_cave_to_pack95_endpoint_match_not_script_PC"
    e["runtime_floor_transition_proof"]={
        "source_movement_confirmed":True,
        "source_map_config_id":"cfg_t08_l092_v2",
        "contact_cell":{"x":71,"y":26},
        "source_arrived_via_cheat_origin_hole_sequence":True,
        "normal_world_to_hole_route_proven":False,
        "pack_switch_frame":663933,
        "selector_convergence_frame":663967,
        "settled_arrival_frame":664018,
        "arrived_pack":"0x95",
        "arrived_xy":{"x":22,"y":8},
        "script_opcode_PC_proven":False,
        "story_flags_verified":False,
        "preexisting_confidence_unchanged":True,
        "provenance":PROOF,
    }
    return result,{
      "new_candidate_count":0,
      "new_bound_edge_count":1,
      "source_id":"cfg_t08_l092_v2",
      "target_id":"cfg_t08_l096_v2",
      "matched_rom_candidate":TARGET,
      "source_binding_method":"observed_map_pair_and_unique_existing_static_destination",
      "actual_rom_opcode_pc_observed":False,
      "world_walking_route_proven":False,
    }
