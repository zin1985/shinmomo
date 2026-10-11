#!/usr/bin/env python3
"""Strict controller-based reverse stair transfer pack0x95->pack0x91.

Pack0x95 state follows from previously cheat-seeded world->cave
exploration. The return control is actual Down then Up and two
continuous neutral frame captures, with no WRAM writes during input.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from audit_vm_frame_series import inspect_series, BASE_SAMPLE_KEYS,SELECTOR_SAMPLE_KEYS
from audit_transition_phases import collect

ROOT=Path(__file__).resolve().parents[2]
EDGE_ID="catalog_transition_0194"
JOIN_KEYS=("frame",)+BASE_SAMPLE_KEYS+SELECTOR_SAMPLE_KEYS

def verify(down,up,neutral1,neutral2,world):
    parts=(down,up,neutral1,neutral2)
    for doc in parts:
        audited=inspect_series(doc)
        if audited["schema_version"]!=2:
            raise ValueError("Require schema2 complete frame-end capture")
    for prev,curr in zip(parts,parts[1:]):
        if (prev["after"]["frame"]!=curr["before"]["frame"] or
            any(prev["after"][key]!=curr["before"][key] for key in JOIN_KEYS)):
            raise ValueError("Replay frame or WRAM boundary is not contiguous")
    floor=next((e for e in world["transition_edges"] if
                e.get("transition_id")=="catalog_transition_0171"),None)
    if (not floor or floor.get("source_config_id")!="cfg_t08_l092_v2" or
        floor.get("destination_config_id")!="cfg_t08_l096_v2" or
        (floor.get("destination_x"),floor.get("destination_y"))!=(22,8) or
        floor.get("runtime_floor_transition_proof",{}).get("source_arrived_via_cheat_origin_hole_sequence") is not True):
        raise ValueError("Independent pack0x95 arrival not proven")
    if (down.get("buttons")!="Down" or down.get("player")!=1 or
        down.get("requested_frames")!=11 or
        up.get("buttons")!="Up" or up.get("player")!=1 or
        up.get("requested_frames")!=20 or
        not down.get("input_sent") or not up.get("input_sent") or
        down.get("input_device")!="isolated_snes_gamepad" or
        up.get("input_device")!="isolated_snes_gamepad" or
        neutral1.get("input_sent") or neutral2.get("input_sent") or
        neutral1.get("requested_frames")!=120 or
        neutral2.get("requested_frames")!=120):
        raise ValueError("Must replay actual Down/Up controller and neutral windows")
    if (down["before"]["w0305"],down["before"]["w1573"],down["before"]["w157d"])!=(149,22,8):
        raise ValueError("Unexpected prior pack0x95 actual arrival source")
    if (down["after"]["w0305"],down["after"]["w1573"],down["after"]["w157d"])!=(149,22,9):
        raise ValueError("Actual Down did not step off arrival tile")
    contact=[row["frame"] for row in up["samples"] if
             (row["w0305"],row["w1573"],row["w157d"])==(149,22,8)]
    if not contact or contact[0]!=664095:
        raise ValueError("Real Up input did not reenter exact stair tile")
    report=collect(up,neutral1,extra_neutral_trace=neutral2,stability_frames=8)
    if (report["source_pack"],report["destination_pack"],report["pack_switch_frame"])!=(149,145,664110):
        raise ValueError("Map pack reverse transfer not reproduced")
    if (report["settled_arrival"],report["first_settled_arrival_frame"])!=(
        {"x":71,"y":26},664196):
        raise ValueError("Stable reverse transfer arrival unproven")
    selectors=next((s["frame"] for s in up["samples"]+neutral1["samples"]+neutral2["samples"] if
                    s["frame"]>=664110 and s["w126e"]==145 and s["w12b4"]==145),None)
    if selectors!=664145:raise ValueError("Selector convergence frame mismatch")
    if any((row["w0305"],row["w1573"],row["w157d"])!=(145,71,26)
           for row in neutral2["samples"]):
        raise ValueError("Additional 120 neutral frames not stable at cave landing")
    e=next((e for e in world["transition_candidates"] if e["transition_id"]==EDGE_ID),None)
    if (not e or e.get("script_pack")!="0x95" or
        e.get("source_config_id") not in (None,"cfg_t08_l096_v2") or
        e.get("destination_config_id")!="cfg_t08_l092_v2" or
        e.get("destination_pack")!="0x91" or
        e.get("trigger_addr")!="CC:DA1A" or
        e.get("confidence")!="strong_candidate"):
        raise ValueError("Static unique pack0x95 reverse candidate changed")
    if e.get("source_config_id")=="cfg_t08_l096_v2" and not (
        e.get("runtime_reverse_stair_proof",{}).get("returned_via_real_gamepad") is True and
        e.get("runtime_reverse_stair_proof",{}).get("ROM_opcode_CPU_executed_proven") is False):
        raise ValueError("Earlier reverse candidate binding lacks proof provenance")
    return {
      "schema_version":1,"kind":"verified_pack95_reverse_stair_return",
      "source_config_id":"cfg_t08_l096_v2","source_pack":"0x95",
      "prior_arrival_stair_xy":{"x":22,"y":8},
      "real_down_cell":{"x":22,"y":9},
      "return_contact_cell":{"x":22,"y":8},
      "return_contact_frame":664095,
      "source_real_gamepad_buttons":["Down","Up"],
      "source_reached_via_cheat_origin_cave_route":True,
      "normal_world_walk_to_cave_proven":False,
      "pack_switch_frame":664110,
      "selector_convergence_frame":664145,
      "destination_config_id":"cfg_t08_l092_v2",
      "destination_pack":"0x91",
      "settled_arrival_xy":{"x":71,"y":26},
      "first_settled_arrival_frame":664196,
      "stable_observed_through_frame":neutral2["after"]["frame"],
      "stable_frames":report["stable_observed_frames"],
      "existing_static_reverse_candidate":EDGE_ID,
      "static_candidate_opcode_address":"CC:DA1A",
      "actual_opcode_CPU_PC_observed":False,
      "source_config_runtime_verified":True,
      "story_condition_verified":False,
      "pack95_stair_at_22_31_proven_as_exit":False,
      "new_transition_candidate_count":0,
      "new_bound_edge_count":1,
      "all_raw_traces_local_only":True,
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ("down","up","neutral1","neutral2"):
        ap.add_argument("--"+n,type=Path,required=True)
    args=ap.parse_args()
    data={n:getattr(args,n).read_bytes() for n in ("down","up","neutral1","neutral2")}
    world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
    doc=verify(*(json.loads(data[n]) for n in ("down","up","neutral1","neutral2")),world)
    doc["local_trace_sha256"]={n:hashlib.sha256(raw).hexdigest().upper() for n,raw in data.items()}
    path=ROOT/"data/maps/transitions/omusubi_pack95_reverse_stair_verified_20261011.json"
    path.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"return":"0x95 (22,8) -> 0x91 (71,26)",
                      "map_switch_frame":664110,
                      "arrive_frame":664196,"selector_frame":664145,
                      "stability":doc["stable_frames"],"status":"PASS"},ensure_ascii=False))

if __name__=="__main__":main()
