"""Append a single runtime cave->world edge without inventing a universal return.

The destination world cell comes from the prior saved-map context,
which was originally cheat-positioned. This is one demonstrated route
in the observed state, not a global script opcode or story phase proof.
"""
from __future__ import annotations
from copy import deepcopy
ID="runtime_pack91_world_saved_origin_return_20261011"
PROVENANCE="data/maps/transitions/omusubi_cave_world_return_verified_20261011.json"

def inject(candidates:list[dict],proof:dict):
    if (proof.get("schema_version")!=1 or
        proof.get("kind")!="verified_conditional_cave_saved_origin_return" or
        proof.get("proposed_edge_id")!=ID or
        proof.get("new_graph_edge_count")!=1 or
        proof.get("cave_source_map_config_id")!="cfg_t08_l092_v2" or
        proof.get("cave_source_pack")!="0x91" or
        proof.get("world_destination_map_config_id")!="cfg_t01_l001_v1" or
        proof.get("world_destination_pack")!="0x4C" or
        proof.get("source_inside_cave_xy")!={"x":71,"y":61} or
        proof.get("return_tile_entered_with_gamepad")!={"x":71,"y":59} or
        proof.get("return_tile_metatile_id")!=32 or
        proof.get("world_arrival_xy_in_this_saved_context")!={"x":47,"y":199} or
        proof.get("contact_frame")!=663402 or
        proof.get("return_map_switch_frame")!=663417 or
        proof.get("return_context_selector_frame")!=663451 or
        proof.get("first_settled_arrival_frame")!=663532 or
        proof.get("stable_observed_frames",0)<120 or
        proof.get("return_requires_original_saved_map_context") is not True or
        proof.get("return_world_xy_for_other_saves_verified") is not False or
        proof.get("entry_origin_supplied_by_analysis_coordinate_cheat") is not True or
        proof.get("normal_world_walk_to_cave_proven") is not False or
        proof.get("floor_to_floor_transition_verified") is not False or
        proof.get("CPU_handler_PC_observed") is not False or
        proof.get("VM_opcode_56_executed_proven") is not False or
        proof.get("trace_data_committed") is not False):
        raise ValueError("Return proof lacks strict scope, provenance or physical replay")
    if any(c.get("transition_id")==ID or
           (c.get("source_config_id")=="cfg_t08_l092_v2" and
            c.get("destination_config_id")=="cfg_t01_l001_v1")
           for c in candidates):
        raise ValueError("Duplicate cave->world map edge")
    if not any(c.get("transition_id")=="catalog_transition_0750" and
               c.get("runtime_cheat_entry_proof",{}).get("observed_in_game_transition") is True and
               c.get("destination_x")==71 and c.get("destination_y")==59
               for c in candidates):
        raise ValueError("Independent cave entrance evidence missing")
    edge={
        "transition_id":ID,
        "tier":"tier1_confirmed",
        "source_config_id":"cfg_t08_l092_v2",
        "source_pack":"0x91",
        "source_layout":92,"source_tileset":8,
        "script_pack":None,"script_record":None,"script_entry":None,
        "trigger_type":"runtime_cave_stair_saved_origin_return",
        "trigger_addr":None,
        "source_hotspot_binding":None,
        "destination_pack":"0x4C",
        "destination_entry_id":None,
        "destination_config_id":"cfg_t01_l001_v1",
        "destination_layout":1,"destination_tileset":1,"destination_variant":1,
        "destination_x":47,"destination_y":199,
        "destination_secondary_x":None,"destination_secondary_y":None,
        "destination_coordinate_addr":None,
        "condition":"Requires saved-map origin from this particular cheat-positioned world-to-cave visit; universal exit target unverified",
        "confidence":"confirmed",
        "evidence":"Real cave gamepad Down then Up, source (71,61)->(71,59), pack0x91->world0x4C frame663417, world stable at (47,199) from frame663532",
        "provenance":PROVENANCE,
        "runtime_saved_origin_context":{
            "runtime_edge_status":"observed_once_replayed",
            "exact_source_tile":{"x":71,"y":59,"width":1,"height":1},
            "original_cave_entry_was_cheat_positioned":True,
            "source_stepped_by_real_controller":True,
            "destination_depends_on_saved_map":True,
            "destination_for_other_saved_states_proven":False,
            "return_handler_CPU_PC_observed":False,
            "floor_to_floor_transition":False,
            "contact_frame":663402,
            "switch_frame":663417,
            "selector_frame":663451,
            "settled_arrival_frame":663532,
            "stable_observed_frames":proof["stable_observed_frames"],
        },
    }
    result=deepcopy(candidates)
    result.append(edge)
    return result,{"new_runtime_cave_saved_return_edge_count":1,
                   "transition_id":ID,
                   "source":"cfg_t08_l092_v2","destination":"cfg_t01_l001_v1",
                   "new_graph_edge_count":1,
                   "saved_map_specific_only":True,
                   "CPU_pc_proven":False}
