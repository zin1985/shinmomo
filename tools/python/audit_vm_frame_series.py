#!/usr/bin/env python3
"""Verify continuous BizHawk onframeend WRAM series without CPU-hook claims.

No game input, ROM or emulator operations. A sampled map-pack switch is
an observation of WRAM, NOT by itself a source config / VM handler proof.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SAMPLE_KEYS = ("w0305","w035f","w1398","w13b8","ptr98_lo","ptr99_hi",
               "ptr9a_bank","w1573","w157d","w15cf","w15d0")


def _uint8(value, key):
    if not isinstance(value,int) or isinstance(value,bool) or not (0<=value<=255):
        raise ValueError(f"Missing or invalid byte {key}")
    return value


def inspect_series(doc:dict)->dict:
    if doc.get("kind") != "isolated_vm_frame_series" or doc.get("schema_version")!=1:
        raise ValueError("Unsupported frame series schema")
    count=doc.get("requested_frames")
    advanced=doc.get("advanced_frames")
    if (not isinstance(count,int) or isinstance(count,bool) or count<1 or count>120
            or advanced!=count):
        raise ValueError("Unbounded or incomplete frame series")
    if doc.get("sampling_method")!="onframeend_WRAM_no_PC_hook":
        raise ValueError("Sampling is not frame-end WRAM")
    if doc.get("cpu_execution_hook_delivery_proven") is not False:
        raise ValueError("Unsupported CPU execute-hook assertion")
    sent=doc.get("input_sent")
    if type(sent) is not bool:
        raise ValueError("Input provenance is missing")
    if sent:
        import re
        buttons=doc.get("buttons")
        if (doc.get("input_device")!="isolated_snes_gamepad"
            or doc.get("player") not in (1,2,3,4)
            or not isinstance(buttons,str) or
            re.fullmatch(r"(?:A|B|X|Y|L|R|Up|Down|Left|Right|Start|Select)(?:[, ]+(?:A|B|X|Y|L|R|Up|Down|Left|Right|Start|Select))*",buttons) is None):
            raise ValueError("Frame series did not use isolated SNES buttons")
    else:
        if doc.get("input_device")!="none" or doc.get("buttons")!="" or doc.get("player") is not None:
            raise ValueError("Non-neutral frame series provenance mismatch")
    before=doc.get("before")
    after=doc.get("after")
    samples=doc.get("samples")
    if not isinstance(before,dict) or not isinstance(after,dict) or not isinstance(samples,list):
        raise ValueError("Incomplete frame series")
    if len(samples)!=count:
        raise ValueError("Frame series sample count mismatched")
    start=before.get("frame")
    stop=after.get("frame")
    if type(start) is not int or type(stop) is not int or stop-start!=count:
        raise ValueError("Frame series outer boundary mismatch")
    for field in (before,after):
        for key in SAMPLE_KEYS:_uint8(field.get(key),key)
    movements=[]
    switches=[]
    frame_rows=[]
    last=before
    for i,sample in enumerate(samples,1):
        if not isinstance(sample,dict) or sample.get("frame")!=start+i:
            raise ValueError("Missing, duplicate or shifted per-frame WRAM sample")
        for key in SAMPLE_KEYS:
            _uint8(sample.get(key),key)
        if sample.get("label")!="sample":
            raise ValueError("Frame-end sample provenance missing")
        changes={}
        for key in SAMPLE_KEYS:
            if sample[key]!=last[key]:
                changes[key]={"previous":last[key],"current":sample[key]}
        item={"frame":sample["frame"],"pack":sample["w0305"],
              "x":sample["w1573"],"y":sample["w157d"],
              "vm_mode_035f":sample["w035f"],
              "dispatch_1398":sample["w1398"],
              "changes":changes}
        frame_rows.append(item)
        if any(key in changes for key in ("w0305","w1573","w157d")):
            movements.append({key:item[key] for key in ("frame","pack","x","y")})
        if "w0305" in changes:
            switches.append({
                "frame":sample["frame"],
                "before_pack":last["w0305"],"after_pack":sample["w0305"],
                "before_position":{"x":last["w1573"],"y":last["w157d"]},
                "after_position":{"x":sample["w1573"],"y":sample["w157d"]},
                "source_map_configuration_proven":False,
                "vm_handler_execution_proven":False
            })
        last=sample
    if any(last.get(k)!=after.get(k) for k in ("frame",)+SAMPLE_KEYS):
        raise ValueError("Last frame sample and final same-frame snapshot disagree")
    return {
        "schema_version":1,"kind":"audited_isolated_vm_frame_series",
        "initial_frame":start,"final_frame":stop,
        "complete_contiguous_frames":count,
        "input_sent":sent,
        "input_device":doc["input_device"],
        "sampling":"frame_end_WRAM",
        "cpu_execution_hook_proven":False,
        "map_switch_count":len(switches),
        "map_switches":switches,
        "position_or_pack_changes":movements,
        "confirmed_source_map_bindings_added":0,
        "new_graph_edges_added":0,
        "interpretation":"Frame-exact WRAM states; distinguish map-pack switch from post-load settled arrival, never infer CPU opcode or event predicate."
    }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--trace",type=Path,required=True)
    ap.add_argument("--output",type=Path)
    args=ap.parse_args()
    doc=json.loads(args.trace.read_text(encoding="utf-8"))
    report=inspect_series(doc)
    output=args.output or args.trace.with_name(args.trace.stem+"_audit.json")
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("map_switches","position_or_pack_changes")},
                     ensure_ascii=False))
    print("MAP_SWITCHES="+json.dumps(report["map_switches"],ensure_ascii=False))
    print("LOCAL_AUDIT_FILE="+str(output))


if __name__=="__main__":
    main()
