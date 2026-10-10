#!/usr/bin/env python3
"""Validate both directions of a coordinate-sensitive Tabidachi village/world link.

The return from village to world is a native saved-map boundary mechanism.
World->village is statically associated with a VM 0x53 hotspot at CC:0B08,
but this verifier does not infer VM handler execution without CPU-hook proof.
Raw frame/trace files and savestates remain local, outside Git.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"data/maps/transitions/tabidachi_x29_world_x55_roundtrip_20261011.json"
ROM_SHA="F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"


def trace_rows(raw, *, kind, initial_pack, final_pack, expected_steps):
    if raw.get("kind")!=kind or raw.get("input_device","isolated_snes_gamepad")!="isolated_snes_gamepad":
        raise ValueError("Wrong local isolated replay type/input")
    rows=raw.get("rows")
    if not isinstance(rows,list) or not 2<=len(rows)<=120:
        raise ValueError("Invalid one-frame replay count")
    if expected_steps is not None and len(rows)!=expected_steps:
        raise ValueError("Unexpected replay length")
    observations=[]
    for i,row in enumerate(rows,1):
        if row.get("step")!=i or row.get("frame1")!=row.get("frame0")+1:
            raise ValueError("Non-contiguous replay step")
        if i>1 and row["frame0"]!=rows[i-2]["frame1"]:
            raise ValueError("Missing frame in replay")
        t=json.loads(Path(row["file"]).read_text(encoding="utf-8"))
        if (t.get("kind")!="isolated_vm_execution_trace" or
            t.get("input_sent") is not True or
            t.get("input_device")!="isolated_snes_gamepad" or
            t.get("buttons")!="Down" or t.get("player")!=1 or
            t.get("requested_input_frames")!=1 or
            t.get("requested_neutral_frames")!=0 or
            t.get("advanced_frames")!=1 or t.get("hook_errors") or
            t.get("dropped_events")!=0):
            raise ValueError("Unsafe/incomplete isolated controller capture")
        b,a=t.get("before") or {},t.get("after") or {}
        if (b.get("frame")!=row["frame0"] or a.get("frame")!=row["frame1"] or
            b.get("w0305")!=row["pack0"] or a.get("w0305")!=row["pack1"] or
            a.get("w1573")!=row["x"] or a.get("w157d")!=row["y"] or
            len(t.get("events",[]))!=row.get("hook_hits",0)):
            raise ValueError("Raw trace and replay manifest disagree")
        observations.append({"frame":row["frame1"],"from_pack":row["pack0"],
                             "pack":row["pack1"],"x":row["x"],"y":row["y"],
                             "cpu_hook_count":len(t["events"])})
    if (observations[0]["from_pack"]!=initial_pack or
        any(x["pack"]!=initial_pack for x in observations[:-1]) or
        observations[-1]["from_pack"]!=initial_pack or
        observations[-1]["pack"]!=final_pack):
        raise ValueError("Unexpected pack sequence: one final switch required")
    return observations


def summarize(village,world,settled,capture_hashes):
    v=trace_rows(village,kind="native_world_return_variant_replay",initial_pack=0x50,
                 final_pack=0x4C,expected_steps=20)
    w=trace_rows(world,kind="world_to_village_exact_reentry",initial_pack=0x4C,
                 final_pack=0x50,expected_steps=18)
    if village.get("start_state")!="vmtrace_tabidachi_pack50_south_x29_y54_20261011":
        raise ValueError("Wrong village exit fixture")
    if world.get("origin_state")!="vmtrace_world_pack4c_x55_y236_preentry_20261011":
        raise ValueError("Wrong world entry fixture")
    if not all(p["x"]==29 for p in v[:-1]) or not all(p["x"]==55 for p in w):
        raise ValueError("Path is not on required source x-column")
    if (v[0]["y"]!=54 or [v[-1]["x"],v[-1]["y"]]!=[55,237] or
        w[0]["y"]!=236 or w[-1]["y"]!=237):
        raise ValueError("Unexpected source/destination coordinates")
    inside=[p for p in v[:-1] if p["y"]==55]
    outside=[p for p in v[:-1] if p["y"]==56]
    entered=[p for p in w[:-1] if p["y"]==237]
    if not inside or not outside or not entered:
        raise ValueError("Required native boundary / world trigger never entered")
    if not inside[-1]["frame"]<outside[0]["frame"]<v[-1]["frame"]:
        raise ValueError("Native boundary frame ordering contradiction")
    if not entered[0]["frame"]<w[-1]["frame"]:
        raise ValueError("Scripted entry frame ordering contradiction")
    if (settled.get("source")!="vmtrace_world_pack4c_x55_y236_preentry_20261011.State" or
        settled.get("switch_frame")!=w[-1]["frame"] or
        settled.get("settled_pack")!="0x50" or
        settled.get("settled_x")!="0x1D" or
        settled.get("settled_y")!="0x37" or
        settled.get("settled_frame",0)<=w[-1]["frame"]):
        raise ValueError("Post-transition village destination was not verified")
    for digest in capture_hashes.values():
        if not isinstance(digest,str) or len(digest)!=64:
            raise ValueError("Missing immutable capture hash")
    return {
        "schema_version":1,
        "kind":"verified_coordinate_sensitive_village_world_roundtrip",
        "canonical_rom_sha256":ROM_SHA,
        "village_to_world":{
            "mechanism":"native_out_of_bounds_saved_map_return",
            "source_config_id":"cfg_t04_l008_v2",
            "source_pack":"0x50",
            "confirmed_exit_cell":{"x":29,"y":55},
            "last_inside_frame":inside[-1]["frame"],
            "first_outside_cell":{"x":29,"y":56},
            "first_outside_frame":outside[0]["frame"],
            "switch_frame":v[-1]["frame"],
            "destination_config_id":"cfg_t01_l001_v1",
            "destination_pack":"0x4C",
            "arrival":{"x":55,"y":237},
            "input_frames":len(v),
            "cpu_handler_execution_observed":False
        },
        "world_to_village":{
            "mechanism":"world_coordinate_VM0x53_candidate_from_static_ROM_not_CPU_proven",
            "source_config_id":"cfg_t01_l001_v1",
            "world_entry_point":{"x":55,"y":237},
            "world_entry_first_frame":entered[0]["frame"],
            "switch_to_pack_0x50_frame":w[-1]["frame"],
            "destination_config_id":"cfg_t04_l008_v2",
            "settled_arrival":{"x":29,"y":55},
            "settled_arrival_frame":settled["settled_frame"],
            "static_candidate_opcode_addr":"CC:0B08",
            "input_frames":len(w),
            "cpu_vm_opcode_execution_observed":False
        },
        "position_dependent_native_return":{
            "confirmed_coordinate_pairs":[
                {"source_village_cell":{"x":28,"y":55},"world_arrival":{"x":54,"y":237},
                 "evidence":"data/maps/transitions/tabidachi_south_boundary_to_world_20260930.json"},
                {"source_village_cell":{"x":29,"y":55},"world_arrival":{"x":55,"y":237},
                 "evidence":"data/maps/transitions/tabidachi_x29_world_x55_roundtrip_20261011.json"}
            ],
            "full_exit_width_proven":False,
            "general_coordinate_transform_proven":False,
            "note":"Two adjacent observed pairs support an offset hypothesis, not a full-world mapping formula."
        },
        "local_raw_capture_sha256":capture_hashes,
        "raw_capture_committed":False,
        "cpu_hook_events_observed":sum(p["cpu_hook_count"] for p in v+w),
        "new_graph_edge_promoted":False,
        "confidence":"two_direction_frame_exact_runtime_state_and_coordinate_proof"
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--village-capture",type=Path,required=True)
    ap.add_argument("--world-capture",type=Path,required=True)
    ap.add_argument("--settled-capture",type=Path,required=True)
    ap.add_argument("--output",type=Path,default=OUT)
    a=ap.parse_args()
    files={"village_to_world":a.village_capture,
           "world_to_village":a.world_capture,
           "settled_arrival":a.settled_capture}
    originals={k:p.read_bytes() for k,p in files.items()}
    hashes={k:hashlib.sha256(b).hexdigest().upper() for k,b in originals.items()}
    decoded={k:json.loads(b) for k,b in originals.items()}
    report=summarize(decoded["village_to_world"],decoded["world_to_village"],
                     decoded["settled_arrival"],hashes)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"village_switch":report["village_to_world"]["switch_frame"],
                      "world_switch":report["world_to_village"]["switch_to_pack_0x50_frame"],
                      "world_exit":report["village_to_world"]["arrival"],
                      "return_settled":report["world_to_village"]["settled_arrival"],
                      "cpu_hooks":report["cpu_hook_events_observed"],
                      "status":"PASS"},ensure_ascii=False))


if __name__=="__main__":
    main()
