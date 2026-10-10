#!/usr/bin/env python3
"""Reconcile four *local* single-command frame series against prior slow replay.

Only summary/evidence SHA-256 goes to Git. No ROM/screenshot/SaveRAM/savestate.
"""
from __future__ import annotations

import argparse,hashlib,json
from pathlib import Path
from audit_vm_frame_series import inspect_series

ROOT=Path(__file__).resolve().parents[2]
OUTPUT=ROOT/"data/maps/transitions/tabidachi_frame_series_replay_20261011.json"


def validate_series(sources):
    required=("interior_exit","village_exit","world_entry","world_settle")
    if set(sources)!=set(required):
        raise ValueError("Need exactly interior_exit/village_exit/world_entry/world_settle captures")
    reports={k:inspect_series(v) for k,v in sources.items()}
    expected={
        "interior_exit":(661523,661546,23,0x2E,0x50,(29,17)),
        "village_exit":(662166,662186,20,0x50,0x4C,(55,237)),
        "world_entry":(663046,663064,18,0x4C,0x50,(55,237)),
        "world_settle":(663064,663184,120,0x50,0x50,(29,55)),
    }
    for name,(first,last,count,src_pack,dst_pack,target_xy) in expected.items():
        report=reports[name]
        raw=sources[name]
        if (report["initial_frame"]!=first or report["final_frame"]!=last or
            report["complete_contiguous_frames"]!=count or
            raw["before"]["w0305"]!=src_pack or
            raw["after"]["w0305"]!=dst_pack or
            (raw["after"]["w1573"],raw["after"]["w157d"])!=target_xy):
            raise ValueError(f"Unexpected {name} frame range, pack or position")
        if report["cpu_execution_hook_proven"] or report["new_graph_edges_added"]:
            raise ValueError("An unverified CPU opcode or source binding was promoted")
    for key in required[:3]:
        if reports[key]["map_switch_count"]!=1 or reports[key]["map_switches"][0]["frame"]!=expected[key][1]:
            raise ValueError(f"Ambiguous/missing single map switch: {key}")
        if reports[key]["input_device"]!="isolated_snes_gamepad" or not reports[key]["input_sent"]:
            raise ValueError(f"Controller not grounded on {key}")
    if reports["world_settle"]["input_sent"] or reports["world_settle"]["map_switch_count"]!=0:
        raise ValueError("World-to-village arrival has unsupported input or pack switch")
    world_settle=sources["world_settle"]
    first_arrival=[row for row in world_settle["samples"] if
                   row["w1573"]==29 and row["w157d"]==55]
    if not first_arrival:
        raise ValueError("No stable post-transition arrival")
    arrive=first_arrival[0]
    if arrive["frame"]!=663169:
        raise ValueError("Unexpected first settled village coordinate")
    for row in world_settle["samples"]:
        if row["frame"]>=arrive["frame"] and (
            row["w0305"]!=0x50 or row["w1573"]!=29 or row["w157d"]!=55):
            raise ValueError("After-arrival coordinates did not remain stable in observed window")
    # Frame-end WRAM is frame-complete but CPU opcode identity is not available.
    return {
        "schema_version":1,
        "kind":"verified_single_command_frame_exact_map_transitions",
        "new_runtime_source_edges":0,
        "canonical_project_progress_unchanged_percent":51.4,
        "sampling_method":"isolated_hidden_BizHawk_event.onframeend",
        "independent_cpu_hook_delivery_proven":False,
        "corroboration":"Previous 2026-10-11 individually requested 1-frame logs agree for village/interior/world switch frames.",
        "observed":{
            "interior_pack2e_to_village_pack50":{"start_frame":661523,"switch_frame":661546,
                "exit_last_outside_xy":[9,13],"first_destination_xy":[29,17],
                "frame_count":23},
            "village_pack50_to_world_pack4c":{"start_frame":662166,"switch_frame":662186,
                "exit_last_outside_xy":[29,56],"first_destination_xy":[55,237],
                "frame_count":20},
            "world_pack4c_to_village_pack50":{"start_frame":663046,"switch_frame":663064,
                "world_entry_xy":[55,237],"switch_time_xy":[55,237],
                "first_settled_arrival_frame":663169,"settled_arrival_xy":[29,55],
                "switch_to_settled_coordinate_delay_frames":105,
                "entry_capture_frames":18,"neutral_settle_capture_frames":120}
        },
        "source_configuration_proven_independently":True,
        "exact_CPU_VM_opcode_execution_proven":False,
        "full_exit_width_proven":False,
        "all_future_story_states_covered":False,
    }


def main():
    p=argparse.ArgumentParser()
    for name in ("interior_exit","village_exit","world_entry","world_settle"):
        p.add_argument("--"+name.replace("_","-"),type=Path,required=True)
    p.add_argument("--output",type=Path,default=OUTPUT)
    args=p.parse_args()
    files={k:getattr(args,k) for k in ("interior_exit","village_exit","world_entry","world_settle")}
    raws={k:v.read_bytes() for k,v in files.items()}
    reports=validate_series({k:json.loads(v) for k,v in raws.items()})
    reports["local_trace_sha256"]={k:hashlib.sha256(b).hexdigest().upper() for k,b in raws.items()}
    reports["raw_captures_committed"]=False
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(reports,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"kind":reports["kind"],"frame_switches":[661546,662186,663064],
                      "settled_frame":663169,"local_only":True,"status":"PASS"},ensure_ascii=False))


if __name__=="__main__":
    main()
