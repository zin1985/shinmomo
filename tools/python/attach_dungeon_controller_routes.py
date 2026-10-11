"""Attach audited gamepad traversable paths to exact scene packs, not map edges.

A path staying in the same map is NOT a new transition edge and does
not authorize a global collision-map or storyline predicate inference.
"""
from __future__ import annotations
from copy import deepcopy
PROOF="data/maps/transitions/dungeon_three_pack_24_controller_turn_routes_20261011.json"
SCENES={
  "0xBD":("cfg_t36_l150_v2",{"x":15,"y":37}),
  "0xB9":("cfg_t25_l129_v2",{"x":68,"y":25}),
  "0xAB":("cfg_t49_l176_v2",{"x":22,"y":5})
}
BUTTON_SEQS=[
 ["Up","Left","Up"],["Up","Right","Up"],
 ["Down","Left","Down"],["Down","Right","Down"],
 ["Left","Down","Left"],["Right","Down","Right"],
 ["Left","Up","Left"],["Right","Up","Right"]]
def attach(maps:list[dict],proof:dict,edges:list[dict]):
    if (proof.get("schema_version")!=1 or
        proof.get("kind")!="three_dungeons_24_real_gamepad_turning_routes_without_pack_switch" or
        proof.get("created_from_hidden_lab_original_state_restored") is not True or
        proof.get("initial_world_entrance_cheat_seeded") is not True or
        proof.get("genuine_onscene_controller_XY_coordinate_cheat") is not False or
        proof.get("pack_scoped_routes")!={pk:8 for pk in SCENES} or
        proof.get("three_dungeons")!=3 or
        proof.get("true_multiturn_controller_routes")!=24 or
        proof.get("total_directional_gamepad_segments")!=72 or
        proof.get("real_controller_frames_per_segment")!=72 or
        proof.get("neutral_frames_after_each_route")!=120 or
        proof.get("added_cross_map_transition_edges")!=0 or
        proof.get("other_map_exits_universally_excluded") is not False or
        proof.get("raw_ROM_screenshots_savestates_frames_not_committed") is not True or
        proof.get("source_previous_verified_scene_trials")!="data/maps/transitions/five_scene_modal_tests_and_pack82_world_return_20261011.json" or
        len(proof.get("routes",[]))!=24):
        raise ValueError("Missing protected local gamepad route scope or forged map transition")
    byid={m["config_id"]:m for m in maps}
    if len(byid)!=len(maps):raise ValueError("Duplicate source config IDs")
    edge_by_id={e["transition_id"]:e for e in edges}
    if len(edge_by_id)!=len(edges):raise ValueError("Duplicate original transition IDs")
    # Ground each route in an already independently measured actual
    # world-to-dungeon gamepad entrance, rather than pack-name guesses.
    for pk,(cfg,start) in SCENES.items():
        matches=[e for e in edges
                 if e.get("source_config_id")=="cfg_t01_l001_v1" and
                    e.get("destination_config_id")==cfg and e.get("destination_pack")==pk and
                    (e.get("runtime_world_entry_batch_probe") or {}).get("actual_SNES_gamepad_triggered_event") is True]
        if len(matches)!=1 or (matches[0].get("destination_x"),matches[0].get("destination_y"))!=(start["x"],start["y"]):
            raise ValueError("No exact independently verified dungeon world entry for "+pk)
    result=deepcopy(maps)
    mapped={m["config_id"]:m for m in result}
    groups={pk:[] for pk in SCENES}
    seen=set()
    for route in proof["routes"]:
        pk=route.get("source_scene_pack")
        if pk not in SCENES:raise ValueError("Unexpected local route pack")
        cfg,start=SCENES[pk]
        idx=route.get("route_index")
        path=route.get("observed_position_trace_grid")
        turn=route.get("turn_endpoints_grid")
        if (not isinstance(idx,int) or idx not in range(8) or (pk,idx) in seen or
            route.get("id")!=f"runtime_turn_path_{pk[2:]}_{idx:02d}" or
            route.get("source_config_id")!=cfg or
            route.get("source_original_scene_xy")!=start or
            route.get("held_button_sequence")!=BUTTON_SEQS[idx] or
            route.get("held_frames_per_step")!=72 or
            route.get("neutral_frames_after_path")!=120 or
            route.get("from_world_entrance_cheat_adjacent") is not True or
            route.get("no_scene_xy_cheat_during_controller_path") is not True or
            route.get("actual_SNES_gamepad_path") is not True or
            route.get("source_pack_unchanged_in_all_observed_frames") is not True or
            route.get("no_new_map_transition_verified_this_route") is not True or
            route.get("other_story_phase_or_turn_routes_excluded") is not False or
            route.get("exact_collision_OR_wall_cause_proven") is not False or
            route.get("actual_CPU_handler_PC_observed") is not False or
            route.get("raw_ROM_screenshot_and_frame_data_committed") is not False or
            len(route.get("gamepad_frame_sha256",[]))!=3 or
            len(route.get("neutral_frame_sha256",""))!=64 or
            len(route.get("final_onscreen_screenshot_sha256",""))!=64 or
            not isinstance(path,list) or not 1<=len(path)<=300 or
            not isinstance(turn,list) or len(turn)!=4 or
            path[0]!=start or turn[0]!=start or
            path[-1]!=route.get("arrived_at_grid") or
            turn[-1]!=route.get("arrived_at_grid")):
            raise ValueError("Unverified exact source and directional trace: "+str(pk)+" "+str(idx))
        if any(not isinstance(k,dict) or set(k)!={"x","y"} or
               not all(isinstance(v,int) and 0<=v<=255 for v in k.values())
               for k in path+turn):
            raise ValueError("Invalid actual grid XY")
        if any(abs(a["x"]-b["x"])+abs(a["y"]-b["y"])>1
               for a,b in zip(path,path[1:])):
            raise ValueError("Local route skips tile positions; do not draw invented corridor")
        seen.add((pk,idx))
        groups[pk].append(route)
    if len(seen)!=24:raise ValueError("Not all 24 independent routes observed")
    for pk,(cfg,start) in SCENES.items():
        if len(groups[pk])!=8:raise ValueError("Not eight routes from specific pack")
        map_=mapped[cfg]
        if map_.get("runtime_controller_route_contexts"):
            raise ValueError("Repeated observed-route attachment")
        map_["runtime_controller_route_contexts"]=[{
          "scene_pack":pk,
          "scene_config_id":cfg,
          "source_saved_entry_grid":start,
          "original_world_entrance_cheat_seeded":True,
          "real_gamepad_movement_without_XY_cheat":True,
          "story_state_alternatives_unverified":True,
          "all_eight_routes_have_no_map_switch":True,
          "source":PROOF,
          "route_count":8,
          "routes":groups[pk]
        }]
    tiles={pk:len({(p["x"],p["y"]) for r in paths
                  for p in r["observed_position_trace_grid"]}) for pk,paths in groups.items()}
    return result,{
      "three_dungeon_scene_contexts":3,
      "verified_controller_route_count":24,
      "real_directional_72frame_segments":72,
      "observed_distinct_grid_cells_by_pack":tiles,
      "new_graph_edges":0,
      "all_dungeon_exits_mapped":False,
      "source":PROOF
    }
