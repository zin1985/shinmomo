#!/usr/bin/env python3
"""Prove input-independent pack0x96 vertical movement from both real controller traces."""
from __future__ import annotations
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
LOCAL=Path(r"C:\Users\zin\AppData\Local\shinmomo-bg-lab")
OUT=ROOT/"data/maps/transitions/pack96_up_down_identical_forced_movement_20261011.json"

def verify():
    down=json.loads((ROOT/"data/maps/transitions/world_14_reverse_returns_after_cheat_arrivals_20261011.json").read_text(encoding='utf-8'))
    up=json.loads((ROOT/"data/maps/transitions/six_scene_up_no_pack_switch_20261011.json").read_text(encoding='utf-8'))
    negative=[x for x in down["unconfirmed_local_direction_returns"] if x["source_scene_pack"]=="0x96"]
    rising=[x for x in up["probes"] if x["source_pack"]=="0x96"]
    if len(negative)!=1 or len(rising)!=1:raise ValueError("Missing pack0x96 both direction trials")
    a,b=negative[0],rising[0]
    if (a["source_world_entrance_cheat_positioned"] is not True or
        a["return_route_did_not_cheat_coordinates"] is not True or
        b["reverse_experiment_controller_has_no_cheat"] is not True or
        b["controller"]!="Up" or
        b["no_pack_switch_in_observation"] is not True):
        raise ValueError("Wrong direction or cheat provenance")
    requested=set(a["underlying_source_file_digest"]+b["trace_sha256"])
    found={}
    for path in (LOCAL/"captures").glob("vmframes_*.json"):
        digest=hashlib.sha256(path.read_bytes()).hexdigest().upper()
        if digest in requested:found.setdefault(digest,path)
    if set(found)!=requested:raise ValueError("Exact raw traces missing")
    def resolve(hashes):
        data=[json.loads(found[h].read_text(encoding="utf-8")) for h in hashes]
        if len(data)!=3:raise ValueError("Expected three contiguous frame chunks")
        for first,second in zip(data,data[1:]):
            if first["after"]["frame"]!=second["before"]["frame"]:
                raise ValueError("Disjoint source input recording")
        return data,[x for d in data for x in d["samples"]]
    D,rows_down=resolve(a["underlying_source_file_digest"])
    U,rows_up=resolve(b["trace_sha256"])
    if (D[1]["buttons"]!="Down" or U[1]["buttons"]!="Up" or
        D[1]["input_device"]!="isolated_snes_gamepad" or
        U[1]["input_device"]!="isolated_snes_gamepad" or
        D[1]["requested_frames"]!=72 or U[1]["requested_frames"]!=72 or
        D[0]["input_sent"] or U[0]["input_sent"] or
        D[2]["input_sent"] or U[2]["input_sent"] or
        D[0]["requested_frames"]!=12 or U[0]["requested_frames"]!=12 or
        D[2]["requested_frames"]!=120 or U[2]["requested_frames"]!=120):
        raise ValueError("Different actual gamepad or neutral duration")
    if len(rows_down)!=204 or len(rows_up)!=204:
        raise ValueError("Missing full 204 frame samples")
    positions=lambda data:[(x["frame"],x["w0305"],x["w1573"],x["w157d"]) for x in data]
    xs=positions(rows_down)
    ys=positions(rows_up)
    if xs!=ys:raise ValueError("The two direction inputs have DIFFERENT position traces")
    if (xs[0]!=(663329,150,39,17) or xs[-1]!=(663532,150,39,24)):
        raise ValueError("Unexpected native movement span")
    changes=[]
    last=(D[0]["before"]["w1573"],D[0]["before"]["w157d"])
    for frame,pack,x,y in xs:
        if pack!=150:raise ValueError("Map switched during ongoing descent")
        if (x,y)!=last:
            changes.append({"frame":frame,"x":x,"y":y})
            last=(x,y)
    expected=[663333,663342,663351,663360,663369,663378,663387]
    if ([r["frame"] for r in changes]!=expected or
        [r["y"] for r in changes]!=[18,19,20,21,22,23,24]):
        raise ValueError("Exact forced downward motion cadence disagrees")
    doc={
      "schema_version":1,
      "kind":"pack96_input_direction_independent_downward_movement_local_state",
      "source_config_id":"cfg_t09_l098_v2","pack":"0x96",
      "real_world_scene_arrival_xy":{"x":39,"y":17},
      "source_world_entrance_originally_coordinate_cheated":True,
      "controller_path_no_xy_cheat":True,
      "compared_actual_buttons":["Down","Up"],
      "neutral_before_frames":12,
      "actual_button_held_frames":72,
      "neutral_after_frames":120,
      "same_game_frame_range":[663329,663532],
      "both_direction_position_series_identical_frame_count":204,
      "same_pack_during_entire_span":True,
      "observed_positions":changes,
      "downward_every_nine_frames":True,
      "last_xy":{"x":39,"y":24},
      "actual_CPU_opcode_PC_proven":False,
      "proven_mechanism":"reproducible_direction_independent_movement",
      "root_cause_interpretation":"scripted_forced_walk_or_physics_unresolved",
      "generalizes_to_other_savestates":False,
      "normal_world_route_walkability_proven":False,
      "raw_frame_traces_committed":False,
      "down_trace_sha256":a["underlying_source_file_digest"],
      "up_trace_sha256":b["trace_sha256"]
    }
    OUT.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"identical_frames":204,"identical_steps":7,
                      "first_frame":663333,"last_step":663387,"end":{"x":39,"y":24}},ensure_ascii=False))
    return doc

if __name__=="__main__":verify()
