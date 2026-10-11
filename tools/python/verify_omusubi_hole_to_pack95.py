#!/usr/bin/env python3
"""Validate Omusubi fall shaft and next pack0x95 map transfer.

Research origin cave entrance was approached by a disclosed WRAM XY
cheat; all hole/shaft/right movement below is actual SNES gameplay.
Each bounded frame capture remains local; commit metadata/digests only.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
from audit_vm_frame_series import inspect_series, BASE_SAMPLE_KEYS, SELECTOR_SAMPLE_KEYS
from audit_transition_phases import collect
ROOT=Path(__file__).resolve().parents[2]
JOIN_KEYS=("frame",)+BASE_SAMPLE_KEYS+SELECTOR_SAMPLE_KEYS
HOLE_FILES=("hole_input","hole_idle1","hole_idle2","hole_idle3","hole_idle4")
FOLLOW_FILES=("pre_right","right_input","right_neutral")
ALL_FILES=HOLE_FILES+FOLLOW_FILES
EDGE_ID="catalog_transition_0171"

def point(row):
    return (row["w0305"],row["w1573"],row["w157d"])

def verify(all_docs,world):
    for name in ALL_FILES:
        inspect_series(all_docs[name])
        if all_docs[name].get("schema_version")!=2:
            raise ValueError("Dungeon experiments require schema2 capture")
    trace=[all_docs[name] for name in ALL_FILES]
    for left,right in zip(trace,trace[1:]):
        if (left["after"]["frame"]!=right["before"]["frame"] or
            any(left["after"][key]!=right["before"][key] for key in JOIN_KEYS)):
            raise ValueError("The sampled dungeon path is not a contiguous replay")
    cave_entry=next((e for e in world["transition_edges"] if
                     e.get("transition_id")=="catalog_transition_0750"),None)
    if (not cave_entry or cave_entry.get("destination_x")!=71 or cave_entry.get("destination_y")!=59 or
        cave_entry.get("runtime_cheat_entry_proof",{}).get("source_position_supplied_by_analysis_cheat") is not True):
        raise ValueError("Cave entry from cheat-positioned world point not independently proven")
    hole=all_docs["hole_input"]
    if (hole["buttons"]!="Up" or hole["player"]!=1 or hole["requested_frames"]!=28 or
        not hole["input_sent"] or hole["input_device"]!="isolated_snes_gamepad" or
        point(hole["before"])!=(145,75,54)):
        raise ValueError("Black-hole experiment must start one cell south with actual gamepad Up")
    if any(all_docs[name]["input_sent"] for name in HOLE_FILES[1:]):
        raise ValueError("Forced shaft drop must run with no further controller input")
    hole_samples=[x for name in HOLE_FILES for x in all_docs[name]["samples"]]
    if any(x["w0305"]!=145 for x in hole_samples):
        raise ValueError("Hole drop was not wholly inside cave pack0x91")
    first_contact=next((x["frame"] for x in hole_samples if
                        (x["w1573"],x["w157d"])==(75,53)),None)
    first_jump=next((x["frame"] for x in hole_samples if
                     (x["w1573"],x["w157d"])==(70,8)),None)
    final_stop=next((x["frame"] for x in hole_samples if
                     (x["w1573"],x["w157d"])==(70,26)),None)
    if (first_contact,first_jump,final_stop)!=(663353,663453,663647):
        raise ValueError("Exact tile entry, scripted jump and shaft landing not reproduced")
    if any(point(x)!=(145,70,26) for x in all_docs["hole_idle4"]["samples"]):
        raise ValueError("Shaft landing is not stable during final 120 neutral frames")
    source=all_docs["pre_right"]
    if (source["input_sent"] or source["requested_frames"]!=60 or
        point(source["before"])!=(145,70,26) or
        point(source["after"])!=(145,70,26)):
        raise ValueError("Pre-stair source location not stable during neutral frames")
    right=all_docs["right_input"]
    if right["buttons"]!="Right" or right["player"]!=1 or right["requested_frames"]!=40:
        raise ValueError("Only bounded actual SNES Right triggers the next map")
    contact=next((row["frame"] for row in right["samples"] if
                  point(row)==(145,71,26)),None)
    if contact!=663918:
        raise ValueError("Real player did not reach first rightward source tile")
    phase=collect(right,all_docs["right_neutral"])
    if (phase["source_pack"],phase["destination_pack"],
        phase["pack_switch_frame"])!=(145,149,663933):
        raise ValueError("Map switch 0x91->0x95 unverified")
    if (phase["settled_arrival"],phase["first_settled_arrival_frame"])!=(
        {"x":22,"y":8},664018) or phase["stable_observed_frames"]<8:
        raise ValueError("Pack0x95 arrival not stable")
    selector_frames=[
        row["frame"] for row in
        (all_docs["right_input"]["samples"]+all_docs["right_neutral"]["samples"])
        if row["frame"]>=phase["pack_switch_frame"] and
        row["w126e"]==149 and row["w12b4"]==149
    ]
    if not selector_frames or selector_frames[0]!=663967:
        raise ValueError("Pack0x95 selector convergence not verified")
    selected=[e for e in world["transition_candidates"] if
              e.get("transition_id")==EDGE_ID]
    if len(selected)!=1:raise ValueError("Expected one ROM 0x95 entry candidate")
    e=selected[0]
    bound_source=e.get("source_config_id")
    if bound_source not in (None,"cfg_t08_l092_v2"):
        raise ValueError("Pack0x95 source bound to unrelated map")
    if bound_source=="cfg_t08_l092_v2" and not (
        e.get("runtime_floor_transition_proof",{}).get("source_movement_confirmed") is True and
        e.get("runtime_floor_transition_proof",{}).get("script_opcode_PC_proven") is False and
        e.get("runtime_floor_transition_proof",{}).get("source_arrived_via_cheat_origin_hole_sequence") is True):
        raise ValueError("Existing cave source binding lacks original replay scope")
    if (
        e.get("destination_config_id")!="cfg_t08_l096_v2" or
        e.get("destination_pack")!="0x95" or
        (e.get("destination_x"),e.get("destination_y"))!=(22,8) or
        e.get("trigger_addr")!="CC:D377" or
        e.get("confidence")!="strong_candidate"):
        raise ValueError("Static source-unbound ROM candidate no longer matches exact arrival")
    meta={
      "schema_version":1,
      "kind":"verified_cheat_origin_cave_hole_shaft_sequence",
      "source_map_config_id":"cfg_t08_l092_v2",
      "pack_unchanged_hex":"0x91",
      "original_world_entry_positioned_by_cheat":True,
      "hole_approach_positioned_by_cheat":True,
      "normal_world_route_to_hole_proven":False,
      "source_hole_tile":{"x":75,"y":53,"metatile_id":30},
      "real_input_started_at":{"x":75,"y":54},
      "real_up_entry_frame":first_contact,
      "unmodified_event_jump_frame":first_jump,
      "unmodified_event_jump_target":{"x":70,"y":8},
      "automatic_descending_shaft":True,
      "automatic_descent_has_no_gamepad_input":True,
      "final_shaft_landing_first_frame":final_stop,
      "final_shaft_landing":{"x":70,"y":26},
      "stable_neutral_end_frame":all_docs["hole_idle4"]["after"]["frame"],
      "floor_index_or_story_flag_proven":False,
      "CPU_opcode_PC_observed":False,
      "runtime_sequence_local_only":True,
    }
    transfer={
      "schema_version":1,"kind":"verified_cave_source_bound_pack95_transfer",
      "prior_hole_shaft_proof":"data/maps/transitions/omusubi_hole_shaft_verified_20261011.json",
      "source_config_id":"cfg_t08_l092_v2",
      "source_pack":"0x91",
      "source_shafts_final_xy":{"x":70,"y":26},
      "source_real_input_contact_cell":{"x":71,"y":26},
      "source_contact_frame":contact,
      "destination_config_id":"cfg_t08_l096_v2",
      "destination_pack":"0x95",
      "destination_xy":{"x":22,"y":8},
      "switch_frame":663933,
      "selector_convergence_frame":663967,
      "arrival_stable_frame":664018,
      "destination_stable_through_frame":all_docs["right_neutral"]["after"]["frame"],
      "existing_rom_candidate_id":EDGE_ID,
      "existing_rom_candidate_opcode_PC":"CC:D377",
      "static_candidate_was_source_unbound":True,
      "ROM_candidate_opcode_executed_PC_proven":False,
      "runtime_source_map_config_proven":True,
      "source_reached_from_cheat_origin_cave_path":True,
      "normal_world_walkable_route_proven":False,
      "universal_story_gate_proven":False,
      "new_candidate_count":0,
      "new_source_bound_edge_count":1,
      "new_dungeon_floor_or_map_pack_observed":True,
    }
    return meta,transfer

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ALL_FILES:
        ap.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    args=ap.parse_args()
    raw={k:getattr(args,k).read_bytes() for k in ALL_FILES}
    world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
    a,b=verify({k:json.loads(raw[k]) for k in ALL_FILES},world)
    hashes={k:hashlib.sha256(v).hexdigest().upper() for k,v in raw.items()}
    a["local_trace_sha256"]={k:hashes[k] for k in HOLE_FILES}
    b["local_trace_sha256"]={k:hashes[k] for k in FOLLOW_FILES}
    for name,doc in (("omusubi_hole_shaft_verified_20261011.json",a),
                     ("omusubi_pack91_to_pack95_verified_20261011.json",b)):
        (ROOT/"data/maps/transitions"/name).write_text(
            json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"hole":"(75,53) -> jump (70,8) -> forced descent (70,26)",
                      "next":"pack0x91 (71,26)->pack0x95 (22,8)",
                      "switch_frame":b["switch_frame"],"arrival_frame":b["arrival_stable_frame"],
                      "unproven_cpu_pc":True},ensure_ascii=False))
if __name__=="__main__":main()
