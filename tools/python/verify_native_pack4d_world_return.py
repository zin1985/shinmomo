#!/usr/bin/env python3
"""Fail-closed proof of pack4D south native return, distinct from VM0x56.

Consumes local, bounded SNES controller & neutral frame-end WRAM captures.
Only metadata goes into the repository. Neither CPU hook nor story
predicate is asserted from pack changes.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path
from audit_vm_frame_series import inspect_series

ROOT=Path(__file__).resolve().parents[2]
ROM_SHA="F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"


def validate(input_doc:dict, neutral_doc:dict, bounds:dict, incoming:dict)->dict:
    i=inspect_series(input_doc)
    n=inspect_series(neutral_doc)
    if i["schema_version"]!=2 or n["schema_version"]!=2:
        raise ValueError("Exact native return requires frame-series schema2")
    if not i["input_sent"] or i["input_device"]!="isolated_snes_gamepad" or input_doc["buttons"]!="Down" or input_doc["player"]!=1:
        raise ValueError("Return must use only isolated Down input")
    if n["input_sent"] or i["complete_contiguous_frames"]!=25 or n["complete_contiguous_frames"]!=120:
        raise ValueError("Unexpected input/neutral capture lengths")
    if i["final_frame"]!=n["initial_frame"] or any(
        input_doc["after"][k]!=neutral_doc["before"][k]
        for k in ("frame","w0305","w1573","w157d","w126e","w12b4","w0306")):
        raise ValueError("Input and neutral captured states do not join")
    if (bounds.get("config_id")!="cfg_t04_l006_v2" or bounds.get("pack_id_hex")!="0x4D" or
        bounds.get("min_y")!="1" or bounds.get("max_y")!="37" or
        bounds.get("min_x")!="1" or bounds.get("max_x")!="46" or
        bounds.get("confidence")!="confirmed_static_opcode52_bounds"):
        raise ValueError("Static native bounds do not match the runtime map")
    if (incoming.get("kind")!="verified_spatial_event_map_transition" or
        incoming.get("destination_config_id")!="cfg_t04_l006_v2" or
        incoming.get("observed_source_config_id")!="cfg_t01_l001_v1" or
        incoming.get("observed_source_pack")!=76 or
        incoming.get("destination_pack")!=77 or
        incoming.get("settled_arrival")!={"x":17,"y":37}):
        raise ValueError("Independent world-to-pack4D source context missing")
    a=input_doc["before"]
    if (a["frame"]!=663378 or a["w0305"]!=77 or (a["w1573"],a["w157d"])!=(17,37)):
        raise ValueError("Unexpected native return source fixture")
    samples=input_doc["samples"]
    outside=[x for x in samples if x["w0305"]==77 and (x["w1573"],x["w157d"])==(17,38)]
    if not outside or outside[0]["frame"]!=663382:
        raise ValueError("Exact native out-of-bounds crossing was not observed")
    switches=[x for x in samples if x["w0305"]!=77]
    if not switches or switches[0]["frame"]!=663387:
        raise ValueError("Exact world pack return frame was not reproduced")
    if any(x["w0305"]!=77 for x in samples if x["frame"]<663387):
        raise ValueError("Source pack changed before required frame")
    if any(x["w0305"]!=76 or (x["w1573"],x["w157d"])!=(52,233) for x in switches):
        raise ValueError("World return position not stable after switch in input capture")
    if any(x["w0305"]!=76 or (x["w1573"],x["w157d"])!=(52,233) for x in neutral_doc["samples"]):
        raise ValueError("World destination was not stable in 120 neutral frames")
    convergence=next((s["frame"] for s in neutral_doc["samples"]
                      if s["w126e"]==76 and s["w12b4"]==76),None)
    if convergence!=663414:
        raise ValueError("Raw VM context selector convergence not reproduced")
    return {
        "schema_version":1,
        "kind":"verified_native_boundary_return_new_edge",
        "canonical_rom_sha256":ROM_SHA,
        "source_config_id":"cfg_t04_l006_v2",
        "source_pack":"0x4D",
        "confirmed_source_inside_cell":{"x":17,"y":37},
        "first_outside_cell":{"x":17,"y":38},
        "first_outside_frame":663382,
        "native_bounds_opcode_address":bounds["bounds_opcode_addr"],
        "native_bounds":{"x_min":1,"x_max":46,"y_min":1,"y_max":37},
        "native_bounds_confidence":"confirmed_static_opcode52_bounds",
        "destination_config_id":"cfg_t01_l001_v1",
        "destination_pack":"0x4C",
        "settled_arrival":{"x":52,"y":233},
        "switch_frame":663387,
        "selector_convergence_frame":convergence,
        "stable_observed_until_frame":neutral_doc["after"]["frame"],
        "input_frames":25,
        "neutral_frames":120,
        "source_context_from_independent_world_entry_proof":"data/maps/transitions/world_52_233_entry_verified_20261011.json",
        "return_mechanism":"native_bounds_saved_map_restore_runtime_consistent",
        "CPU_handler_PC_observed":False,
        "VM_opcode_56_executed_proven":False,
        "full_south_exit_width_proven":False,
        "all_story_states_navigable_proven":False,
        "raw_w0306_converged_to_destination":neutral_doc["after"]["w0306"]==76,
        "new_edge_runtime_source_unique":True,
        "confidence":"confirmed_runtime_2way_position",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--neutral",type=Path,required=True)
    parser.add_argument("--output",type=Path,default=ROOT/"data/maps/transitions/pack4d_south_native_return_20261011.json")
    args=parser.parse_args()
    inbytes=args.input.read_bytes()
    nbytes=args.neutral.read_bytes()
    with (ROOT/"data/maps/transitions/map_native_bounds_catalog.csv").open(encoding="utf-8-sig",newline="") as file:
        rows=[x for x in csv.DictReader(file) if x.get("pack_id_hex")=="0x4D"]
    if len(rows)!=1:raise ValueError("Native bounds row not unique")
    incoming=json.loads((ROOT/"data/maps/transitions/world_52_233_entry_verified_20261011.json").read_text(encoding="utf-8"))
    proof=validate(json.loads(inbytes),json.loads(nbytes),rows[0],incoming)
    proof["local_raw_capture_sha256"]={
        "input":hashlib.sha256(inbytes).hexdigest().upper(),
        "neutral":hashlib.sha256(nbytes).hexdigest().upper()
    }
    proof["raw_traces_committed"]=False
    args.output.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"source":"0x4D x17 y37","first_outside_frame":proof["first_outside_frame"],
                      "switch_frame":proof["switch_frame"],"destination":"0x4C x52 y233",
                      "context_convergence_frame":proof["selector_convergence_frame"],
                      "status":"PASS"}))


if __name__=="__main__":main()
