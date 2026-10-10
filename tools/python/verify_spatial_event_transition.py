#!/usr/bin/env python3
"""Audit real SNES hotspot contact, map switch, selectors and settled arrival.

Retains a critical distinction:
  the map path/coordinate is runtime verified;
  the catalog's static VM opcode PC is NOT CPU-execution-hook verified.

This operates only on LOCAL frame-series trace files; never writes to
ROM, VRAM, savestates, emulator or player input.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from audit_transition_phases import collect

ROOT=Path(__file__).resolve().parents[2]
CATALOG=ROOT/"data/maps/transitions/source_transition_hotspots.csv"


def prove(input_doc,settle_doc,hotspot,candidate_edge,*,expected_source_pack:int,
          expected_destination_pack:int,stable_frames:int=8):
    result=collect(input_doc,settle_doc,stability_frames=stable_frames)
    if input_doc.get("schema_version")!=2 or settle_doc.get("schema_version")!=2:
        raise ValueError("Require actual v2 frame captures including selector state")
    if result["source_pack"]!=expected_source_pack or result["destination_pack"]!=expected_destination_pack:
        raise ValueError("Unexpected source or destination pack")
    if (result["source_pack"]==result["destination_pack"] or
        result["first_settled_arrival_frame"]<=result["pack_switch_frame"]):
        raise ValueError("No independently observed transition and landing")
    if any(not hotspot.get(k) for k in
           ("hotspot_id","source_config_id","destination_config_id","trigger_addr")):
        raise ValueError("Missing spatial hotspot provenance")
    if any(hotspot.get(k)!=candidate_edge.get(k) for k in
           ("source_config_id","destination_config_id","trigger_addr")):
        raise ValueError("Hotspot and unique graph edge disagree")
    if candidate_edge.get("confidence") not in ("strong_candidate","confirmed_runtime_and_static"):
        raise ValueError("Unsupported existing graph confidence")
    sx=int(hotspot["source_grid_x"]);sy=int(hotspot["source_grid_y"])
    sw=int(hotspot["source_width"]);sh=int(hotspot["source_height"])
    if not (1<=sw<=8 and 1<=sh<=8):
        raise ValueError("Invalid bounded source hotspot region")
    dx=int(hotspot["destination_x"]);dy=int(hotspot["destination_y"])
    if (result["settled_arrival"]!={"x":dx,"y":dy} or
        candidate_edge.get("destination_x")!=dx or candidate_edge.get("destination_y")!=dy):
        raise ValueError("Runtime arrival differs from static destination or Viewer")
    before=input_doc["before"]
    region_path=[before]+input_doc["samples"]
    contact=[p["frame"] for p in region_path
             if p["w0305"]==expected_source_pack and
             sx<=p["w1573"]<sx+sw and sy<=p["w157d"]<sy+sh]
    if not contact or contact[0]>=result["pack_switch_frame"]:
        raise ValueError("Runtime source never entered the exact spatial hotspot before transition")
    allrows=input_doc["samples"]+settle_doc["samples"]
    state_at_switch=next((row for row in allrows if row["frame"]==result["pack_switch_frame"]),None)
    if state_at_switch is None:
        raise ValueError("Missing source-to-target switch frame")
    def first_frame(predicate):
        matches=[row["frame"] for row in allrows if row["frame"]>=result["pack_switch_frame"] and predicate(row)]
        return matches[0] if matches else None
    selector_pair=first_frame(lambda r:r["w126e"]==expected_destination_pack
                                       and r["w12b4"]==expected_destination_pack)
    if selector_pair is None or selector_pair>result["first_settled_arrival_frame"]:
        raise ValueError("Destination VM selectors did not converge by coordinate settlement")
    current_data_pack=first_frame(lambda r:r["w0306"]==expected_destination_pack)
    if current_data_pack is not None and current_data_pack>result["first_settled_arrival_frame"]:
        # Could change later. Leave as later observation, not a settled requirement.
        pass
    return {
        "schema_version":1,
        "kind":"verified_spatial_event_map_transition",
        "source_hotspot_id":hotspot["hotspot_id"],
        "existing_viewer_transition_id":candidate_edge["transition_id"],
        "existing_static_opcode_address":hotspot["trigger_addr"],
        "static_opcode_cpu_execution_proven":False,
        "runtime_map_movement_proven":True,
        "observed_source_config_id":hotspot["source_config_id"],
        "observed_source_pack":expected_source_pack,
        "confirmed_source_region":{"x":sx,"y":sy,"width":sw,"height":sh},
        "first_observed_source_contact_frame":contact[0],
        "last_observed_source_contact_frame":contact[-1],
        "pack_switch_frame":result["pack_switch_frame"],
        "raw_vm_script_pointer_at_switch":result["raw_script_pointer_at_switch"],
        "raw_event_entry_at_switch":result["event_entry_byte_at_switch"],
        "saved_pack_bytes_at_switch":result["saved_pack_bytes_at_switch"],
        "destination_config_id":hotspot["destination_config_id"],
        "destination_pack":expected_destination_pack,
        "first_selector_pair_convergence_frame":selector_pair,
        "first_0306_target_byte_frame":current_data_pack,
        "first_settled_arrival_frame":result["first_settled_arrival_frame"],
        "settled_arrival":{"x":dx,"y":dy},
        "switch_to_settle_delay_frames":result["switch_to_settle_delay_frames"],
        "existing_graph_confidence_unchanged":candidate_edge["confidence"],
        "new_graph_edges_promoted":0,
        "unproven":["CPU opcode callback PC","all story predicates","other hotspot cells",
                    "full map reachability","destination map label"],
    }


def read_catalog(path,id):
    with path.open(encoding="utf-8-sig",newline="") as fh:
        matches=[row for row in csv.DictReader(fh) if row.get("hotspot_id")==id]
    if len(matches)!=1:raise ValueError("Hotspot ID must match exactly one catalog row")
    return matches[0]


def unique_edge(world,hotspot):
    rows=[e for e in world["transition_edges"] if
          e.get("source_config_id")==hotspot["source_config_id"] and
          e.get("destination_config_id")==hotspot["destination_config_id"] and
          e.get("trigger_addr")==hotspot["trigger_addr"]]
    if len(rows)!=1:raise ValueError("Runtime proof cannot identify exactly one existing edge")
    return rows[0]


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--input-trace",type=Path,required=True)
    a.add_argument("--settle-trace",type=Path,required=True)
    a.add_argument("--hotspot-id",required=True)
    a.add_argument("--source-pack",type=lambda s:int(s,0),required=True)
    a.add_argument("--destination-pack",type=lambda s:int(s,0),required=True)
    a.add_argument("--output",type=Path,required=True)
    a.add_argument("--catalog",type=Path,default=CATALOG)
    a.add_argument("--viewer-json",type=Path,default=ROOT/"viewer/data/world.json")
    args=a.parse_args()
    b1=args.input_trace.read_bytes();b2=args.settle_trace.read_bytes()
    spot=read_catalog(args.catalog,args.hotspot_id)
    world=json.loads(args.viewer_json.read_text(encoding="utf-8"))
    edge=unique_edge(world,spot)
    proof=prove(json.loads(b1),json.loads(b2),spot,edge,
                expected_source_pack=args.source_pack,
                expected_destination_pack=args.destination_pack)
    proof["local_raw_trace_sha256"]={
        "input":hashlib.sha256(b1).hexdigest().upper(),
        "neutral":hashlib.sha256(b2).hexdigest().upper()
    }
    proof["raw_capture_committed"]=False
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:proof[k] for k in (
        "source_hotspot_id","existing_viewer_transition_id","pack_switch_frame",
        "first_selector_pair_convergence_frame","first_settled_arrival_frame",
        "settled_arrival","static_opcode_cpu_execution_proven")},ensure_ascii=False))


if __name__=="__main__":
    main()
