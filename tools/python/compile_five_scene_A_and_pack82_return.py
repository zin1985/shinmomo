#!/usr/bin/env python3
"""Strictly compile five actual controller scene experiments plus village dialogue scans.

No raw ROM, savestates, frame captures, image bytes committed.
Generated ledger is only exact pack scoped and one saved-world contextual
exit; it does not infer title-dismissal cause in other three dungeons.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_vm_frame_series import inspect_series, BASE_SAMPLE_KEYS, SELECTOR_SAMPLE_KEYS
ROOT=Path(__file__).resolve().parents[2]
LOCAL=Path(r"C:\Users\zin\AppData\Local\shinmomo-bg-lab")
OUT=ROOT/"data/maps/transitions/five_scene_modal_tests_and_pack82_world_return_20261011.json"
TARGETS=("0xBD","0xB9","0xAB","0x82","0x60")
EXPECTED={
 "0xBD":{"Down":[15,38],"Up":[15,36],"Left":[14,37],"Right":[16,37]},
 "0xB9":{"Down":[68,31],"Up":[68,23],"Left":[62,25],"Right":[74,25]},
 "0xAB":{"Down":[22,11],"Up":[22,3],"Left":[16,5],"Right":[26,5]},
 "0x82":{k:[40,59] for k in ("Down","Up","Left","Right")},
 "0x60":{k:[37,56] for k in ("Down","Up","Left","Right")}
}
KEYS=("frame",)+BASE_SAMPLE_KEYS+SELECTOR_SAMPLE_KEYS

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def audit():
    entrance=read(ROOT/"data/maps/transitions/world_37_gamepad_entrances_after_cheat_20261011.json")
    incoming={x["destination_pack"]:x for x in entrance["entries"]}
    docs=[read(LOCAL/"research/scene_modal5_A8_directional_0_2_20261011.json"),
          read(LOCAL/"research/scene_modal5_A8_directional_2_3_20261011.json")]
    if [x.get("requested_count") for x in docs]!=[2,3]:raise ValueError("Bad batch cardinality")
    for d in docs:
        if (d.get("schema_version")!=1 or d.get("kind")!="five_scenes_title_modal_A8_controller_probes" or
            d.get("original_world_entry_coordinate_cheat_seeded") is not True or
            d.get("controller_probe_XY_coordinate_cheat_used") is not False or
            d.get("original_hidden_emulator_state_restored") is not True or
            d.get("isolated_dedicated_hidden_bizhawk_used") is not True):
            raise ValueError("Missing protected isolated emulator research provenance")
    trials=[r for d in docs for r in d["results"]]
    if [x["pack"] for x in trials]!=list(TARGETS) or any(x["result_status"]!="completed" for x in trials):
        raise ValueError("Expected five individually successful probes in exact order")
    dialogues={p:read(LOCAL/f"research/village_dialogue_{p[2:]}_A_12_20261011.json") for p in ("0x82","0x60")}
    return_raw=read(LOCAL/"research/pack82_A12_down_saved_world_return_stability_20261011.json")
    if (return_raw.get("kind")!="pack82_twelve_real_A_dialogues_then_real_Down_world_return" or
        return_raw.get("original_emulator_restored") is not True or
        return_raw.get("no_xy_Wram_writes_during_scene_return") is not True or
        len(return_raw.get("records",[]))!=4):
        raise ValueError("Missing protected extended destination stability")
    hashes=set()
    screenshots=set()
    for t in trials:
        hashes.update((t["A_trace_sha256"],t["post_A_neutral_sha256"]))
        screenshots.update((t["initial_screenshot_sha256"],t["A_dismissed_screenshot_sha256"]))
        for r in t["directions"]:
            hashes.update((r["gamepad_capture_sha256"],r["neutral_capture_sha256"]))
            screenshots.add(r["screenshot_sha256"])
    for d in dialogues.values():
        for r in d["history"]:
            hashes.add(r["neutral_sha256"])
            if "gamepad_sha256" in r:hashes.add(r["gamepad_sha256"])
            if "input_sha256" in r:hashes.add(r["input_sha256"])
            if "screen_sha256" in r:screenshots.add(r["screen_sha256"])
    for r in return_raw["records"]:
        hashes.add(r["trace_sha256"])
        screenshots.add(r["screenshot_sha256"])
    index={}
    for f in (LOCAL/"captures").glob("vmframes_*.json"):
        digest=hashlib.sha256(f.read_bytes()).hexdigest().upper()
        if digest in hashes:index.setdefault(digest,f)
    if set(index)!=hashes:raise ValueError(f"Missing raw frames {len(hashes-set(index))}")
    captured={}
    for h,f in index.items():
        d=read(f)
        if inspect_series(d)["schema_version"]!=2:raise ValueError("Non-frame-end capture")
        captured[h]=d
    screen_index={}
    for f in (LOCAL/"screens").glob("game_*.png"):
        h=hashlib.sha256(f.read_bytes()).hexdigest().upper()
        if h in screenshots:screen_index.setdefault(h,f)
    if set(screen_index)!=screenshots:raise ValueError(f"Missing screenshot originals {len(screenshots-set(screen_index))}")

    def connected(a,b):
        return (a["after"]["frame"]==b["before"]["frame"] and
                all(a["after"][k]==b["before"][k] for k in KEYS))
    details=[]
    for t in trials:
        pack=t["pack"];root=incoming[pack];val=int(pack,16)
        if (t["source_transition_id"]!=root["transition_id"] or
            t["source_config_id"]!=root["destination_config_id"] or
            t["saved_source_arrival_xy"]!=[root["settled_arrival_xy"][k] for k in ("x","y")] or
            t["original_world_entry_was_cheat_seeded"] is not True or
            t["no_xy_Wram_writes_inside_these_trials"] is not True or
            t["before_A_pack"]!=pack or t["after_A_pack"]!=pack or
            t["before_A_xy"]!=t["saved_source_arrival_xy"] or
            t["after_A_xy"]!=t["saved_source_arrival_xy"] or
            len(t["directions"])!=4):
            raise ValueError("Scene arrival/pack did not match actual original world entry "+pack)
        a=captured[t["A_trace_sha256"]];z=captured[t["post_A_neutral_sha256"]]
        if (not connected(a,z) or a.get("buttons")!="A" or
            a.get("input_sent") is not True or a.get("requested_frames")!=8 or
            z.get("input_sent") or z.get("requested_frames")!=64 or
            a["before"]["w0305"]!=val or
            [a["before"]["w1573"],a["before"]["w157d"]]!=t["before_A_xy"] or
            z["after"]["w0305"]!=val or
            [z["after"]["w1573"],z["after"]["w157d"]]!=t["after_A_xy"]):
            raise ValueError("Post-A scene did not come from real gamepad frames")
        outcomes=[]
        for dr in t["directions"]:
            direction=dr["direction"]
            if direction not in EXPECTED[pack] or direction in [x["direction"] for x in outcomes]:
                raise ValueError("Duplicate/invalid direction")
            x=captured[dr["gamepad_capture_sha256"]];y=captured[dr["neutral_capture_sha256"]]
            if (not connected(x,y) or
                x["input_sent"] is not True or x.get("buttons")!=direction or
                x.get("player")!=1 or x.get("input_device")!="isolated_snes_gamepad" or
                x.get("requested_frames")!=96 or
                y.get("input_sent") or y.get("requested_frames")!=120 or
                dr.get("after_transition_neutral_extra_frames")!=0 or
                dr.get("extra_capture_sha256") is not None or
                x["before"]["w0305"]!=val or
                [x["before"]["w1573"],x["before"]["w157d"]]!=t["after_A_xy"] or
                dr["initial_pack"]!=pack or dr["initial_xy"]!=t["after_A_xy"] or
                dr["after_gamepad_pack"]!=pack or dr["after_neutral_pack"]!=pack or
                dr["final_pack"]!=pack or dr["final_xy"]!=EXPECTED[pack][direction] or
                dr["after_neutral_xy"]!=dr["final_xy"] or
                [y["after"]["w1573"],y["after"]["w157d"]]!=dr["final_xy"] or
                any(row["w0305"]!=val for row in x["samples"]+y["samples"])):
                raise ValueError("Cannot prove scoped directional movement from post-A state "+pack+" "+direction)
            outcomes.append({"direction":direction,"after_gamepad_xy":dr["after_gamepad_xy"],
                "after_neutral_xy":dr["final_xy"],"input_frames":96,"neutral_frames":120,
                "real_gamepad_trace_sha256":dr["gamepad_capture_sha256"],
                "neutral_trace_sha256":dr["neutral_capture_sha256"],
                "screenshot_sha256":dr["screenshot_sha256"],
                "did_not_switch_pack_in_this_probe":True})
        if set(o["direction"] for o in outcomes)!=set(EXPECTED[pack]):
            raise ValueError("Missing one of four directions")
        details.append({
          "source_scene_pack":pack,"source_scene_config_id":t["source_config_id"],
          "original_world_transition_id":t["source_transition_id"],
          "source_scene_arrival_xy":t["saved_source_arrival_xy"],
          "source_world_entrance_cheat_seeded":True,
          "actual_scene_probe_wram_xy_cheat_used":False,
          "real_A8_followed_by_neutral64":True,
          "prior_world_entry_proven":True,
          "scene_A_interaction_cause_of_walking_proven":False,
          "before_A_screenshot_sha256":t["initial_screenshot_sha256"],
          "after_A_screenshot_sha256":t["A_dismissed_screenshot_sha256"],
          "actual_A_trace_sha256":t["A_trace_sha256"],
          "after_A_neutral_trace_sha256":t["post_A_neutral_sha256"],
          "directions":outcomes,
          "all_story_states_reachable_proven":False,
          "no_exit_other_stories_or_directions_proven":False,
          "raw_images_traces_ROM_savestates_committed":False
        })
    conversations=[]
    for pack,doc in dialogues.items():
        expected=incoming[pack]
        if (doc.get("schema_version")!=1 or doc.get("kind")!="village_scene_repeated_dialogue_and_down_probe" or
            doc.get("pack")!=pack or doc.get("source_world_transition_id")!=expected["transition_id"] or
            doc.get("original_hidden_emulator_restored") is not True or
            doc.get("probe_uses_no_xy_cheat") is not True or
            doc.get("A_presses")!=12 or len(doc.get("history",[]))!=14):
            raise ValueError("Dialogue 12 A progression source/protection mismatch")
        events=[]
        for j,step in enumerate(doc["history"]):
            if step["index"]!=j or step["pack"] not in (pack,"0x4C"):raise ValueError("Wrong dialogue sequence")
            if j==0:
                d=captured[step["neutral_sha256"]]
                if d["input_sent"] or d["requested_frames"]!=12:raise ValueError("Bad starting neutral")
            elif j<=12:
                a=captured[step["gamepad_sha256"]];b=captured[step["neutral_sha256"]]
                if (a["buttons"]!="A" or not a["input_sent"] or a["requested_frames"]!=8 or
                    b["input_sent"] or b["requested_frames"]!=20 or not connected(a,b) or
                    [b["after"]["w1573"],b["after"]["w157d"]]!=step["xy"]):
                    raise ValueError("Not twelve real A presses")
            else:
                a=captured[step["input_sha256"]];b=captured[step["neutral_sha256"]]
                if (a["buttons"]!="Down" or not a["input_sent"] or a["requested_frames"]!=96 or
                    b["input_sent"] or b["requested_frames"]!=120 or not connected(a,b) or
                    [b["after"]["w1573"],b["after"]["w157d"]]!=step["xy"]):
                    raise ValueError("Not real Down after twelve A presses")
            if j<13:
                if step["pack"]!=pack or step["xy"]!=[expected["settled_arrival_xy"][k] for k in ("x","y")]:
                    raise ValueError("Scene moved during twelve A trials")
            events.append({"index":j,"input":step["input"],"frame":step["frame"],
                           "scene_pack_after":step["pack"],"xy":step["xy"],
                           "screenshot_sha256":step.get("screen_sha256")})
        if (events[-1]["scene_pack_after"],events[-1]["xy"])!=(("0x4C",[175,189]) if pack=="0x82" else (pack,[37,56])):
            raise ValueError("Expected 82 world return and 60 local nonreturn, not observed")
        conversations.append({
          "pack":pack,"source_world_transition_id":expected["transition_id"],
          "actual_A_button_presses":12,"per_press_held_frames":8,
          "neutral_frames_between_presses":20,
          "scene_xy_unchanged_during_all_twelve_A_presses":True,
          "screenshot_digests_distinct_during_dialogue":len({x["screenshot_sha256"] for x in events if x["screenshot_sha256"]}),
          "followup_controller":"Down","followup_frames":96,"followup_neutral_frames":120,
          "followup_destination_pack":events[-1]["scene_pack_after"],
          "followup_destination_xy":events[-1]["xy"],
          "normal_world_entry_walkability_proven":False,
          "universal_story_state_proven":False,
          "per_step":events,
        })
    traces=[captured[x["trace_sha256"]] for x in return_raw["records"]]
    if len(traces)!=4 or any(not connected(a,b) for a,b in zip(traces,traces[1:])):
        raise ValueError("Missing continuous world stability frames")
    if (traces[0]["buttons"]!="Down" or not traces[0]["input_sent"] or traces[0]["requested_frames"]!=96 or
        any(d["input_sent"] or d["requested_frames"]!=120 for d in traces[1:]) or
        traces[0]["before"]["w0305"]!=130 or
        [traces[0]["before"]["w1573"],traces[0]["before"]["w157d"]]!=[40,59] or
        traces[-1]["after"]["w0305"]!=76 or
        [traces[-1]["after"]["w1573"],traces[-1]["after"]["w157d"]]!=[175,189]):
        raise ValueError("Cannot prove 82 original-scene to real world switch")
    samples=[r for d in traces for r in d["samples"]]
    switch=next((r for r in samples if r["w0305"]!=130),None)
    if switch is None or switch["w0305"]!=76:raise ValueError("Missing direct 82->world frame")
    stable=sum(1 for x in traces[1:] for row in x["samples"]
               if (row["w0305"],row["w1573"],row["w157d"])==(76,175,189))
    if stable!=360:raise ValueError("World scene/coordinate unstable in 360 neutral frames")
    extra={
       "source_pack":"0x82","source_config_id":"cfg_t04_l059_v2",
       "source_world_transition_id":"catalog_transition_0791",
       "original_scene_spawn_xy":{"x":40,"y":59},
       "dialogue_A_presses_before_exit":12,
       "actual_world_return_input":"Down",
       "world_switch_frame":switch["frame"],
       "world_destination_pack":"0x4C",
       "world_destination_config_id":"cfg_t01_l001_v1",
       "world_destination_xy_for_original_saved_world_context":{"x":175,"y":189},
       "world_arrival_stable_neutral_frames":stable,
       "last_observed_world_frame":traces[-1]["after"]["frame"],
       "native_handler_CPU_PC_proven":False,
       "world_destination_other_saves_universal":False,
       "source_exact_exit_hotspot_proven":False,
       "source_entrance_originally_cheat_seeded":True,
       "return_gamepad_xy_coordinate_cheated":False,
       "raw_screenshots_frames_states_or_ROM_committed":False,
       "raw_frame_sha256":[x["trace_sha256"] for x in return_raw["records"]],
       "screenshot_sha256":[x["screenshot_sha256"] for x in return_raw["records"]]
    }
    result={
       "schema_version":1,
       "kind":"five_original_world_entered_scene_A_interactions_and_pack82_saved_world_return",
       "five_scene_pack_contexts":[x["source_scene_pack"] for x in details],
       "five_scene_actual_A8_plus_four_direction_tests":5,
       "total_real_direction_probes":20,
       "dungeon_scene_packs_with_observed_local_movement":["0xBD","0xB9","0xAB"],
       "two_village_scene_packs_still_stationary_after_one_A":["0x82","0x60"],
       "village_twelve_A_dialogue_trials":["0x82","0x60"],
       "village_pack82_saved_world_return_reproduced":True,
       "village_pack60_world_return_observed":False,
       "original_world_entry_cheat_positioned":True,
       "actual_scene_input_XY_coordinate_cheat_used":False,
       "actual_emulator_restored_after_all_local_trials":True,
       "no_globally_valid_story_route_or_exit_missing_claim":True,
       "raw_ROM_images_Wram_frames_savestates_committed":False,
       "new_contextual_saved_world_return_edges":1,
       "scene_trials":details,
       "dialogue_sequences":conversations,
       "pack82_confirmed_world_return":extra,
    }
    OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"scene_tests":len(details),"directional":20,"dialogue_presses_each":12,
                      "pack82_world_switch":switch["frame"],"world_xy":[175,189],
                      "stable_neutral_frames":stable,"pack60_stationary":True}))
if __name__=="__main__":audit()
