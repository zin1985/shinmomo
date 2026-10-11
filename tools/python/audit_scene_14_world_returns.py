#!/usr/bin/env python3
"""Audit 20 reverse controls from local scene savestates, 14 confirmed returns.

The world->scene save was originally cheat-positioned before ordinary
gamepad entry. Reverse trials use NO WRAM coordinate writes; map
switches are actual controller-triggered game events. Each individual
frame capture is matched by SHA256 and checked for continuity.
"""
from __future__ import annotations
from collections import defaultdict
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_vm_frame_series import inspect_series,BASE_SAMPLE_KEYS,SELECTOR_SAMPLE_KEYS
ROOT=Path(__file__).resolve().parents[2]
LOCAL=Path(r"C:\Users\zin\AppData\Local\shinmomo-bg-lab")
LEDGER=ROOT/"data/maps/transitions/world_37_gamepad_entrances_after_cheat_20261011.json"
OUT=ROOT/"data/maps/transitions/world_14_reverse_returns_after_cheat_arrivals_20261011.json"
KEYS=("frame",)+BASE_SAMPLE_KEYS+SELECTOR_SAMPLE_KEYS

def analyze(local=LOCAL):
    old=json.loads(LEDGER.read_text(encoding='utf-8'))
    ledger={r["transition_id"]:r for r in old["entries"]}
    sources=[
        local/"research/reverse_scene_batch_0_3_Down_20261011.json",
        local/"research/reverse_scene_batch_3_8_Down_20261011.json",
        local/"research/reverse_scene_batch_11_9_Down_20261011.json",
    ]
    records=[]
    for path in sources:
        doc=json.loads(path.read_text(encoding="utf-8-sig"))
        if (doc.get("schema_version")!=1 or
            doc.get("kind")!="protected_original_scene_arrival_controller_exit_trials" or
            doc.get("source_original_world_entry_cheat_positioned") is not True or
            doc.get("actual_reverse_test_no_xy_wram_edits") is not True or
            doc.get("untouched_original_emulator_restored") is not True):
            raise ValueError(f"Unprotected return research batch {path}")
        records.extend(doc["results"])
    if len(records)!=20 or len({x['source_map_pack'] for x in records})!=20:
        raise ValueError("Expected exactly 20 unique pack return probes")
    needed={h for item in records for h in item["raw_trace_hashes"]}
    index={}
    for path in (local/"captures").glob("vmframes_*.json"):
        digest=hashlib.sha256(path.read_bytes()).hexdigest().upper()
        if digest in needed:
            if digest in index:raise ValueError("Ambiguous hash-matched capture")
            index[digest]=path
    if set(index)!=needed:
        raise ValueError("Missing local frame-end captures "+str(sorted(needed-set(index))[:3]))
    world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
    worldcfgs={m["config_id"] for m in world["maps"]}
    results=[];negative=[]
    for item in records:
        inp=ledger.get(item["source_world_transition_id"])
        if (not inp or inp["destination_pack"]!=item["source_map_pack"] or
            inp["destination_config_id"]!=item["source_config_id"] or
            [inp["settled_arrival_xy"][k] for k in ("x","y")]!=item["source_real_arrival_xy"] or
            item["source_config_id"] not in worldcfgs or
            item["actual_test_controller"]!="Down" or
            item["input_frames"]!=72 or
            item["original_world_entrance_cheat_positioned"] is not True):
            raise ValueError("Return test source not independently aligned with entrance")
        captures=[]
        for d in item["raw_trace_hashes"]:
            obj=json.loads(index[d].read_text(encoding="utf-8"))
            inspect_series(obj)
            if obj.get("schema_version")!=2:raise ValueError("Need full frame-end series")
            captures.append(obj)
        if len(captures) not in (3,4):raise ValueError("Unexpected number of frame captures")
        prep,controller,neutral1=captures[:3]
        if (prep.get("input_sent") or prep.get("requested_frames")!=12 or
            controller.get("input_sent") is not True or
            controller.get("buttons")!="Down" or
            controller.get("player")!=1 or
            controller.get("input_device")!="isolated_snes_gamepad" or
            controller.get("requested_frames")!=72 or
            neutral1.get("input_sent") or neutral1.get("requested_frames")!=120):
            raise ValueError("Cannot validate controller-only scene return capture")
        source_pack=int(inp["destination_pack"],16)
        if ((prep["before"]["w0305"],prep["before"]["w1573"],prep["before"]["w157d"])!=
            (source_pack,*item["source_real_arrival_xy"]) or
            prep["after"]["w0305"]!=source_pack):
            raise ValueError(f"Scene save source differs {item['source_map_pack']} expected={item['source_real_arrival_xy']} observed={prep['before']['w0305'],prep['before']['w1573'],prep['before']['w157d']} to={prep['after']['w0305'],prep['after']['w1573'],prep['after']['w157d']}")
        for a,b in zip(captures,captures[1:]):
            if (a["after"]["frame"]!=b["before"]["frame"] or
                any(a["after"][key]!=b["before"][key] for key in KEYS)):
                raise ValueError("Return series frame or WRAM not strictly contiguous")
        series=controller["samples"]+neutral1["samples"]+(captures[3]["samples"] if len(captures)==4 else [])
        first_change=next((r for r in series if r["w0305"]!=source_pack),None)
        label={"source_world_transition_id":item["source_world_transition_id"],
               "source_config_id":inp["destination_config_id"],"source_scene_pack":inp["destination_pack"],
               "scene_spawn_xy":inp["settled_arrival_xy"],
               "input":"Down","input_frames":72,
               "source_world_entrance_cheat_positioned":True,
               "return_route_did_not_cheat_coordinates":True,
               "normal_world_route_to_original_entrance_proven":False,
               "universal_story_gate_proven":False,
               "CPU_handler_PC_observed":False,
               "underlying_source_file_digest":item["raw_trace_hashes"],
               "frame_capture_raw_not_committed":True}
        if item["result_status"]=="observed_map_switch_stable_local_window":
            if (len(captures)!=4 or first_change is None or
                first_change["w0305"]!=76 or
               item["map_switch_frame"]!=first_change["frame"] or
               item["destination_pack"]!="0x4C" or
               item["destination_xy"]!=[captures[3]["after"]["w1573"],captures[3]["after"]["w157d"]] or
                captures[3]["after"]["w0305"]!=76):
                raise ValueError("Real world return switch missing / mismatch")
            switches=[(a["frame"],a["w0305"]) for a in series if a["w0305"] not in (source_pack,76)]
            if switches:raise ValueError("Other map packs intervene; cannot treat direct world return")
            final=captures[3]["after"]
            tail=0
            for r in reversed(series):
                if (r["w0305"],r["w1573"],r["w157d"])==(76,final["w1573"],final["w157d"]):
                    tail+=1
                else:break
            if tail<8:raise ValueError("World landing failed stable observation")
            prior=controller["before"]
            before_switch=None
            for r in series:
                if r["frame"]==first_change["frame"]:
                    before_switch=prior;break
                prior=r
            if not before_switch or before_switch["w0305"]!=source_pack:
                raise ValueError("Missing last source-pack coordinate before return")
            if not item.get("screenshot_sha256") or len(item["screenshot_sha256"])!=64:
                raise ValueError("Missing world return screenshot digest")
            local_screen=Path(item["screenshot_path"])
            if not local_screen.is_file() or hashlib.sha256(local_screen.read_bytes()).hexdigest().upper()!=item["screenshot_sha256"]:
                raise ValueError("Source-local screen file does not match recorded SHA256")
            label.update({
              "verified_reverse_result":"observed_direct_return_from_destination_scene_to_saved_world",
              "first_world_pack_switch_frame":first_change["frame"],
              "last_observed_source_xy_before_switch":{"x":before_switch["w1573"],"y":before_switch["w157d"]},
              "world_arrival_xy_in_this_saved_origin_context":{"x":final["w1573"],"y":final["w157d"]},
              "world_destination_pack":"0x4C",
              "world_destination_config_id":"cfg_t01_l001_v1",
              "world_stable_observed_frames":tail,
              "world_stable_through_frame":final["frame"],
              "screenshot_sha256":item["screenshot_sha256"],
              "requires_saved_world_origin_context":True,
              "world_arrival_same_for_other_saves_proven":False,
            })
            results.append(label)
        elif item["result_status"]=="no_scene_pack_change_in_probe_window":
            if (first_change or len(captures)!=3 or
                captures[2]["after"]["w0305"]!=source_pack):
                raise ValueError("Failed negative return case has scene switch")
            label.update({
              "verified_reverse_result":"no_map_change_under_72_frame_down_then_120_neutral",
              "source_after_probe_xy":{"x":captures[2]["after"]["w1573"],"y":captures[2]["after"]["w157d"]},
              "absence_of_exit_globally_proven":False,
              "other_directions_not_checked":True
            })
            negative.append(label)
        else:
            raise ValueError("Unresolved batch case "+item["source_map_pack"])
    if len(results)!=14 or len(negative)!=6:raise ValueError("Expected exactly 14 returns and 6 scoped nonreturns")
    found={r["source_scene_pack"] for r in results}
    if len(found)!=14 or len({r["source_scene_pack"] for r in negative})!=6:
        raise ValueError("Return scenes aren't unique")
    report={
     "schema_version":1,"kind":"fourteen_verified_original_scene_return_events_from_real_controller",
     "source_entrance_ledger":"data/maps/transitions/world_37_gamepad_entrances_after_cheat_20261011.json",
     "research_isolated_hidden_emulator":True,
     "all_batches_original_emulator_restored":True,
     "source_original_world_entrances_cheat_seeded":True,
     "reverse_scene_controller_path_Wram_XY_cheat_used":False,
     "normal_walkable_world_access_all_scenes_proven":False,
     "story_condition_gate_universal":False,
     "actual_native_or_VM_CPU_instruction_PC_observed":False,
     "attempts":20,"confirmed_world_returns":14,"local_nonreturns":6,
     "verified_reverse_returns":results,
     "unconfirmed_local_direction_returns":negative,
     "raw_frame_screenshots_states_or_ROM_committed":False,
     "new_graph_edges_to_add":14,
    }
    OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')
    print(json.dumps({"attempts":20,"world_returns":14,"nonreturns":6,
                      "sources":[r["source_scene_pack"] for r in results],
                      "destinations":[r["world_arrival_xy_in_this_saved_origin_context"] for r in results],
                      "observed_source_tiles":[r["last_observed_source_xy_before_switch"] for r in results]},
                     ensure_ascii=False))
    return report
if __name__=="__main__":analyze()
