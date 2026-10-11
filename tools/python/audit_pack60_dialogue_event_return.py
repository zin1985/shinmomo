#!/usr/bin/env python3
"""Compile strict local pack0x60 12+24 A-dialogue event and actual world return."""
from __future__ import annotations
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_vm_frame_series import inspect_series,BASE_SAMPLE_KEYS,SELECTOR_SAMPLE_KEYS
ROOT=Path(__file__).resolve().parents[2]
LOCAL=Path(r"C:\Users\zin\AppData\Local\shinmomo-bg-lab")
OUT=ROOT/"data/maps/transitions/pack60_dialogue_phase_world_return_20261011.json"
KEYS=("frame",)+BASE_SAMPLE_KEYS+SELECTOR_SAMPLE_KEYS

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def audit(local=LOCAL):
    initial=load(local/"research/village_dialogue_60_A_12_20261011.json")
    extension=load(local/"research/pack60_A12_plus_24_A_and_four_directions_20261011.json")
    follow=load(local/"research/pack60_A36_down_saved_world_extended_stability_20261011.json")
    entry_data=load(ROOT/"data/maps/transitions/world_37_gamepad_entrances_after_cheat_20261011.json")
    entrance=next(x for x in entry_data["entries"] if x["destination_pack"]=="0x60")
    if (entrance["transition_id"]!="catalog_transition_0755" or
        entrance["destination_config_id"]!="cfg_t04_l035_v2" or
        [entrance["settled_arrival_xy"][k] for k in ("x","y")]!=[37,56] or
        initial.get("kind")!="village_scene_repeated_dialogue_and_down_probe" or
        initial.get("A_presses")!=12 or initial.get("original_hidden_emulator_restored") is not True or
        extension.get("kind")!="pack60_dialogue_extended_then_four_real_controller_directions" or
        extension.get("source_after_original_A12")!="village_dialogue_60_after_12_A_20261011" or
        extension.get("no_coordinate_wram_cheat_in_scene") is not True or
        extension.get("dedicated_emulator_restored") is not True or
        extension.get("additional_real_A_presses")!=24 or
        extension.get("raw_captures_not_committed") is not True or
        follow.get("kind")!="pack60_36_real_A_presses_then_Down_world_return_stability" or
        follow.get("no_XY_Wram_edit_during_scene") is not True or
        follow.get("original_hidden_emulator_restored") is not True or
        (follow.get("original_dialogue_A_presses"),follow.get("additional_dialogue_A_presses"))!=(12,24)):
        raise ValueError("Source/original state, event sequence or protection does not match")
    presses=[h for h in extension["history"] if h["button"]=="A8_then_neutral20"]
    directions=[h for h in extension["history"] if h["button"] in ("Down","Up","Left","Right")]
    if ([h["index"] for h in presses]!=list(range(1,25)) or
        [h["button"] for h in directions]!=["Down","Up","Left","Right"] or
        len(initial.get("history",[]))!=14 or
        len(follow.get("records",[]))!=4):
        raise ValueError("Event records were truncated")
    hashes=set()
    screens=set()
    for step in initial["history"]:
        for k in ("neutral_sha256","gamepad_sha256","input_sha256"):
            if step.get(k):hashes.add(step[k])
        if step.get("screen_sha256"):screens.add(step["screen_sha256"])
    for step in extension["history"]:
        for k in ("frame_sha256","gamepad_sha256","neutral_sha256"):
            if step.get(k):hashes.add(step[k])
        if step.get("screenshot_sha256"):screens.add(step["screenshot_sha256"])
    for step in follow["records"]:
        hashes.add(step["trace_sha256"])
        screens.add(step["screenshot_sha256"])
    frame_files={}
    for f in (local/"captures").glob("vmframes_*.json"):
        h=hashlib.sha256(f.read_bytes()).hexdigest().upper()
        if h in hashes:frame_files.setdefault(h,f)
    if set(frame_files)!=hashes:
        raise ValueError(f"Absent hashed frame samples: {len(hashes-set(frame_files))}")
    docs={}
    for h,f in frame_files.items():
        d=load(f);summary=inspect_series(d)
        if summary["schema_version"]!=2:raise ValueError("Need schema2 full frame-end samples")
        docs[h]=d
    img_files=set()
    for f in (local/"screens").glob("game_*.png"):
        h=hashlib.sha256(f.read_bytes()).hexdigest().upper()
        if h in screens:img_files.add(h)
    if img_files!=screens:raise ValueError(f"Missing screen evidence {len(screens-img_files)}")
    def same(a,b):
        return a["after"]["frame"]==b["before"]["frame"] and all(a["after"][k]==b["before"][k] for k in KEYS)
    first=docs[extension["history"][0]["frame_sha256"]]
    if (first["requested_frames"]!=12 or first["input_sent"] or
        (first["before"]["w0305"],first["before"]["w1573"],first["before"]["w157d"])!=(96,37,56)):
        raise ValueError("Extension not started at exact pack60 A12 scene")
    last=first
    printrows=[]
    for step in presses:
        a=docs[step["gamepad_sha256"]];b=docs[step["neutral_sha256"]]
        if (not same(last,a) or not same(a,b) or
            a.get("buttons")!="A" or a.get("input_device")!="isolated_snes_gamepad" or
            not a["input_sent"] or a["requested_frames"]!=8 or
            b["input_sent"] or b["requested_frames"]!=20 or
            (b["after"]["w0305"],b["after"]["w1573"],b["after"]["w157d"])!=(96,37,56) or
            [b["after"]["w1573"],b["after"]["w157d"]]!=step["xy"]):
            raise ValueError(f"Extended A button controller stream not contiguous at {step['index']}")
        printrows.append({"sequence_A_after_previous_twelve":step["index"],
            "absolute_ordinal_A":12+step["index"],
            "frame":step["frame"],
            "screenshot_sha256":step["screenshot_sha256"],
            "pack":"0x60","xy":{"x":37,"y":56},
            "gamepad_trace_sha256":step["gamepad_sha256"],
            "neutral_trace_sha256":step["neutral_sha256"]})
        last=b
    if len({x["screenshot_sha256"] for x in printrows})<10:
        raise ValueError("No significant dialogue/visual phase variation proven")
    # These frames are screenshots of an actual fully black transition
    # inside the source game (not inferred from hash repetition alone).
    blackout=presses[16]["screenshot_sha256"]
    if (blackout!="6BE1250C4F701AA84D921C77F05D8F95753B441F06F39E55D233D4DE0EE9FBC0" or
        [r["screenshot_sha256"] for r in presses[16:21]]!=[blackout]*5):
        raise ValueError("Black-frame interstitial is missing in existing visual record")
    final_screenshot=presses[-1]["screenshot_sha256"]
    if final_screenshot!="B2F1D1EEDB517D43B91D52D2A45C2A9FBCEF66BB574FBA13C15421F30C9D2709":
        raise ValueError("Visual transformed-village screenshot mismatch")
    expected={"Down":("0x4C",[59,155]),"Up":("0x60",[37,40]),
              "Left":("0x60",[36,56]),"Right":("0x60",[38,56])}
    for x in directions:
        a=docs[x["gamepad_sha256"]];b=docs[x["neutral_sha256"]]
        name=x["button"];pack,xy=expected[name]
        if (not same(a,b) or a["requested_frames"]!=96 or
            not a["input_sent"] or a["buttons"]!=name or
            a["input_device"]!="isolated_snes_gamepad" or
            [a["before"]["w0305"],a["before"]["w1573"],a["before"]["w157d"]]!=[96,37,56] or
            b["input_sent"] or b["requested_frames"]!=120 or
            x["pack"]!=pack or x["xy"]!=xy or
            [b["after"]["w0305"],b["after"]["w1573"],b["after"]["w157d"]]!=[int(pack,16),*xy]):
            raise ValueError("Four genuine post-event direction probes did not match")
    line=[docs[r["trace_sha256"]] for r in follow["records"]]
    if not all(same(a,b) for a,b in zip(line,line[1:])):
        raise ValueError("Final long return observations are not contiguous")
    if (line[0]["buttons"]!="Down" or not line[0]["input_sent"] or
        line[0]["requested_frames"]!=96 or
        (line[0]["before"]["w0305"],line[0]["before"]["w1573"],line[0]["before"]["w157d"])!=(96,37,56) or
        any(d["input_sent"] or d["requested_frames"]!=120 for d in line[1:]) or
        (line[-1]["after"]["w0305"],line[-1]["after"]["w1573"],line[-1]["after"]["w157d"])!=(76,59,155)):
        raise ValueError("Return scene pack and landing invalid")
    timeline=[sample for d in line for sample in d["samples"]]
    change=next((x for x in timeline if x["w0305"]!=96),None)
    if change is None or change["w0305"]!=76:
        raise ValueError("Direct 0x60->0x4C pack transition missing")
    stable=sum(1 for d in line[1:] for f in d["samples"]
               if (f["w0305"],f["w1573"],f["w157d"])==(76,59,155))
    if stable!=360:raise ValueError("Arrival at world original position unstable")
    proof={
      "schema_version":1,"kind":"pack60_36_dialogue_A_scene_visual_change_then_real_world_return",
      "source_world_transition_id":"catalog_transition_0755",
      "source_config_id":"cfg_t04_l035_v2","source_pack":"0x60",
      "source_arrival_xy":{"x":37,"y":56},
      "original_world_entry_cheat_seeded":True,
      "scene_controller_XY_coordinate_cheat_used":False,
      "exact_story_gates_proven":False,
      "dialogue_event_cpu_handler_pc_observed":False,
      "A_presses_in_initial_village_study":12,
      "additional_A_presses_in_extension":24,
      "all_real_SNES_A_presses":36,
      "A_held_frames_each":8,"A_neutral_frames_each":20,
      "recorded_A_screen_phases":printrows,
      "A17_to_A21_additional_black_screenshot_identical":True,
      "black_screenshot_sha256":blackout,
      "original_pre_event_screenshot_sha256":initial["history"][0]["screen_sha256"],
      "dialogue_at_initial_A12_screenshot_sha256":initial["history"][12]["screen_sha256"],
      "transformed_village_onscreen_sha256":final_screenshot,
      "visual_transformation_described_from_local_screenshots":"pink_flowery_village_to_brown_withered_vegetation",
      "exact_visual_event_trigger_A_count_proven":False,
      "after_A36_four_direction_real_controller_results":{
          x["button"]:{"scene_pack_after":x["pack"],"xy":x["xy"],
                        "controller_sha256":x["gamepad_sha256"],"neutral_sha256":x["neutral_sha256"]}
          for x in directions},
      "return_after_A36_controller":"Down",
      "return_after_A36_controller_frames":96,
      "return_world_pack":"0x4C","return_world_config_id":"cfg_t01_l001_v1",
      "return_world_xy_this_saved_context":{"x":59,"y":155},
      "world_scene_switch_frame":change["frame"],
      "last_world_frame":line[-1]["after"]["frame"],
      "world_stable_neutral_frames":360,
      "return_destination_for_other_saves_proven":False,
      "source_exact_return_trigger_cell_proven":False,
      "original_world_access_without_cheat_proven":False,
      "runtime_source_emulator_restored_after_probes":True,
      "raw_ROM_screenshots_traces_savestates_committed":False,
      "long_return_frame_sha256":[r["trace_sha256"] for r in follow["records"]],
      "long_return_screen_sha256":[r["screenshot_sha256"] for r in follow["records"]]
    }
    OUT.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"pack60_last_world_switch_frame":change["frame"],
      "world_xy":[59,155],"A_presses":36,"stable_neutral_frames":360,
      "black_interstitial_frames_detected":True,
      "visual_change":"pink_flowered_to_brown_withered"},ensure_ascii=False))
    return proof
if __name__=="__main__":audit()
