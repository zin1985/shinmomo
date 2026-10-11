#!/usr/bin/env python3
"""Verify the cave entrance's conditional return to the prior world origin.

The cave was entered from a cheat-positioned world coordinate. The
return itself is unmodified SNES Down->Up gameplay with observed
frame-end state and TWO contiguous neutral 120-frame captures.
No CPU handler PC or universal saved-map target is inferred.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from audit_vm_frame_series import inspect_series, BASE_SAMPLE_KEYS, SELECTOR_SAMPLE_KEYS
from audit_transition_phases import collect
ROOT=Path(__file__).resolve().parents[2]
EDGE_ID="runtime_pack91_world_saved_origin_return_20261011"

def verify(approach:dict, input_doc:dict, neutral1:dict,neutral2:dict,incoming:dict):
    a=inspect_series(approach)
    b=inspect_series(input_doc)
    c=inspect_series(neutral1)
    d=inspect_series(neutral2)
    if any(z["schema_version"]!=2 for z in (a,b,c,d)):
        raise ValueError("Strict selector-aware schema2 captures required")
    if not (a["input_sent"] and b["input_sent"] and
            approach["buttons"]=="Down" and input_doc["buttons"]=="Up" and
            approach["player"]==1 and input_doc["player"]==1 and
            a["complete_contiguous_frames"]==50 and b["complete_contiguous_frames"]==35 and
            c["complete_contiguous_frames"]==120 and d["complete_contiguous_frames"]==120 and
            not c["input_sent"] and not d["input_sent"]):
        raise ValueError("Need actual bounded controller Down/Up followed by two neutral windows")
    keys=("frame",)+BASE_SAMPLE_KEYS+SELECTOR_SAMPLE_KEYS
    if (a["final_frame"]!=b["initial_frame"] or
        any(approach["after"][k]!=input_doc["before"][k] for k in keys)):
        raise ValueError("The cave approach and exit are not contiguous")
    if (incoming.get("kind")!="cheat_positioned_runtime_dungeon_entrance" or
        incoming.get("original_edge_id")!="catalog_transition_0750" or
        incoming.get("destination_pack")!="0x91" or
        incoming.get("destination_xy")!={"x":71,"y":59} or
        incoming.get("source_normal_world_walk_route_proven") is not False):
        raise ValueError("Independent, disclosed cheat-origin cave entrance proof missing")
    if (approach["before"]["w0305"],approach["before"]["w1573"],
        approach["before"]["w157d"])!=(145,71,59):
        raise ValueError("Dungeon replay must begin at verified cave arrival")
    if (approach["after"]["w0305"],approach["after"]["w1573"],
        approach["after"]["w157d"])!=(145,71,61):
        raise ValueError("Cave approach did not reach the exact south floor cell")
    contacts=[s["frame"] for s in input_doc["samples"]
              if s["w0305"]==145 and
                 (s["w1573"],s["w157d"])==(71,59)]
    if not contacts or contacts[0]!=663402:
        raise ValueError("Return floor tile must be entered by normal controller movement")
    report=collect(input_doc,neutral1,stability_frames=8,
                   extra_neutral_trace=neutral2)
    if (report["source_pack"],report["destination_pack"],
        report["pack_switch_frame"])!=(145,76,663417):
        raise ValueError("Cave-to-world map switch not reproduced")
    if (report["first_settled_arrival_frame"],
        report["settled_arrival"])!=(663532,{"x":47,"y":199}):
        raise ValueError("Actual saved-origin landing not independently stable")
    if report["neutral_capture_chunk_count"]!=2 or report["stable_observed_frames"]<120:
        raise ValueError("Insufficient verified neutral stability")
    allrows=input_doc["samples"]+neutral1["samples"]+neutral2["samples"]
    context=next((r["frame"] for r in allrows if
                  r["frame"]>=663417 and r["w126e"]==76 and r["w12b4"]==76),None)
    if context!=663451:
        raise ValueError("Selector convergence not independently verified")
    if any(row["w0305"]!=76 or
           (row["w1573"],row["w157d"])!=(47,199)
           for row in neutral2["samples"]):
        raise ValueError("Return world state not stable through entire extra capture")
    return {
        "schema_version":1,"kind":"verified_conditional_cave_saved_origin_return",
        "existing_cave_entry_proof":"data/maps/transitions/omusubi_kororin_cheat_entry_verified_20261011.json",
        "entry_origin_supplied_by_analysis_coordinate_cheat":True,
        "normal_world_walk_to_cave_proven":False,
        "cave_source_map_config_id":"cfg_t08_l092_v2",
        "cave_source_pack":"0x91",
        "source_inside_cave_xy":{"x":71,"y":61},
        "return_tile_entered_with_gamepad":{"x":71,"y":59},
        "return_tile_metatile_id":32,
        "contact_frame":contacts[0],
        "return_map_switch_frame":663417,
        "return_context_selector_frame":context,
        "world_destination_map_config_id":"cfg_t01_l001_v1",
        "world_destination_pack":"0x4C",
        "world_arrival_xy_in_this_saved_context":{"x":47,"y":199},
        "first_settled_arrival_frame":663532,
        "observed_stable_through_frame":neutral2["after"]["frame"],
        "stable_observed_frames":report["stable_observed_frames"],
        "return_requires_original_saved_map_context":True,
        "return_world_xy_for_other_saves_verified":False,
        "floor_to_floor_transition_verified":False,
        "CPU_handler_PC_observed":False,
        "VM_opcode_56_executed_proven":False,
        "new_source_map_binding_promoted":False,
        "normal_input_buttons":["Down","Up"],
        "neutral_capture_count":2,
        "trace_data_committed":False,
        "new_graph_edge_count":1,
        "proposed_edge_id":EDGE_ID,
        "result":"confirmed_runtime_saved_origin_return_one_exact_context"
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--approach",type=Path,required=True)
    ap.add_argument("--input",type=Path,required=True)
    ap.add_argument("--neutral1",type=Path,required=True)
    ap.add_argument("--neutral2",type=Path,required=True)
    ap.add_argument("--output",type=Path,default=ROOT/"data/maps/transitions/omusubi_cave_world_return_verified_20261011.json")
    args=ap.parse_args()
    payload={n:getattr(args,n).read_bytes() for n in ("approach","input","neutral1","neutral2")}
    prev=json.loads((ROOT/"data/maps/transitions/omusubi_kororin_cheat_entry_verified_20261011.json").read_text(encoding="utf-8"))
    report=verify(*(json.loads(payload[n]) for n in ("approach","input","neutral1","neutral2")),prev)
    report["local_raw_trace_sha256"]={n:hashlib.sha256(payload[n]).hexdigest().upper() for n in payload}
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"source":"pack91 (71,59)","world":"pack4C (47,199)",
                      "switch":663417,"landed":663532,"stable_frames":report["stable_observed_frames"],
                      "CPU_PC_observed":False,"scope":"this cheat-origin saved map context","status":"PASS"},ensure_ascii=False))
if __name__=="__main__":
    main()
