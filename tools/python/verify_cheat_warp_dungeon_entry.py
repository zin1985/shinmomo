#!/usr/bin/env python3
"""Validate an actual dungeon event fired after a clearly disclosed coordinate cheat.

The ROM map trigger is executed naturally *after* warp; normal world walkability
and the VM opcode execution PC remain unproven. No ROM/screens/states get committed.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from audit_transition_phases import collect
ROOT=Path(__file__).resolve().parents[2]
DUNGEON_EDGE="catalog_transition_0750"
SCREEN_SHA="403BE0D1A45A98A513EA034F4CF7E501DE97DCD7F5A84254CF629D292EEE3825"


def verify(input_doc,neutral_doc,edge):
    report=collect(input_doc,neutral_doc,stability_frames=8)
    if input_doc.get("schema_version")!=2 or neutral_doc.get("schema_version")!=2:
        raise ValueError("Strict selector-aware v2 frames required")
    if (not input_doc.get("input_sent") or input_doc.get("input_device")!="isolated_snes_gamepad"
        or input_doc.get("buttons")!="Up" or input_doc.get("player")!=1
        or input_doc.get("requested_frames")!=30 or neutral_doc.get("requested_frames")!=120):
        raise ValueError("Input must be bounded real SNES Up and neutral frames")
    if (edge.get("transition_id")!=DUNGEON_EDGE or
        edge.get("source_config_id")!="cfg_t01_l001_v1" or
        edge.get("destination_config_id")!="cfg_t08_l092_v2" or
        edge.get("trigger_addr")!="CC:0B7F" or
        edge.get("destination_pack")!="0x91" or
        edge.get("confidence")!="strong_candidate"):
        raise ValueError("Existing ROM candidate unexpectedly differs; no promotion")
    target_xy=(edge.get("destination_x"),edge.get("destination_y"))
    if target_xy not in ((None,None),(71,59)):
        raise ValueError("Unexpected prior destination coordinates")
    if target_xy==(71,59) and (
            edge.get("destination_coordinate_origin")!="frame_exact_destination_after_explicit_analysis_warp" or
            not edge.get("runtime_cheat_entry_proof",{}).get("source_position_supplied_by_analysis_cheat")):
        raise ValueError("Previously resolved destination lacks honest cheat provenance")
    hs=edge.get("source_hotspot_binding") or {}
    if any(hs.get(k)!=v for k,v in {
        "source_grid_x":47,"source_grid_y":199,
        "source_width":2,"source_height":1
    }.items()):
        raise ValueError("World source hotspot mismatch")
    before=input_doc["before"]
    if (before.get("w0305"),before.get("w1573"),before.get("w157d"))!=(76,47,200):
        raise ValueError("Cheat start must be the exact world cell x47/y200")
    contact=[row["frame"] for row in input_doc["samples"] if
             row["w0305"]==76 and row["w1573"] in (47,48) and row["w157d"]==199]
    if not contact or contact[0]!=663064:
        raise ValueError("Unmodified game input did not enter the source hotspot")
    if (report["source_pack"],report["destination_pack"],report["pack_switch_frame"])!=(76,145,663079):
        raise ValueError("Wrong pack switch; dungeon event unproven")
    if (report["first_settled_arrival_frame"],report["settled_arrival"])!=(663203,{"x":71,"y":59}):
        raise ValueError("Incorrect stable dungeon landing")
    selector_candidates=[row["frame"] for row in
        (input_doc["samples"]+neutral_doc["samples"]) if
        row["frame"]>=663079 and row["w126e"]==145 and row["w12b4"]==145]
    if not selector_candidates or selector_candidates[0]!=663116:
        raise ValueError("Dungeon selectors did not converge at measured frame")
    if any(row["w0305"]!=145 for row in neutral_doc["samples"]):
        raise ValueError("Dungeon pack was not stable throughout 120 settling frames")
    return {
      "schema_version":1,
      "kind":"cheat_positioned_runtime_dungeon_entrance",
      "source_setup_type":"explicit_analysis_cheat_world_position",
      "source_cheat_wram_addresses":["0x1573","0x157D"],
      "source_cheat_only_before_input":True,
      "source_normal_world_walk_route_proven":False,
      "hien_enabled_state":"analysis_world_lv60_hien_20261011",
      "hien_destination_flags_unlocked":True,
      "hien_spell_menu_destinations_observed":False,
      "hien_spell_actually_cast_for_this_transition":False,
      "cheat_world_xy":[47,200],
      "source_region_contact_cell":[47,199],
      "source_region_contact_frame":contact[0],
      "runtime_source_config_id":"cfg_t01_l001_v1",
      "original_edge_id":DUNGEON_EDGE,
      "rom_static_vm_candidate_address":"CC:0B7F",
      "rom_static_cpu_opcode_execution_proven":False,
      "runtime_event_triggered_by_gamepad":True,
      "map_pack_switch_frame":663079,
      "map_pack_before":"0x4C","map_pack_after":"0x91",
      "selector_convergence_frame":663116,
      "destination_config_id":"cfg_t08_l092_v2",
      "destination_pack":"0x91",
      "destination_xy":{"x":71,"y":59},
      "first_settled_coordinate_frame":663203,
      "screenshot_later_local_frame":663332,
      "screenshot_sha256":SCREEN_SHA,
      "screenshot_onscreen_title":"おむすびころりん",
      "screenshot_raw_committed":False,
      "screenshot_identity_scope":"runtime destination pack0x91 only, not every tileset08/layout92 alias",
      "destination_onscreen_rendered":True,
      "static_graph_confidence_unchanged":True,
      "all_story_phases_accessible_proven":False,
      "new_graph_edges":0,
      "next_interior_floor_transition_verified":False,
      "cave_current_state_navigation_generalized":False
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-trace",type=Path,required=True)
    p.add_argument("--settle-trace",type=Path,required=True)
    p.add_argument("--output",type=Path,default=ROOT/"data/maps/transitions/omusubi_kororin_cheat_entry_verified_20261011.json")
    args=p.parse_args()
    a=args.input_trace.read_bytes()
    b=args.settle_trace.read_bytes()
    world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
    matching=[e for e in world["transition_edges"] if e.get("transition_id")==DUNGEON_EDGE]
    if len(matching)!=1:raise ValueError("Static edge not unique")
    proof=verify(json.loads(a),json.loads(b),matching[0])
    proof["local_raw_capture_sha256"]={"input":hashlib.sha256(a).hexdigest().upper(),
                                       "settle":hashlib.sha256(b).hexdigest().upper()}
    args.output.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"source":"cheated world 47,200 -> normal entry 47,199",
                      "destination":"pack91 x71,y59",
                      "switch":663079,"settled":663203,"label":"おむすびころりん",
                      "static_pc_proven":False,"status":"PASS"},ensure_ascii=False))
if __name__=="__main__":main()
