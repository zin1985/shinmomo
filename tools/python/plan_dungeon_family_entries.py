#!/usr/bin/env python3
"""Identify ROM-derived tileset8 dungeon-family world entry targets without inventing reachability."""
from __future__ import annotations
import argparse,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WORLD_ID="cfg_t01_l001_v1"
CAVE_TILESET=8

def catalog_targets(world:dict,origin_xy=(55,236)):
    known=set()
    result=[]
    for e in world["transition_edges"]:
        if e.get("source_config_id")!=WORLD_ID or e.get("destination_tileset")!=CAVE_TILESET:
            continue
        hs=e.get("source_hotspot_binding") or {}
        dest=e.get("destination_config_id")
        if not dest or not hs:continue
        spot=(hs.get("source_grid_x"),hs.get("source_grid_y"),hs.get("source_width"),hs.get("source_height"))
        if any(type(x)is not int for x in spot) or spot[2]<=0 or spot[3]<=0:
            continue
        if e.get("transition_id") in known:raise ValueError("Duplicate transition")
        known.add(e["transition_id"])
        distance=min(abs(origin_xy[0]-x)+abs(origin_xy[1]-y)
                     for x in range(spot[0],spot[0]+spot[2])
                     for y in range(spot[1],spot[1]+spot[3]))
        cheat_probe=e.get("runtime_cheat_entry_proof") or {}
        runtime_observed=(
            cheat_probe.get("observed_in_game_transition") is True
            and cheat_probe.get("source_position_supplied_by_analysis_cheat") is True
            and cheat_probe.get("normal_walkable_world_route_proven") is False
        )
        result.append({
            "transition_id":e["transition_id"],
            "source_config_id":WORLD_ID,
            "source_region":{"x":spot[0],"y":spot[1],"width":spot[2],"height":spot[3]},
            "destination_config_id":dest,
            "destination_pack":e.get("destination_pack"),
            "destination_tileset":CAVE_TILESET,
            "destination_layout":e.get("destination_layout"),
            "static_opcode_candidate":e.get("trigger_addr"),
            "distance_lower_bound_world_grid_cells":distance,
            "distance_is_walkable_route":False,
            "observed_runtime_transition":runtime_observed,
            "runtime_origin_positioned_by_cheat":runtime_observed,
            "destination_arrival_xy_confirmed":runtime_observed and
                e.get("destination_x") is not None and e.get("destination_y") is not None,
            "destination_arrival_xy":([e["destination_x"],e["destination_y"]]
                                      if runtime_observed else None),
            "normal_world_route_walkable_proven":False,
            "active_story_gate_evaluated":False,
            "evidence_status":("rom_hotspot_and_cheat_positioned_gamepad_event_verified"
                               if runtime_observed
                               else "rom_dungeon_family_and_exact_world_source_rectangle_only"),
        })
    result.sort(key=lambda x:(x["distance_lower_bound_world_grid_cells"],x["transition_id"]))
    return {"schema_version":1,
            "kind":"prioritized_rom_dungeon_family_world_hotspot_targets",
            "origin_config_id":WORLD_ID,
            "origin_observed_xy":list(origin_xy),
            "dungeon_family_criteria":"ROM setup tileset8 layouts92/94/96; not a named dungeon or actual floor transition",
            "candidate_count":len(result),
            "accessible_from_origin_current_story_proven":False,
            "recorded_navigation_probe":{
                "source_world_xy":[55,236],
                "direct_north_result_xy":[55,233],
                "north_stalled_from_this_route":True,
                "alternate_east_west_probes_did_not_find_a_walk_route":True,
                "entire_region_or_all_possible_routes_blocked_proven":False,
                "result":"route_unresolved_no_teleport_or_WRAM_edit"
            },
            "targets":result,
            "no_edges_promoted":True}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--world",type=Path,default=ROOT/"viewer/data/world.json")
    p.add_argument("--output",type=Path,default=ROOT/"data/maps/transitions/world_dungeon_family_targets_20261011.json")
    args=p.parse_args()
    world=json.loads(args.world.read_text(encoding="utf-8"))
    report=catalog_targets(world)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"targets":report["candidate_count"],"nearest":report["targets"][0]["transition_id"] if report["targets"] else None,"walk_route_proven":False},ensure_ascii=False))

if __name__=="__main__":main()
