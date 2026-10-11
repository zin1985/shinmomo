#!/usr/bin/env python3
"""Determine map-switch and settled-arrival phases from contiguous WRAM captures.

This is a frame-end observation, NOT an assertion that an SNES opcode
callback was delivered. Results are local by default.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from audit_vm_frame_series import inspect_series

WATCHED = (
    "w0305", "w035f", "w1398", "w13b8",
    "ptr98_lo", "ptr99_hi", "ptr9a_bank",
    "w1573", "w157d", "w15cf", "w15d0",
)

def state(row):
    return {k:row[k] for k in WATCHED}

def collect(input_trace, settle_trace, *, stability_frames=8, extra_neutral_trace=None):
    first=inspect_series(input_trace)
    second=inspect_series(settle_trace)
    if first["schema_version"]!=second["schema_version"]:
        raise ValueError("Input/settle frame-series schema differ")
    keys=WATCHED + (("w0306","w126e","w12b4","w12b5")
                    if first["schema_version"]==2 else ())
    if (not first["input_sent"] or second["input_sent"] or
        first["input_device"]!="isolated_snes_gamepad" or
        second["input_device"]!="none"):
        raise ValueError("Expected bounded isolated controller then neutral settling")
    if first["final_frame"]!=second["initial_frame"]:
        raise ValueError("Input and settling capture frames are not contiguous")
    if any(input_trace["after"][k]!=settle_trace["before"][k] for k in keys):
        raise ValueError("State changed between input and neutral captures")
    if not isinstance(stability_frames,int) or not 2<=stability_frames<=120:
        raise ValueError("Invalid stable-window length")
    third=None
    if extra_neutral_trace is not None:
        third=inspect_series(extra_neutral_trace)
        if (third["schema_version"]!=first["schema_version"] or
            third["input_sent"] or third["input_device"]!="none" or
            third["initial_frame"]!=second["final_frame"] or
            any(settle_trace["after"][k]!=extra_neutral_trace["before"][k]
                for k in ("frame",)+keys)):
            raise ValueError("Additional neutral frame capture is not exactly contiguous")
    before=input_trace["before"]
    series=input_trace["samples"]+settle_trace["samples"]+(
        extra_neutral_trace["samples"] if third is not None else [])
    prev=before
    pack_switches=[]
    state_changes=[]
    for row in series:
        changed={
            k:{"before":prev[k],"after":row[k]}
            for k in keys if prev[k]!=row[k]
        }
        if changed:
            state_changes.append({"frame":row["frame"],"changes":changed})
        if "w0305" in changed:
            pack_switches.append({
                "frame":row["frame"],
                "pack_before":prev["w0305"],"pack_after":row["w0305"],
                "xy_at_switch":{"x":row["w1573"],"y":row["w157d"]},
                "state_before":{k:prev[k] for k in keys},"state_at_switch":{k:row[k] for k in keys},
                "changed_fields":changed,
            })
        prev=row
    if len(pack_switches)!=1:
        raise ValueError("Require exactly one pack switch in this event experiment")
    switch=pack_switches[0]
    final_pack=switch["pack_after"]
    post=[r for r in series if r["frame"]>=switch["frame"]]
    if any(r["w0305"]!=final_pack for r in post):
        raise ValueError("Destination pack did not remain stable")
    # Candidate settled coordinate must differ from at-switch carryover
    # coordinate, and then remain identical for the rest of observed frames.
    switch_xy=(switch["xy_at_switch"]["x"],switch["xy_at_switch"]["y"])
    candidate=None
    for i,row in enumerate(post):
        xy=(row["w1573"],row["w157d"])
        if xy==switch_xy:
            continue
        remaining=post[i:]
        if len(remaining)<stability_frames:
            continue
        if all((r["w1573"],r["w157d"])==xy for r in remaining):
            candidate=row
            break
    if candidate is None:
        raise ValueError("Could not prove a new settled coordinate distinct from carryover")
    if candidate["frame"]<=switch["frame"]:
        raise ValueError("Destination settling must follow pack switch")
    frame_deltas=[x for x in state_changes
                  if switch["frame"]-2<=x["frame"]<=candidate["frame"]+2]
    return {
        "schema_version":1,
        "kind":"runtime_pack_switch_and_settled_arrival_phases",
        "observation_method":"contiguous_per_frame_WRAM",
        "source_pack":switch["pack_before"],
        "destination_pack":final_pack,
        "pack_switch_frame":switch["frame"],
        "input_window":{"from_frame":first["initial_frame"],
                        "to_frame":first["final_frame"]},
        "neutral_window":{"from_frame":second["initial_frame"],
                          "to_frame":(third["final_frame"] if third else second["final_frame"])},
        "neutral_capture_chunk_count":2 if third else 1,
        "extended_neutral_capture_verified":third is not None,
        "raw_script_pointer_at_switch":{
            "bank":switch["state_at_switch"]["ptr9a_bank"],
            "high":switch["state_at_switch"]["ptr99_hi"],
            "low":switch["state_at_switch"]["ptr98_lo"],
        },
        "event_entry_byte_at_switch":switch["state_at_switch"]["w13b8"],
        "saved_pack_bytes_at_switch":{
            "w15cf":switch["state_at_switch"]["w15cf"],
            "w15d0":switch["state_at_switch"]["w15d0"],
        },
        "map_state_changes_at_switch":switch["changed_fields"],
        "frame_series_schema_version":first["schema_version"],
        "selector_raw_at_switch":({k:switch["state_at_switch"][k]
                                   for k in ("w0306","w126e","w12b4","w12b5")}
                                  if first["schema_version"]==2 else None),
        "selector_changes_near_switch":[
            {"frame":x["frame"],"changes":{k:v for k,v in x["changes"].items()
                                             if k in ("w0306","w126e","w12b4","w12b5")}}
            for x in state_changes
            if any(k in x["changes"] for k in ("w0306","w126e","w12b4","w12b5"))
        ],
        "at_switch_coordinate":switch["xy_at_switch"],
        "first_settled_arrival_frame":candidate["frame"],
        "settled_arrival":{"x":candidate["w1573"],"y":candidate["w157d"]},
        "switch_to_settle_delay_frames":candidate["frame"]-switch["frame"],
        "stable_observed_frames":len([r for r in post if r["frame"]>=candidate["frame"]]),
        "surrounding_state_changes":frame_deltas,
        "exact_cpu_handler_execution_proven":False,
        "VM_opcode_53_or_56_executed_proven":False,
        "source_event_caller_proven":False,
        "new_source_map_binding_promoted":False,
        "limitations":"WRAM script pointer and event byte are observations; they do not prove exact executed VM opcode PC or all narrative predicates."
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-trace",type=Path,required=True)
    ap.add_argument("--settle-trace",type=Path,required=True)
    ap.add_argument("--extra-neutral-trace",type=Path)
    ap.add_argument("--stable-frames",type=int,default=8)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    raw_a=args.input_trace.read_bytes()
    raw_b=args.settle_trace.read_bytes()
    raw_extra=(args.extra_neutral_trace.read_bytes()
               if args.extra_neutral_trace else None)
    report=collect(json.loads(raw_a),json.loads(raw_b),
                   stability_frames=args.stable_frames,
                   extra_neutral_trace=(json.loads(raw_extra)
                                        if raw_extra is not None else None))
    report["local_capture_sha256"]={
        "input":hashlib.sha256(raw_a).hexdigest().upper(),
        "settle":hashlib.sha256(raw_b).hexdigest().upper()
    }
    if raw_extra is not None:
        report["local_capture_sha256"]["extra_neutral"]=hashlib.sha256(raw_extra).hexdigest().upper()
    output=args.output or args.input_trace.with_name(
        args.input_trace.stem+"_transition_phases.json")
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "pack_switch_frame":report["pack_switch_frame"],
        "source_pack":report["source_pack"],
        "destination_pack":report["destination_pack"],
        "settled_frame":report["first_settled_arrival_frame"],
        "settled_xy":report["settled_arrival"],
        "raw_script_pointer":report["raw_script_pointer_at_switch"],
        "saved_pack_bytes":report["saved_pack_bytes_at_switch"],
        "cpu_handler_proven":False,
        "local_audit":str(output)},ensure_ascii=False))

if __name__=="__main__":
    main()
