"""Attach an explicitly cheat-positioned runtime event to the already-known dungeon edge.

Only arrival coordinates and the bounded experiment are established.
Normal world walkability, story gate, CPU handler PC and other source
cells are NOT inferred. Existing ROM confidence remains unchanged.
"""
from __future__ import annotations
from copy import deepcopy

TARGET_ID="catalog_transition_0750"
PROOF_REL="data/maps/transitions/omusubi_kororin_cheat_entry_verified_20261011.json"

def attach(candidates:list[dict],proof:dict):
    if (proof.get("kind")!="cheat_positioned_runtime_dungeon_entrance" or
        proof.get("schema_version")!=1 or
        proof.get("original_edge_id")!=TARGET_ID or
        proof.get("source_setup_type")!="explicit_analysis_cheat_world_position" or
        proof.get("source_normal_world_walk_route_proven") is not False or
        proof.get("hien_spell_actually_cast_for_this_transition") is not False or
        proof.get("cheat_world_xy")!=[47,200] or
        proof.get("source_region_contact_cell")!=[47,199] or
        proof.get("map_pack_switch_frame")!=663079 or
        proof.get("selector_convergence_frame")!=663116 or
        proof.get("first_settled_coordinate_frame")!=663203 or
        proof.get("destination_config_id")!="cfg_t08_l092_v2" or
        proof.get("destination_pack")!="0x91" or
        proof.get("destination_xy")!={"x":71,"y":59} or
        proof.get("screenshot_onscreen_title")!="おむすびころりん" or
        proof.get("rom_static_cpu_opcode_execution_proven") is not False or
        proof.get("static_graph_confidence_unchanged") is not True or
        proof.get("all_story_phases_accessible_proven") is not False or
        proof.get("new_graph_edges")!=0):
        raise ValueError("Cheat-positioned dungeon proof lacks required boundaries")
    result=deepcopy(candidates)
    matches=[e for e in result if e.get("transition_id")==TARGET_ID]
    if len(matches)!=1:raise ValueError("Dungeon transition edge not unique")
    e=matches[0]
    if (e.get("source_config_id")!="cfg_t01_l001_v1" or
        e.get("destination_config_id")!="cfg_t08_l092_v2" or
        e.get("destination_pack")!="0x91" or
        e.get("trigger_addr")!="CC:0B7F" or
        e.get("confidence")!="strong_candidate" or
        e.get("destination_x") is not None or
        e.get("destination_y") is not None or
        e.get("runtime_cheat_entry_proof")):
        raise ValueError("Source candidate changed or has earlier proof")
    e["destination_x"]=71
    e["destination_y"]=59
    e["destination_coordinate_origin"]="frame_exact_destination_after_explicit_analysis_warp"
    e["runtime_cheat_entry_proof"]={
      "observed_in_game_transition":True,
      "source_position_supplied_by_analysis_cheat":True,
      "normal_walkable_world_route_proven":False,
      "source_cell_entered_by_real_gamepad":[47,199],
      "switch_frame":663079,
      "destination_pack":"0x91",
      "first_settled_arrival_frame":663203,
      "selector_convergence_frame":663116,
      "stable_arrival_xy":{"x":71,"y":59},
      "on_screen_destination_title":"おむすびころりん",
      "exact_rom_opcode_execution_proven":False,
      "current_story_gate_proven":False,
      "provenance":PROOF_REL,
    }
    return result,{"attached_count":1,"new_graph_edges":0,"source_walkability_verified":False,
                   "coordinate_resolved_existing_candidate_count":1}
