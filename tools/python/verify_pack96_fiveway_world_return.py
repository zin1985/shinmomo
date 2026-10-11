#!/usr/bin/env python3
"""Audit pack0x96 five-input automatic descent and modal-dismissed world return.

All executable frame traces, screenshots, save states and ROM stay LOCAL.
Committed derived JSON records frame coordinates and SHA256 only.
"""
from __future__ import annotations
from pathlib import Path
from collections import Counter
import argparse,hashlib,json,sys
from audit_vm_frame_series import inspect_series,BASE_SAMPLE_KEYS,SELECTOR_SAMPLE_KEYS

ROOT=Path(__file__).resolve().parents[2]
DEFAULT_LOCAL=Path(r"C:\Users\zin\AppData\Local\shinmomo-bg-lab")
OUT=ROOT/"data/maps/transitions/pack96_5way_modal_and_world_return_20261011.json"
NAME=ROOT/"data/maps/context/pack96_runtime_location_title_20261011.json"
NAMES=("Down","Up","Left","Right","None")
# Real-probe hashes for A/title dismissal, real Up and complete world landing.
A8="48B71D48336D1521599F7DAD30B97DA46F179887388A330738CE6067EEE70048"
A64="B817458679178297442007FBE24611704501DB268605A71AA7821CB8351D27DE"
WALK_UP="F832B3F028F214AB19BF5D6F2B455D93D9F7E639FBB748C9E828F8D0D59844F8"
SETTLE=(
 "4DE6F2D1F25579BCED23F7FE63A75191857A6A577B20CDD2D4777475BD5D9587",
 "8E1372C39A62306DD3F7769EC8D0F0344994826FE1253BDADD7316E3C1794C7A",
 "CF6880A6D7342EB86111ACBDB608DC2BFE5A5B6AAFE291138DF642A92A476787",
 "FEE349F3F3B2E1C65FCA6132662925F5F0BA09E9D0DC8EBBE67F18CA980B046F"
)
NONE_BEFORE_RIGHT="42DE1F36AE21EE094C607638196C69D689E592025F5265D3A30AEE670A282FCC"
BLOCKED_RIGHT="9F4C9621B099C773D7AD2D81802A32726CAB847F8969CD6D04B47040C91E6750"
UNBLOCKED_RIGHT="0E99533E34C282D6F4E278B954DAFADAD308D96FE94D5E5E4D2F6684F77586AE"
DISPLAY_PRE="7BBEABEEE411E44B184CA64B89D28FE42774FAA149B5E60E6786D37337674C82"
DISPLAY_POST="7E51D71F560B09DF1AB19678CEA7018CEB839E39E98D6B1EB2A37A8E16E609AF"
DISPLAY_WORLD="33C9DF73C69381E28A99ECBD6B819BAC0298459584BBA49BD47100BB682AB0C5"
KEYS=("frame",)+BASE_SAMPLE_KEYS+SELECTOR_SAMPLE_KEYS

def match(local,hashes):
    hashes=set(hashes)
    found={}
    for path in (local/"captures").glob("vmframes_*.json"):
        h=hashlib.sha256(path.read_bytes()).hexdigest().upper()
        if h in hashes:found.setdefault(h,path)
    if set(found)!=hashes:
        raise ValueError("Missing exact local frame captures: "+str(sorted(hashes-set(found))))
    output={}
    for h,f in found.items():
        doc=json.loads(f.read_text(encoding="utf-8"))
        checked=inspect_series(doc)
        if checked["schema_version"]!=2:raise ValueError("Need strict frame-end capture")
        output[h]=doc
    return output

def verify_order(docs):
    for old,new in zip(docs,docs[1:]):
        if (old["after"]["frame"]!=new["before"]["frame"] or
            any(old["after"][k]!=new["before"][k] for k in KEYS)):
            raise ValueError("Cannot splice noncontiguous observations")
    return [r for doc in docs for r in doc["samples"]]

def hash_screen(local,h):
    screen=list((local/"screens").glob("game_*.png"))
    for f in screen:
        if hashlib.sha256(f.read_bytes()).hexdigest().upper()==h:
            return True
    return False

def audit(local=DEFAULT_LOCAL):
    prior=json.loads((ROOT/"data/maps/transitions/world_14_reverse_returns_after_cheat_arrivals_20261011.json").read_text(encoding="utf-8"))
    updoc=json.loads((ROOT/"data/maps/transitions/six_scene_up_no_pack_switch_20261011.json").read_text(encoding="utf-8"))
    old=json.loads((ROOT/"data/maps/transitions/pack96_up_down_identical_forced_movement_20261011.json").read_text(encoding="utf-8"))
    down=next(i for i in prior["unconfirmed_local_direction_returns"] if i["source_scene_pack"]=="0x96")
    up=next(i for i in updoc["probes"] if i["source_pack"]=="0x96")
    groups={"Down":down["underlying_source_file_digest"],
            "Up":up["trace_sha256"]}
    for b in ("Left","Right"):
        fn=local/"research"/f"reverse_scene_batch_0_1_{b}_20261011.json"
        j=json.loads(fn.read_text(encoding="utf-8-sig"))
        if (j.get("schema_version")!=1 or
            j.get("untouched_original_emulator_restored") is not True or
            j.get("actual_reverse_test_no_xy_wram_edits") is not True or
            j["results"][0]["source_map_pack"]!="0x96" or
            j["results"][0]["actual_test_controller"]!=b or
            j["results"][0]["result_status"]!="no_scene_pack_change_in_probe_window"):
            raise ValueError("Untrusted left/right source")
        groups[b]=j["results"][0]["raw_trace_hashes"]
    neutral=json.loads((local/"research/pack96_no_buttons_204_frames_20261011.json").read_text(encoding="utf-8-sig"))
    if (neutral.get("schema_version")!=1 or
        neutral.get("kind")!="protected_pack96_no_buttons_control_204frames" or
        neutral.get("all_previous_emulator_state_restored") is not True or
        neutral.get("no_xy_wram_edits_during_control") is not True or
        neutral.get("no_gamepad_buttons_sent") is not True):
        raise ValueError("No-button control not source-protected")
    groups["None"]=[c["raw_sha256"] for c in neutral["captures"]]
    digest={h for g in groups.values() for h in g}
    digest.update((A8,A64,WALK_UP,*SETTLE,
                   NONE_BEFORE_RIGHT,BLOCKED_RIGHT,UNBLOCKED_RIGHT))
    data=match(local,digest)
    series={}
    for b,hashes in groups.items():
        docs=[data[h] for h in hashes]
        rows=verify_order(docs)
        if (len(rows)<204 or
            (rows[0]["frame"],rows[0]["w0305"],rows[0]["w1573"],rows[0]["w157d"])!=(663329,150,39,17) or
            b=="None" and any(d["input_sent"] for d in docs) or
            b!="None" and (docs[1]["input_sent"] is not True or
                           docs[1]["buttons"]!=b or
                           docs[1]["input_device"]!="isolated_snes_gamepad" or
                           docs[1]["player"]!=1) or
            any(docs[i]["input_sent"] for i in (0,2))):
            raise ValueError("Five-way comparison isn't from same scene/actual buttons")
        series[b]=[(row["frame"],row["w0305"],row["w1573"],row["w157d"]) for row in rows[:204]]
    if any(series[b]!=series["None"] for b in NAMES):
        raise ValueError("An actual controller position differs from no-input")
    if (series["None"][-1]!=(663532,150,39,24) or
        old["both_direction_position_series_identical_frame_count"]!=204):
        raise ValueError("Wrong deterministic natural descent")
    steps=[];prev=(39,17)
    for frame,pack,x,y in series["None"]:
        if pack!=150:raise ValueError("Scene changed in controlled descent")
        if (x,y)!=prev:
            steps.append({"frame":frame,"x":x,"y":y});prev=(x,y)
    if ([v["frame"] for v in steps]!=[663333,663342,663351,663360,663369,663378,663387] or
        [v["y"] for v in steps]!=list(range(18,25))):
        raise ValueError("Descent cadence differs")
    # Disambiguate a modal-only lock from geometry/collision: identical
    # 72 neutral frames + Right72 stays at (39,24), whereas
    # A8+neutral64 followed by actual Right72 moves to (42,24).
    blocked=[data[h] for h in (NONE_BEFORE_RIGHT,BLOCKED_RIGHT)]
    clear=[data[h] for h in (A8,A64,UNBLOCKED_RIGHT)]
    br=verify_order(blocked)
    cr=verify_order(clear)
    if (blocked[0]["input_sent"] or blocked[0]["requested_frames"]!=72 or
        not blocked[1]["input_sent"] or blocked[1]["buttons"]!="Right" or
        blocked[1]["requested_frames"]!=72 or
        (blocked[1]["before"]["w0305"],blocked[1]["before"]["w1573"],blocked[1]["before"]["w157d"])!=(150,39,24) or
        (blocked[1]["after"]["w0305"],blocked[1]["after"]["w1573"],blocked[1]["after"]["w157d"])!=(150,39,24) or
        any((r["w0305"],r["w1573"],r["w157d"])!=(150,39,24) for r in br) or
        not clear[0]["input_sent"] or clear[0]["buttons"]!="A" or
        clear[0]["requested_frames"]!=8 or
        clear[1]["input_sent"] or clear[1]["requested_frames"]!=64 or
        not clear[2]["input_sent"] or clear[2]["buttons"]!="Right" or
        clear[2]["requested_frames"]!=72 or
        (clear[2]["after"]["w0305"],clear[2]["after"]["w1573"],clear[2]["after"]["w157d"])!=(150,42,24)):
        raise ValueError("Cannot prove modal blocking via neutral+Right vs A+Right")
    chain=[data[h] for h in (A8,A64,WALK_UP,*SETTLE)]
    rows=verify_order(chain)
    assert len(chain)==7
    if (chain[0]["buttons"]!="A" or not chain[0]["input_sent"] or
        chain[0]["requested_frames"]!=8 or
        chain[1]["input_sent"] or chain[1]["requested_frames"]!=64 or
        chain[2]["buttons"]!="Up" or not chain[2]["input_sent"] or
        chain[2]["requested_frames"]!=96 or
        any(d["input_sent"] for d in chain[3:]) or
        any(d["requested_frames"]!=120 for d in chain[3:]) or
        (chain[0]["before"]["w0305"],chain[0]["before"]["w1573"],chain[0]["before"]["w157d"])!=(150,39,24) or
        (chain[2]["before"]["w0305"],chain[2]["before"]["w1573"],chain[2]["before"]["w157d"])!=(150,39,24)):
        raise ValueError("Cannot prove A-title-dismissal and real Up escape")
    change=next((row for row in rows if row["w0305"]!=150),None)
    if (not change or change["frame"]!=663807 or
        (change["w0305"],change["w1573"],change["w157d"])!=(76,39,7)):
        raise ValueError("Scene-to-world switch phase mismatch")
    settled=next((row for row in rows if (row["w0305"],row["w1573"],row["w157d"])==(76,50,129)),None)
    if not settled or settled["frame"]!=663897:raise ValueError("Delayed world XY correction missing")
    if any((x["w0305"],x["w1573"],x["w157d"])!=(76,50,129)
           for x in rows if x["frame"]>=663897):
        raise ValueError("World arrival failed to remain stable")
    if any(x["w126e"]!=76 or x["w12b4"]!=76 for x in rows if x["frame"]>=663976):
        raise ValueError("Raw selector pack never converged to world")
    # Ground the Japanese title in an actual screenshot, not a reused map.
    for h in (DISPLAY_PRE,DISPLAY_POST,DISPLAY_WORLD):
        if not hash_screen(local,h):
            raise ValueError("Missing local original named/location screenshot")
    proof={
        "schema_version":1,
        "kind":"pack96_five_way_no_input_and_modal_unlocked_world_escape",
        "source_world_transition_id":"catalog_transition_0756",
        "source_config_id":"cfg_t09_l098_v2",
        "source_pack":"0x96",
        "source_world_entry_was_cheat_seeded":True,
        "scene_controller_probe_wram_xy_cheat_used":False,
        "location_title_onscreen":"音無しの洞窟",
        "display_title_at_blocked_state_screenshot_sha256":DISPLAY_PRE,
        "display_title_cleared_post_A_screenshot_sha256":DISPLAY_POST,
        "actual_world_screenshot_sha256":DISPLAY_WORLD,
        "conditions":["Down","Up","Left","Right","None"],
        "five_conditions_full_204_frame_position_identity":True,
        "identical_frame_count_each":204,
        "same_frame_range":[663329,663532],
        "real_left_right_gamepad_presses_observed":True,
        "neutral_no_buttons_test_observed":True,
        "descent_steps":steps,
        "end_of_automatic_descent_xy":{"x":39,"y":24},
        "title_modal_blocked_directional_movement":True,
        "no_button_then_right_72_blocked_verified":True,
        "A_then_right_72_walkable_verified":True,
        "no_button_right_traces_sha256":[NONE_BEFORE_RIGHT,BLOCKED_RIGHT],
        "A_then_right_traces_sha256":[A8,A64,UNBLOCKED_RIGHT],
        "A_press_then_Up_world_return_observed":True,
        "post_title_A_frames":8,
        "post_title_neutral_frames":64,
        "world_return_actual_gamepad_direction":"Up",
        "world_return_actual_gamepad_frames":96,
        "pack_switch_frame":663807,
        "temporary_world_pack_xy":{"x":39,"y":7},
        "world_arrival_first_stable_frame":663897,
        "world_arrival_xy":{"x":50,"y":129},
        "world_pack":"0x4C",
        "world_config_id":"cfg_t01_l001_v1",
        "world_stable_through_frame":664216,
        "world_raw_selector_converged":True,
        "world_arrival_for_other_savestates_proven":False,
        "all_story_phases_verified":False,
        "exact_CPU_instruction_PC_observed":False,
        "natural_world_entry_walkability_proven":False,
        "modal_causal_code_handler_proven":False,
        "source_exit_exact_hotspot_tile_proven":False,
        "raw_traces_screens_ROM_or_states_committed":False,
        "five_way_trace_sha256":groups,
        "modal_escape_full_trace_sha256":[A8,A64,WALK_UP,*SETTLE],
    }
    OUT.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    title={
      "schema_version":1,"kind":"runtime_onscreen_location_title_proof",
      "map_config_id":"cfg_t09_l098_v2","runtime_pack_id_hex":"0x96",
      "onscreen_title":"音無しの洞窟",
      "location_identity_confidence":"confirmed_onscreen_title_for_runtime_pack_context",
      "onscreen_title_source":"actual_BizHawk_pack96_modal_screenshot_after_world_gamepad_entry",
      "source_evidence":"data/maps/transitions/pack96_5way_modal_and_world_return_20261011.json",
      "screenshot_sha256":DISPLAY_PRE,"screenshot_committed":False,
      "applies_to_all_configs_sharing_tileset_layout":False,
      "all_story_phases_location_identity_proven":False,
      "world_entered_after_cheat_adjacent_original_entrance":True
    }
    NAME.write_text(json.dumps(title,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"five_identical_frame_series":204,"five_conditions":5,
                      "world_switch_frame":663807,"world_arrival_frame":663897,
                      "world_xy":[50,129],"title":"音無しの洞窟"},ensure_ascii=False))
    return proof

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--local-lab",type=Path,default=DEFAULT_LOCAL)
    audit(parser.parse_args().local_lab)
