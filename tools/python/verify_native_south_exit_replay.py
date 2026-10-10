#!/usr/bin/env python3
"""Fail-closed 1-frame-per-step native exit evidence summarizer.

Reads ONLY isolated hidden BizHawk local replay logs. Does not touch the
emulator, ROM, savestates or game input. Produces metadata, not raw capture.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

SOURCE_CONFIG="cfg_t07_l015_v2"
DEST_CONFIG="cfg_t04_l008_v2"
ROM_SHA="F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"data/maps/transitions/pack2e_exact_south_exit_20261011.json"


def summarize(manifest:dict, traces:list[dict], capture_sha256:str)->dict:
    steps=manifest.get("frames")
    if manifest.get("kind")!="native_exit_runtime_replay" or not isinstance(steps,list):
        raise ValueError("Not a native 1-frame runtime replay")
    if len(steps)<3 or len(steps)!=len(traces):
        raise ValueError("Replay frame rows and individual trace files disagree")
    if manifest.get("origin_state")!="vmtrace_tabidachi_pack2e_interior_20261011":
        raise ValueError("Unexpected interior fixture")
    if manifest.get("current_user_desktop_untouched") is not True:
        raise ValueError("Desktop isolation not verified")
    positions=[]
    hook_counts={}
    previous=None
    for i,(row,trace) in enumerate(zip(steps,traces),start=1):
        if row.get("step")!=i or row.get("after")!=row.get("before")+1:
            raise ValueError(f"Replay step/frame shape mismatch at {i}")
        if previous is not None and row["before"]!=previous:
            raise ValueError(f"Missing/overlapping frame at step {i}")
        previous=row["after"]
        if (trace.get("kind")!="isolated_vm_execution_trace" or
            trace.get("input_sent") is not True or
            trace.get("input_device")!="isolated_snes_gamepad" or
            trace.get("buttons")!="Down" or
            trace.get("player")!=1 or
            trace.get("requested_neutral_frames")!=0 or
            trace.get("requested_input_frames")!=1 or
            trace.get("advanced_frames")!=1 or
            trace.get("dropped_events")!=0 or
            trace.get("hook_errors")):
            raise ValueError(f"Unsafe or incomplete input trace at step {i}")
        before,after=trace.get("before") or {},trace.get("after") or {}
        if (before.get("frame")!=row["before"] or after.get("frame")!=row["after"] or
            before.get("w0305")!=row["p0"] or after.get("w0305")!=row["p1"] or
            after.get("w1573")!=row["x"] or after.get("w157d")!=row["y"]):
            raise ValueError(f"Trace and replay state disagree at step {i}")
        events=trace.get("events")
        if not isinstance(events,list) or len(events)!=row.get("events"):
            raise ValueError(f"Hook count mismatch at step {i}")
        for event in events:
            k=event.get("hook")
            hook_counts[k]=hook_counts.get(k,0)+1
        positions.append(dict(step=i,frame=row["after"],from_pack=row["p0"],
                              pack=row["p1"],x=row["x"],y=row["y"]))
    if positions[0]["from_pack"]!=0x2E or positions[0]["x"]!=9:
        raise ValueError("Unexpected interior start map / X")
    switch=[i for i,p in enumerate(positions) if p["from_pack"]==0x2E and p["pack"]==0x50]
    if len(switch)!=1 or switch[0]!=len(positions)-1:
        raise ValueError("Source->target switch is not unique/final")
    j=switch[0]
    if any(p["pack"]!=0x2E or p["x"]!=9 for p in positions[:j]):
        raise ValueError("Source coordinate/map changed unexpectedly before exit")
    dest=positions[j]
    if [dest["x"],dest["y"]]!=[29,17]:
        raise ValueError("Unexpected native return arrival")
    inside=[p for p in positions[:j] if p["y"]==12]
    outside=[p for p in positions[:j] if p["y"]==13]
    if not inside or not outside or inside[-1]["frame"]>=outside[0]["frame"]:
        raise ValueError("Missing the inside-to-outside boundary observations")
    if positions[0]["y"]!=10:
        raise ValueError("Unexpected entry y-step")
    if any(p["y"] not in (10,11,12,13) for p in positions[:j]):
        raise ValueError("Unexpected route leaves the center corridor")
    if not isinstance(capture_sha256,str) or len(capture_sha256)!=64:
        raise ValueError("Missing immutable local capture digest")
    return {
        "schema_version":1,
        "kind":"verified_frame_exact_native_south_exit",
        "canonical_rom_sha256":ROM_SHA,
        "source":{"config_id":SOURCE_CONFIG,"pack_id_hex":"0x2E",
                  "confirmed_center_exit_cell":{"x":9,"y":12,"width":1,"height":1},
                  "first_outside_cell":{"x":9,"y":13},
                  "last_observed_inside_frame":inside[-1]["frame"],
                  "first_observed_outside_frame":outside[0]["frame"]},
        "destination":{"config_id":DEST_CONFIG,"pack_id_hex":"0x50",
                       "arrival":{"x":29,"y":17}},
        "replay":{"origin_local_savestate":"vmtrace_tabidachi_pack2e_interior_20261011.State",
                  "start_frame":steps[0]["before"],"switch_frame":dest["frame"],
                  "number_of_exact_input_frames":len(positions),
                  "input_device":"isolated_snes_gamepad","buttons":"Down","player":1,
                  "local_raw_capture_sha256":capture_sha256,
                  "local_raw_capture_policy":"not_committed",
                  "observed_positions_at_changes":[
                      {k:p[k] for k in ("frame","pack","x","y")}
                      for idx,p in enumerate(positions)
                      if idx==0 or (p["pack"],p["x"],p["y"])!=
                      (positions[idx-1]["pack"],positions[idx-1]["x"],positions[idx-1]["y"])
                  ],
                  "hook_event_counts":hook_counts,
                  "execution_hook_firing_proven":bool(hook_counts),
                  "native_transition_proven_by_wram":True,
                  "all_traces_without_input_error_or_overflow":True},
        "confidence":"confirmed_runtime_source_cell_and_destination",
        "does_not_prove":[
            "Exit width beyond x=9",
            "CPU execution-hook callbacks (none recorded if counts empty)",
            "Scripted opcode 0x56 firing (this is a native boundary restore)",
            "All possible game story states"
        ],
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--capture",type=Path,required=True)
    p.add_argument("--output",type=Path,default=OUT)
    a=p.parse_args()
    raw=a.capture.read_bytes()
    m=json.loads(raw)
    traces=[]
    for step in m.get("frames",[]):
        if not step.get("file"):raise SystemExit("Replay trace path missing")
        traces.append(json.loads(Path(step["file"]).read_text(encoding="utf-8")))
    report=summarize(m,traces,hashlib.sha256(raw).hexdigest().upper())
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="replay"},ensure_ascii=False))
    print("PROVEN_RUNTIME_FRAME="+str(report["replay"]["switch_frame"]))


if __name__=="__main__":
    main()
