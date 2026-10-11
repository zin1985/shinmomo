#!/usr/bin/env python3
"""Audit exact 24 native-gamepad multi-turn dungeon routes, without inventing exits.

Raw WRAM frame recordings and screenshots must remain on the local lab PC.
This emits only per-tile observed player paths, provenance hashes, state limits.
"""
from __future__ import annotations
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from audit_vm_frame_series import inspect_series,BASE_SAMPLE_KEYS,SELECTOR_SAMPLE_KEYS
ROOT=Path(__file__).resolve().parents[2]
LOCAL=Path(r"C:\Users\zin\AppData\Local\shinmomo-bg-lab")
OUTPUT=ROOT/"data/maps/transitions/dungeon_three_pack_24_controller_turn_routes_20261011.json"
ROUTES=[
 ["Up","Left","Up"],["Up","Right","Up"],
 ["Down","Left","Down"],["Down","Right","Down"],
 ["Left","Down","Left"],["Right","Down","Right"],
 ["Left","Up","Left"],["Right","Up","Right"]]
PACKS=[
 ("0xBD","cfg_t36_l150_v2",[15,37]),
 ("0xB9","cfg_t25_l129_v2",[68,25]),
 ("0xAB","cfg_t49_l176_v2",[22,5])]
KEYS=("frame",)+BASE_SAMPLE_KEYS+SELECTOR_SAMPLE_KEYS
def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))
def continuity(a,b):
    return a["after"]["frame"]==b["before"]["frame"] and all(a["after"][key]==b["before"][key] for key in KEYS)
def main():
    local=LOCAL
    batch=read(local/"research/dungeon_branch_8x_0_3_20261011.json")
    original=read(ROOT/"data/maps/transitions/five_scene_modal_tests_and_pack82_world_return_20261011.json")
    mapped={r["source_scene_pack"]:r for r in original["scene_trials"]}
    if (batch.get("schema_version")!=1 or
        batch.get("kind")!="three_dungeons_genuine_controller_branch_path_probes" or
        batch.get("world_entrance_initially_cheat_positioned") is not True or
        batch.get("scene_probe_wram_XY_cheat_used") is not False or
        batch.get("original_hidden_emulator_restored") is not True or
        batch.get("exact_post_A_scene_source_state_used") is not True or
        batch.get("directions_each_segment")!=72 or
        batch.get("start_index")!=0 or batch.get("count")!=3 or
        len(batch.get("results",[]))!=24):
        raise ValueError("Cannot verify 24 real gamepad routes from protected original scenes")
    hashes=set()
    pics=set()
    for t in batch["results"]:
        if len(t.get("raw_steps",[]))!=3:raise ValueError("Missing directional step")
        hashes.update(x["raw_sha256"] for x in t["raw_steps"])
        hashes.add(t["neutral120_sha256"])
        pics.add(t["screenshot_sha256"])
    captures={}
    for f in (local/"captures").glob("vmframes_*.json"):
        digest=hashlib.sha256(f.read_bytes()).hexdigest().upper()
        if digest in hashes:captures.setdefault(digest,f)
    if set(captures)!=hashes:raise ValueError(f"Lost raw hashed WRAM captures: {len(hashes-set(captures))}")
    docs={}
    for h,f in captures.items():
        doc=read(f)
        if inspect_series(doc)["schema_version"]!=2:raise ValueError("Require all frame-end samples")
        docs[h]=doc
    images=set()
    for f in (local/"screens").glob("game_*.png"):
        h=hashlib.sha256(f.read_bytes()).hexdigest().upper()
        if h in pics:images.add(h)
    if images!=pics:raise ValueError(f"Missing actual route screenshots: {len(pics-images)}")
    routes=[]
    by_pack={pk:0 for pk,_,_ in PACKS}
    seen=set()
    for t in batch["results"]:
        pk=t["original_scene_pack"]
        try:
            pack,cfg,start=next(x for x in PACKS if x[0]==pk)
        except StopIteration:
            raise ValueError("Unknown source scene pack")
        index=t["route_index"]
        if (pk,index) in seen or index not in range(8):
            raise ValueError("Duplicate route or invalid ordinal")
        seen.add((pk,index))
        fromworld=mapped[pk]
        if (fromworld["source_scene_config_id"]!=cfg or
            fromworld["source_scene_arrival_xy"]!=start or
            fromworld["real_A8_followed_by_neutral64"] is not True or
            t["original_source_state"]!=f"scene_modal5_{pk[2:]}_post_A_20261011" or
            t["route_buttons"]!=ROUTES[index] or
            t["status"]!="same_scene"):
            raise ValueError("Source or route path does not match original game context")
        docs_for=[docs[step["raw_sha256"]] for step in t["raw_steps"]]
        neutral=docs[t["neutral120_sha256"]]
        if any(not continuity(a,b) for a,b in zip(docs_for,[*docs_for[1:],neutral])):
            raise ValueError("Disjoint controller observations across route turn")
        if t["first_frame"]!=docs_for[0]["before"]["frame"]:
            raise ValueError("Wrong start frame")
        if ((docs_for[0]["before"]["w0305"],docs_for[0]["before"]["w1573"],docs_for[0]["before"]["w157d"])
            !=(int(pk,16),*start)):
            raise ValueError("Not the exact saved post-A start scene")
        turnpoints=[{"x":start[0],"y":start[1]}]
        observed=[{"x":start[0],"y":start[1]}]
        for button,meta,doc in zip(ROUTES[index],t["raw_steps"],docs_for):
            if (meta["button"]!=button or meta["frames"]!=72 or
                doc["buttons"]!=button or doc["input_device"]!="isolated_snes_gamepad" or
                doc["player"]!=1 or doc["input_sent"] is not True or
                doc["requested_frames"]!=72 or
                meta["first_frame"]!=doc["before"]["frame"] or
                meta["last_frame"]!=doc["after"]["frame"] or
                meta["source_pack"]!=pk or meta["destination_pack"]!=pk or
                meta["source_xy"]!=[doc["before"]["w1573"],doc["before"]["w157d"]] or
                meta["destination_xy"]!=[doc["after"]["w1573"],doc["after"]["w157d"]] or
                any(s["w0305"]!=int(pk,16) for s in doc["samples"])):
                raise ValueError("Incorrect real SNES turn packet")
            for row in doc["samples"]:
                point={"x":row["w1573"],"y":row["w157d"]}
                if point!=observed[-1]:observed.append(point)
            turnpoints.append({"x":doc["after"]["w1573"],"y":doc["after"]["w157d"]})
        if (neutral["requested_frames"]!=120 or neutral["input_sent"] or
            neutral["after"]["w0305"]!=int(pk,16) or
            any(s["w0305"]!=int(pk,16) for s in neutral["samples"]) or
            t["neutral120_frame_begin"]!=neutral["before"]["frame"] or
            t["neutral120_frame_end"]!=neutral["after"]["frame"] or
            t["neutral120_after_pack"]!=pk or
            t["neutral120_after_xy"]!=[neutral["after"]["w1573"],neutral["after"]["w157d"]]):
            raise ValueError("Neutral window or same-map outcome invalid")
        for row in neutral["samples"]:
            point={"x":row["w1573"],"y":row["w157d"]}
            if point!=observed[-1]:observed.append(point)
        if observed[-1]!={"x":t["neutral120_after_xy"][0],"y":t["neutral120_after_xy"][1]}:
            raise ValueError("Route's final coordinate inconsistent with observed trace")
        route={
            "id":f"runtime_turn_path_{pk[2:]}_{index:02d}",
            "source_config_id":cfg,"source_scene_pack":pk,
            "from_world_entrance_cheat_adjacent":True,
            "no_scene_xy_cheat_during_controller_path":True,
            "actual_SNES_gamepad_path":True,
            "source_original_scene_xy":{"x":start[0],"y":start[1]},
            "route_index":index,
            "held_button_sequence":ROUTES[index],
            "held_frames_per_step":72,
            "neutral_frames_after_path":120,
            "turn_endpoints_grid":turnpoints,
            "observed_position_trace_grid":observed,
            "arrived_at_grid":observed[-1],
            "source_pack_unchanged_in_all_observed_frames":True,
            "no_new_map_transition_verified_this_route":True,
            "other_story_phase_or_turn_routes_excluded":False,
            "exact_collision_OR_wall_cause_proven":False,
            "actual_CPU_handler_PC_observed":False,
            "raw_ROM_screenshot_and_frame_data_committed":False,
            "first_observed_frame":t["first_frame"],
            "last_observed_frame":neutral["after"]["frame"],
            "gamepad_frame_sha256":[x["raw_sha256"] for x in t["raw_steps"]],
            "neutral_frame_sha256":t["neutral120_sha256"],
            "final_onscreen_screenshot_sha256":t["screenshot_sha256"],
        }
        if len(observed)>300:raise ValueError("Route trace has unreasonable moves")
        routes.append(route)
        by_pack[pk]+=1
    if len(seen)!=24 or any(c!=8 for c in by_pack.values()):
        raise ValueError("Not exactly eight independent routes for all 3 dungeons")
    evidence={
        "schema_version":1,
        "kind":"three_dungeons_24_real_gamepad_turning_routes_without_pack_switch",
        "created_from_hidden_lab_original_state_restored":True,
        "initial_world_entrance_cheat_seeded":True,
        "genuine_onscene_controller_XY_coordinate_cheat":False,
        "pack_scoped_routes":by_pack,
        "three_dungeons":len(by_pack),
        "true_multiturn_controller_routes":len(routes),
        "total_directional_gamepad_segments":72,
        "real_controller_frames_per_segment":72,
        "neutral_frames_after_each_route":120,
        "added_cross_map_transition_edges":0,
        "other_map_exits_universally_excluded":False,
        "raw_ROM_screenshots_savestates_frames_not_committed":True,
        "source_previous_verified_scene_trials":"data/maps/transitions/five_scene_modal_tests_and_pack82_world_return_20261011.json",
        "routes":routes
    }
    OUTPUT.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"total_paths":len(routes),"total_segments":72,
       "unique_observed_grid_tiles_by_pack":{pk:len({(pt["x"],pt["y"]) for r in routes if r["source_scene_pack"]==pk for pt in r["observed_position_trace_grid"]}) for pk in by_pack},
       "max_path_observed_unique_tiles":max(len(r["observed_position_trace_grid"]) for r in routes)},
       ensure_ascii=False))
if __name__=="__main__":main()
