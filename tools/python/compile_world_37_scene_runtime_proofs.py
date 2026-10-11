#!/usr/bin/env python3
"""Convert LOCAL hidden-BizHawk world-hotspot experiment artifacts into ROM-backed metadata.

Never commit local frame logs, screenshots, real ROM or savestates. Exact
per-pack visible Japanese place names were manually checked from a
montage, NOT derived from map layout equality or coerced dialogue.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
WORLD_ID="cfg_t01_l001_v1"
WORLD_PACK="0x4C"
TITLE_BY_PACK={
    "0x4D":"桃太郎の生家",
    "0x91":"おむすびころりん",
    "0x65":"ほほえみの村",
    "0x83":"竹取の村",
    "0x8E":"神仙郷",
    "0x5A":"すずめのお宿1",
    "0x5B":"すずめのお宿2",
    "0x5D":"すずめのお宿5",
    "0x5E":"すずめのお宿6",
    "0x5F":"すずめのお宿7",
    "0x6B":"寝太郎の村",
    "0x80":"すずめのお宿4",
    "0x8C":"はらだしの里",
    "0x98":"音無しの洞窟",
    "0x7A":"でか太郎の庵",
    "0x87":"神々の里",
    "0x8A":"びろーんの森",
    "0x7C":"桃葉山",
    "0x9E":"大江山",
    "0xBD":"鬼が島",
    "0xB1":"鬼の牢獄",
    "0xA9":"氷の塔",
    "0xB9":"虹の洞窟",
    "0xAD":"伏龍の洞窟",
    "0xAB":"怨みの洞窟",
}
ALREADY_PROVEN_PACKS={"0x4D","0x91"}
PLACE_OUTPUT=ROOT/"data/maps/context/world_batch_verified_onscreen_titles_20261011.json"
ENTRY_OUTPUT=ROOT/"data/maps/transitions/world_37_gamepad_entrances_after_cheat_20261011.json"
CSV_PATH=ROOT/"data/maps/context/map_location_identity_candidates_20260930.csv"

def verify_all(raw_records:list[dict],world:dict):
    matches={e["transition_id"]:e for e in world["transition_edges"]}
    seen=set()
    good=[];no_switch=[]
    for raw in raw_records:
        eid=raw["source_id"]
        if eid in seen:raise ValueError(f"Duplicate trial identifier: {eid}")
        seen.add(eid)
        e=matches.get(eid)
        if not e or e.get("source_config_id")!=WORLD_ID or not e.get("source_hotspot_binding"):
            raise ValueError(f"Not an existing bounded world-entry edge: {eid}")
        h=e["source_hotspot_binding"]
        sx,sy=raw["source_cell_xy"]
        if (sx,sy)!=(h.get("source_grid_x"),h.get("source_grid_y")) or (
            raw["static_destination_pack"],raw["static_destination_config"])!=(
                e.get("destination_pack"),e.get("destination_config_id")):
            raise ValueError(f"World hotspot/config/pack disagrees with ROM: {eid}")
        ax,ay=raw["approach_xy"]
        if (ax,ay)!=(sx,sy+1) or raw.get("approach_direction")!="Up":
            raise ValueError(f"Unverified south-to-north approach: {eid}")
        if raw["source_position_cheat"] is not True or raw["gamepad_trigger"] is not True:
            raise ValueError("Undisclosed or synthetic controller movement")
        if raw["entry_replay_status"]=="gamepad_event_arrived_at_rom_candidate_pack":
            if (not raw.get("source_hotspot_touched") or not raw.get("source_contact_frame") or
                not raw.get("map_switch_frame") or
                raw.get("runtime_target_pack")!=e["destination_pack"] or
                not isinstance(raw.get("runtime_arrival_xy"),list) or
                len(raw["runtime_arrival_xy"])!=2 or
                any(type(x)is not int or not 0<=x<=255 for x in raw["runtime_arrival_xy"])):
                raise ValueError(f"Actual destination pack/trigger proof missing {eid}")
            rx,ry=raw["runtime_arrival_xy"]
            if e.get("destination_x") not in (None,rx) or e.get("destination_y") not in (None,ry):
                raise ValueError(f"ROM destination disagrees with observed arrival {eid}")
            if not (isinstance(raw.get("screenshot_sha256"),str) and
                    len(raw["screenshot_sha256"])==64 and
                    isinstance(raw.get("raw_input_capture_sha256"),str) and
                    len(raw["raw_input_capture_sha256"])==64 and
                    isinstance(raw.get("raw_neutral_capture_sha256"),str) and
                    len(raw["raw_neutral_capture_sha256"])==64 and
                    isinstance(raw.get("raw_extra_neutral_capture_sha256"),str) and
                    len(raw["raw_extra_neutral_capture_sha256"])==64):
                raise ValueError(f"Missing 3 capture digests or screen hash {eid}")
            local=Path(raw["screenshot_local_path"])
            if not local.is_file() or hashlib.sha256(local.read_bytes()).hexdigest().upper()!=raw["screenshot_sha256"]:
                raise ValueError(f"Screenshot bytes not at expected current local source {eid}")
            if raw.get("state_name") is None:
                # A previous interrupted batch may have saved the same
                # unique state already. The batch never overwrites it.
                expected=f"analysis_multi_world_{eid}_p{e['destination_pack'][2:]}_20261011.State"
                path=Path(r"C:\Users\zin\AppData\Local\shinmomo-bg-lab\states")/expected
                if not path.is_file():
                    raise ValueError(f"No protected destination savestate exists {eid}")
            good.append({
                "transition_id":eid,
                "source_config_id":WORLD_ID,
                "source_world_pack":WORLD_PACK,
                "source_hotspot_xy":{"x":sx,"y":sy,"width":h["source_width"],"height":h["source_height"]},
                "cheat_positioned_approach_xy":{"x":ax,"y":ay},
                "source_position_supplied_by_analysis_cheat":True,
                "normal_world_walking_route_to_source_proven":False,
                "source_hotspot_contact_frame":raw["source_contact_frame"],
                "map_switch_frame":raw["map_switch_frame"],
                "real_snes_gamepad_input":"Up",
                "destination_config_id":e["destination_config_id"],
                "destination_pack":e["destination_pack"],
                "settled_arrival_xy":{"x":rx,"y":ry},
                "scene_pack_matches_rom_candidate":True,
                "cpu_rom_opcode_PC_observed":False,
                "all_story_states_accessible_proven":False,
                "screenshot_sha256":raw["screenshot_sha256"],
                "local_raw_input_sha256":raw["raw_input_capture_sha256"],
                "local_raw_neutral_sha256":raw["raw_neutral_capture_sha256"],
                "local_raw_second_neutral_sha256":raw["raw_extra_neutral_capture_sha256"],
                "screenshot_raw_committed":False,
                "local_savestate_raw_committed":False,
                "inferred_onscreen_title":None,
            })
        elif raw["entry_replay_status"]=="no_pack_switch_observed":
            no_switch.append({
               "transition_id":eid,"source_world_hotspot":[sx,sy],
               "source_hotspot_contact_observed":raw.get("source_hotspot_touched") is True,
               "observed_final_world_xy":raw.get("final_world_xy"),
               "test_approach":"south_with_Up",
               "did_not_switch_this_local_state":True,
               "all_story_states_blocked_proven":False,
               "ROM_candidate_still_valid":True,
            })
        else:
            raise ValueError(f"Unreviewed/error probe cannot enter proof ledger: {eid}")
    return good,no_switch


def generate(local_dir:Path):
    world=json.loads((ROOT/"viewer/data/world.json").read_text(encoding="utf-8"))
    files=sorted(local_dir.glob("world_batch_*_south_20261011.json"),
                 key=lambda p:int(p.stem.split("_")[2]))
    if len(files)!=6:raise ValueError("Must have all six known isolated world probe batches")
    raw=[];keys=set()
    for file in files:
        doc=json.loads(file.read_text(encoding="utf-8-sig"))
        if not (doc.get("schema_version")==1 and
                doc.get("kind")=="cheat_adjacent_world_to_actual_gamepad_scene_batch" and
                doc.get("source_map_pack")==WORLD_PACK and
                doc.get("source_xy_set_by_cheat_before_controller") is True and
                doc.get("original_emulator_state_restored") is True and
                doc.get("all_current_story_gates_proven") is False):
            raise ValueError(f"One bulk research capture has incomplete safety provenance: {file}")
        raw.extend(doc["results"])
        keys.add((file.name,doc["total_requested"]))
    if len(raw)!=40 or len(keys)!=6:
        raise ValueError(f"Expected 40 distinct attempted hotspots; got {len(raw)}")
    good,bad=verify_all(raw,world)
    if len(good)!=37 or len(bad)!=3:
        raise ValueError(f"Expected 37 successes/3 negative local probes, not {len(good)}/{len(bad)}")
    by_pack={}
    for entry in good:by_pack.setdefault(entry["destination_pack"],[]).append(entry)
    if len(by_pack)!=36 or len(set(x["destination_config_id"] for x in good))!=32:
        raise ValueError("Observed unique scene pack/config count changed")
    if not TITLE_BY_PACK.keys() <= by_pack.keys():
        raise ValueError("One curated Japanese title lacks a completed actual screenshot")
    titles=[]
    for pack,title in TITLE_BY_PACK.items():
        e=by_pack[pack][0]
        titles.append({
            "kind":"runtime_onscreen_location_title_proof",
            "map_config_id":e["destination_config_id"],
            "runtime_pack_id_hex":pack,
            "onscreen_title":title,
            "presentation_kind":"in_game_location_overlay_after_controller_entrance",
            "source_transition_id":e["transition_id"],
            "source_world_cheat_positioned":True,
            "gamepad_event_to_destination_observed":True,
            "source_position":{"x":e["settled_arrival_xy"]["x"],"y":e["settled_arrival_xy"]["y"]},
            "screenshot_sha256":e["screenshot_sha256"],
            "screenshot_committed":False,
            "applies_to_all_configs_sharing_tileset_layout":False,
            "location_identity_confidence":"confirmed_onscreen_title_for_runtime_pack_context",
            "all_story_phases_location_identity_proven":False,
            "normal_world_route_proven":False,
        })
    titles.sort(key=lambda t:int(t["runtime_pack_id_hex"],16))
    new_titles=[t for t in titles if t["runtime_pack_id_hex"] not in ALREADY_PROVEN_PACKS]
    if len(titles)!=25 or len(new_titles)!=23:raise ValueError("Expected 25 place names and 23 newly scoped titles")
    for entry in good:
        pack=entry["destination_pack"]
        if pack in TITLE_BY_PACK:
            entry["inferred_onscreen_title"]=TITLE_BY_PACK[pack]
    result={
       "schema_version":1,
       "kind":"strict_37_world_scene_entrance_batch_replay_20261011",
       "source_map_config_id":WORLD_ID,
       "world_pack":WORLD_PACK,
       "base_analysis_state":"analysis_world_lv60_hien_20261011.State",
       "world_hien_spell_unlocked":True,
       "Hien_spell_cast_for_these_entries":False,
       "source_world_xy_cheat_positioned":True,
       "map_switch_triggered_by_real_controller":True,
       "normal_world_walking_routes_proven":False,
       "SNES_CPU_opcode_pc_observed":False,
       "all_story_states_accessible_proven":False,
       "total_attempted_hotspots":40,
       "successful_gamepad_world_to_ROM_pack":len(good),
       "failed_to_switch_this_local_attempt":len(bad),
       "unique_runtime_scene_packs":len(by_pack),
       "unique_runtime_map_configs":len(set(e["destination_config_id"] for e in good)),
       "distinct_onscreen_named_pack_contexts":len(titles),
       "new_onscreen_named_pack_contexts_for_viewer":len(new_titles),
       "no_raw_image_savestate_ROM_or_frame_json_committed":True,
       "underlying_emulator_restored_after_each_of_6_batches":True,
       "entries":good,
       "local_no_switch_observations":bad,
    }
    ENTRY_OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    PLACE_OUTPUT.write_text(json.dumps({
        "schema_version":1,
        "kind":"world_gamepad_entrances_visible_title_pack_scoped",
        "source_world_entrance_ledger":str(ENTRY_OUTPUT.relative_to(ROOT)).replace("\\","/"),
        "existing_two_individual_title_proofs_not_duplicated":sorted(ALREADY_PROVEN_PACKS),
        "all_25_onscreen_title_contexts":titles,
        "new_title_proofs":new_titles,
        "raw_screenshots_committed":False,
        "never_infer_from_equal_tilemap_layout":True,
    },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with CSV_PATH.open("r",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f);fields=reader.fieldnames;old=list(reader)
    for info in new_titles:
        cfg,pack=info["map_config_id"],info["runtime_pack_id_hex"]
        if any(r["config_id"]==cfg and r["pack_id_hex"]==pack for r in old):
            raise ValueError(f"Place CSV already has specific identity {cfg}@{pack}")
        old.append({
           "config_id":cfg,
           "pack_id_hex":pack,
           "candidate_label":info["onscreen_title"],
           "candidate_status":"confirmed_onscreen_pack_context",
           "runtime_identity_status":"world_hotspot_replay_onscreen_title_pack_specific",
           "internal_semantic_evidence":f'Actual destination screenshot SHA256={info["screenshot_sha256"]}; gamepad Up from cheat-positioned world nearby hotspot; pack={pack}.',
           "external_corroboration":f'Existing ROM source hotspot/pack/config entry {info["source_transition_id"]}; destination screenshot visibly renders the named title.',
           "limitation":"Name is specific to this scene pack and config; player world-start coordinate was set via analysis cheat; story conditions/NPC state/global tile layout names are unproven.",
           "promotion_rule":"Only name the exact selected runtime pack+config; never apply to all configs sharing one tileset or layout; CPU execution PC not captured.",
           "provenance":str(PLACE_OUTPUT.relative_to(ROOT)).replace("\\","/")+";"+str(ENTRY_OUTPUT.relative_to(ROOT)).replace("\\","/")
        })
    with CSV_PATH.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator="\n")
        writer.writeheader();writer.writerows(old)
    print(json.dumps({
        "attempted":40,"runtime_success":37,"runtime_distinct_packs":36,
        "runtime_distinct_configs":32,"named_exact_pack_contexts":25,
        "new_titles":23,"no_switch_observations":3,
        "previously_unknown_pack96_xy":next(x["settled_arrival_xy"] for x in good if x["destination_pack"]=="0x96"),
    },ensure_ascii=False))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--local-research-dir",type=Path,
        default=Path(r"C:\Users\zin\AppData\Local\shinmomo-bg-lab\research"))
    args=parser.parse_args()
    generate(args.local_research_dir)


if __name__=="__main__":main()
