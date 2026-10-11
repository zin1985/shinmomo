#!/usr/bin/env python3
"""Audit six Up-direction followups for the six Down-unconfirmed scenes.

Do not mistake failure to switch in one local state for absence
of any exit. Each raw frame capture stays in the local lab.
"""
from pathlib import Path
import json,hashlib,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_vm_frame_series import inspect_series,BASE_SAMPLE_KEYS,SELECTOR_SAMPLE_KEYS
ROOT=Path(__file__).resolve().parents[2]
LOCAL=Path(r"C:\Users\zin\AppData\Local\shinmomo-bg-lab")
FILES=[
    ("0x96",0),
    ("0xBD",3),
    ("0xB9",4),
    ("0xAB",6),
    ("0x82",14),
    ("0x60",16),
]
KEYS=("frame",)+BASE_SAMPLE_KEYS+SELECTOR_SAMPLE_KEYS
OUTPUT=ROOT/"data/maps/transitions/six_scene_up_no_pack_switch_20261011.json"
def audit():
    ledger=json.loads((ROOT/"data/maps/transitions/world_37_gamepad_entrances_after_cheat_20261011.json").read_text(encoding="utf-8"))
    inputs={e["transition_id"]:e for e in ledger["entries"]}
    raw=[]
    needed=set()
    for pack,n in FILES:
        f=LOCAL/"research"/f"reverse_scene_batch_{n}_1_Up_20261011.json"
        doc=json.loads(f.read_text(encoding="utf-8-sig"))
        if (doc.get("schema_version")!=1 or doc.get("kind")!="protected_original_scene_arrival_controller_exit_trials" or
            doc.get("source_original_world_entry_cheat_positioned") is not True or
            doc.get("actual_reverse_test_no_xy_wram_edits") is not True or
            doc.get("untouched_original_emulator_restored") is not True or
            len(doc.get("results",[]))!=1 or doc["results"][0]["source_map_pack"]!=pack):
            raise ValueError("Missing exactly one protected Up scene trial "+pack)
        item=doc["results"][0]
        if (item.get("result_status")!="no_scene_pack_change_in_probe_window" or
            item.get("actual_test_controller")!="Up" or item.get("input_frames")!=72 or
            len(item.get("raw_trace_hashes",[]))!=3):
            raise ValueError("Up trial did not match expected local negative observation")
        raw.append(item)
        needed.update(item["raw_trace_hashes"])
    index={}
    for file in (LOCAL/"captures").glob("vmframes_*.json"):
        digest=hashlib.sha256(file.read_bytes()).hexdigest().upper()
        if digest in needed:
            # Same deterministic neutral capture may exist at two paths.
            # Identical content hashes are safe to deduplicate.
            index.setdefault(digest,file)
    if set(index)!=needed:raise ValueError("Local trusted raw captures absent")
    report=[]
    for item in raw:
        pack=item["source_map_pack"]
        original=inputs.get(item["source_world_transition_id"])
        if (not original or original["destination_pack"]!=pack or
            original["destination_config_id"]!=item["source_config_id"] or
            [original["settled_arrival_xy"][k] for k in ("x","y")]!=item["source_real_arrival_xy"]):
            raise ValueError("Source came from an unverified exact-pack entry")
        docs=[]
        for digest in item["raw_trace_hashes"]:
            doc=json.loads(index[digest].read_text(encoding="utf-8"))
            checked=inspect_series(doc)
            if checked["schema_version"]!=2:raise ValueError("Strict frame-end schema required")
            docs.append(doc)
        before,up,neutral=docs
        scene=int(pack,16)
        if ((before["before"]["w0305"],before["before"]["w1573"],before["before"]["w157d"])!=
            (scene,*item["source_real_arrival_xy"]) or
            before["requested_frames"]!=12 or before["input_sent"] or
            up["input_device"]!="isolated_snes_gamepad" or
            up.get("buttons")!="Up" or up["player"]!=1 or up["requested_frames"]!=72 or
            not up["input_sent"] or
            neutral["requested_frames"]!=120 or neutral["input_sent"]):
            raise ValueError("Source pose / true Up input / neutral window invalid")
        for a,b in zip(docs,docs[1:]):
            if (a["after"]["frame"]!=b["before"]["frame"] or
                any(a["after"][k]!=b["before"][k] for k in KEYS)):
                raise ValueError("Broken sample-to-sample frame or WRAM continuity")
        series=[*before["samples"],*up["samples"],*neutral["samples"]]
        if any(row["w0305"]!=scene for row in series):
            raise ValueError("One of six local negatives DID leave the source pack")
        final=neutral["after"]
        if (item["destination_pack"]!=pack or
            item["destination_xy"]!=[final["w1573"],final["w157d"]]):
            raise ValueError("Final no-switch observation not independently reproducible")
        changes=[]
        previous=before["before"]
        for row in series:
            if (row["w1573"],row["w157d"])!=(previous["w1573"],previous["w157d"]):
                changes.append({"frame":row["frame"],
                                "x":row["w1573"],"y":row["w157d"]})
            previous=row
        entry={
           "source_pack":pack,
           "source_config_id":item["source_config_id"],
           "original_world_transition_id":item["source_world_transition_id"],
           "source_scene_original_arrival_xy":item["source_real_arrival_xy"],
           "source_original_world_approach_cheat":True,
           "reverse_experiment_controller_has_no_cheat":True,
           "controller":"Up","controller_frames":72,"neutral_frames":120,
           "no_pack_switch_in_observation":True,
           "other_direction_or_story_state_exits_proven_absent":False,
           "scene_final_xy_after_neutral":{"x":final["w1573"],"y":final["w157d"]},
           "first_input_frame":up["before"]["frame"],
           "end_neutral_frame":final["frame"],
           "observed_xy_changes":changes,
           "trace_sha256":list(item["raw_trace_hashes"]),
           "raw_frame_capture_committed":False
        }
        if pack=="0x96":
            if ([final["w1573"],final["w157d"]]!=[39,24] or
                [before["before"]["w1573"],before["before"]["w157d"]]!=[39,17] or
                not any(c["y"]>17 for c in changes)):
                raise ValueError("Native downward drift while pressing Up unverified")
            entry["up_input_did_not_prevent_downward_drift_in_this_state"]=True
            entry["autonomous_motion_or_script_pending"]="cause_unresolved"
        report.append(entry)
    if len(report)!=6:raise ValueError("Exactly six Up local trials required")
    payload={
      "schema_version":1,
      "kind":"six_protected_up_direction_dungeon_and_village_no_switch_observations",
      "previous_down_trial_proof":"data/maps/transitions/world_14_reverse_returns_after_cheat_arrivals_20261011.json",
      "six_exact_scopes":[x["source_pack"] for x in report],
      "all_original_hidden_emulator_states_restored":True,
      "original_world_to_scene_entry_cheat_positioned":True,
      "Up_trial_no_coordinate_cheat":True,
      "each_trial_duration_input_plus_neutral_frames":192,
      "six_observed_no_scene_switch":True,
      "universal_no_exit_claim":False,
      "raw_samples_ROM_states_screens_not_committed":True,
      "probes":report
    }
    OUTPUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"six_no_switch":len(report),
                      "pack96_drift":next(x["observed_xy_changes"] for x in report if x["source_pack"]=="0x96")},
                     ensure_ascii=False))
if __name__=="__main__":audit()
