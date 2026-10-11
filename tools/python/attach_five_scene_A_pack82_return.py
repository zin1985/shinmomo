"""Attach five pack-scoped A interaction observations and one real pack82 scene return.

Do not infer precise exit tiles, globally traversable routes or other
story-state outcomes from the tested local saved-world context.
"""
from __future__ import annotations
from copy import deepcopy
PATH="data/maps/transitions/five_scene_modal_tests_and_pack82_world_return_20261011.json"
EDGE="runtime_pack82_dialogue12_Down_saved_world_20261011"
PACKS=("0xBD","0xB9","0xAB","0x82","0x60")
MOVING={"0xBD","0xB9","0xAB"}
DIRECTIONS={"Down","Up","Left","Right"}

def attach(maps:list[dict],candidates:list[dict],proof:dict):
    if (proof.get("schema_version")!=1 or
        proof.get("kind")!="five_original_world_entered_scene_A_interactions_and_pack82_saved_world_return" or
        proof.get("five_scene_pack_contexts")!=list(PACKS) or
        proof.get("five_scene_actual_A8_plus_four_direction_tests")!=5 or
        proof.get("total_real_direction_probes")!=20 or
        proof.get("dungeon_scene_packs_with_observed_local_movement")!=["0xBD","0xB9","0xAB"] or
        proof.get("two_village_scene_packs_still_stationary_after_one_A")!=["0x82","0x60"] or
        proof.get("village_twelve_A_dialogue_trials")!=["0x82","0x60"] or
        proof.get("village_pack82_saved_world_return_reproduced") is not True or
        proof.get("village_pack60_world_return_observed") is not False or
        proof.get("original_world_entry_cheat_positioned") is not True or
        proof.get("actual_scene_input_XY_coordinate_cheat_used") is not False or
        proof.get("actual_emulator_restored_after_all_local_trials") is not True or
        proof.get("no_globally_valid_story_route_or_exit_missing_claim") is not True or
        proof.get("raw_ROM_images_Wram_frames_savestates_committed") is not False or
        proof.get("new_contextual_saved_world_return_edges")!=1 or
        len(proof.get("scene_trials",[]))!=5 or
        len(proof.get("dialogue_sequences",[]))!=2):
        raise ValueError("Full five-scene evidence is incomplete or overclaimed")
    world={m["config_id"]:m for m in maps}
    if len(world)!=len(maps):raise ValueError("Duplicate map configuration")
    source_by_id={c["transition_id"]:c for c in candidates}
    if len(source_by_id)!=len(candidates) or EDGE in source_by_id:
        raise ValueError("Duplicate or previously attached contextual return")
    result_maps=deepcopy(maps)
    result_by_id={m["config_id"]:m for m in result_maps}
    for item in proof["scene_trials"]:
        pack=item["source_scene_pack"];cfg=item["source_scene_config_id"]
        incoming=source_by_id.get(item["original_world_transition_id"])
        map_=result_by_id.get(cfg)
        dr=item.get("directions",[])
        if (pack not in PACKS or not incoming or not map_ or
            incoming.get("source_config_id")!="cfg_t01_l001_v1" or
            incoming.get("destination_config_id")!=cfg or
            incoming.get("destination_pack")!=pack or
            incoming.get("destination_x")!=item["source_scene_arrival_xy"][0] or
            incoming.get("destination_y")!=item["source_scene_arrival_xy"][1] or
            incoming.get("runtime_world_entry_batch_probe",{}).get("actual_SNES_gamepad_triggered_event") is not True or
            item.get("source_world_entrance_cheat_seeded") is not True or
            item.get("actual_scene_probe_wram_xy_cheat_used") is not False or
            item.get("real_A8_followed_by_neutral64") is not True or
            item.get("scene_A_interaction_cause_of_walking_proven") is not False or
            item.get("all_story_states_reachable_proven") is not False or
            item.get("no_exit_other_stories_or_directions_proven") is not False or
            item.get("raw_images_traces_ROM_savestates_committed") is not False or
            not all(isinstance(item.get(k),str) and len(item[k])==64 for k in
                ("before_A_screenshot_sha256","after_A_screenshot_sha256",
                 "actual_A_trace_sha256","after_A_neutral_trace_sha256")) or
            len(dr)!=4 or {d.get("direction") for d in dr}!=DIRECTIONS or
            not all(d.get("did_not_switch_pack_in_this_probe") is True and
                    d.get("input_frames")==96 and d.get("neutral_frames")==120 and
                    len(d.get("real_gamepad_trace_sha256",""))==64 and
                    len(d.get("neutral_trace_sha256",""))==64 and
                    len(d.get("screenshot_sha256",""))==64 for d in dr)):
            raise ValueError(f"Unverified exact source scene or A directional input: {pack}")
        if pack in MOVING:
            if not any(d["after_neutral_xy"]!=item["source_scene_arrival_xy"] for d in dr):
                raise ValueError("Dungeon interaction lacks observed movement")
        else:
            if any(d["after_neutral_xy"]!=item["source_scene_arrival_xy"] for d in dr):
                raise ValueError("Village claimed immobile but changed coordinates")
        context={
          "source_pack":pack,"source_transition_id":incoming["transition_id"],
          "original_world_entry_cheat_seeded":True,
          "real_SNES_A8_neutral64_before_directional_probes":True,
          "A_input_caused_walking_unlock_proven":False,
          "directions":[{"direction":d["direction"],
                         "local_post_A_xy":d["after_neutral_xy"],
                         "scene_pack_switch_in_local_probe":False} for d in dr],
          "all_story_phases_and_exits_proven":False,
          "source":PATH,
        }
        extras=map_.setdefault("runtime_five_scene_A_directional_contexts",[])
        if any(x["source_pack"]==pack for x in extras):
            raise ValueError("Duplicate runtime pack-scoped A investigation")
        extras.append(context)
    if len({item["source_scene_pack"] for item in proof["scene_trials"]})!=5:
        raise ValueError("Five separate scene packs are needed")
    by_dialogue={d.get("pack"):d for d in proof["dialogue_sequences"]}
    if set(by_dialogue)!={"0x82","0x60"}:raise ValueError("Missing village dialogue branches")
    for pack in by_dialogue:
        d=by_dialogue[pack]
        if (d.get("actual_A_button_presses")!=12 or
            d.get("per_press_held_frames")!=8 or
            d.get("neutral_frames_between_presses")!=20 or
            d.get("scene_xy_unchanged_during_all_twelve_A_presses") is not True or
            d.get("followup_controller")!="Down" or
            d.get("followup_frames")!=96 or
            d.get("followup_neutral_frames")!=120 or
            d.get("normal_world_entry_walkability_proven") is not False or
            d.get("universal_story_state_proven") is not False or
            len(d.get("per_step",[]))!=14):
            raise ValueError("Dialogue blocked route lacks twelve original A interactions")
    if (by_dialogue["0x60"]["followup_destination_pack"]!="0x60" or
        by_dialogue["0x60"]["followup_destination_xy"]!=[37,56] or
        by_dialogue["0x82"]["followup_destination_pack"]!="0x4C" or
        by_dialogue["0x82"]["followup_destination_xy"]!=[175,189]):
        raise ValueError("Village 60 or 82 return result contradicted")
    ret=proof.get("pack82_confirmed_world_return") or {}
    inbound=source_by_id.get("catalog_transition_0791")
    world_map=result_by_id.get("cfg_t01_l001_v1")
    source=result_by_id.get("cfg_t04_l059_v2")
    if (not inbound or not source or not world_map or
        inbound.get("destination_pack")!="0x82" or
        inbound.get("destination_config_id")!="cfg_t04_l059_v2" or
        [inbound.get("destination_x"),inbound.get("destination_y")]!=[40,59] or
        (inbound.get("source_hotspot_binding") or {}).get("source_grid_x")!=175 or
        (inbound.get("source_hotspot_binding") or {}).get("source_grid_y")!=189 or
        ret.get("source_pack")!="0x82" or
        ret.get("source_config_id")!="cfg_t04_l059_v2" or
        ret.get("source_world_transition_id")!="catalog_transition_0791" or
        ret.get("original_scene_spawn_xy")!={"x":40,"y":59} or
        ret.get("dialogue_A_presses_before_exit")!=12 or
        ret.get("actual_world_return_input")!="Down" or
        ret.get("world_switch_frame")!=663683 or
        ret.get("world_destination_pack")!="0x4C" or
        ret.get("world_destination_config_id")!="cfg_t01_l001_v1" or
        ret.get("world_destination_xy_for_original_saved_world_context")!={"x":175,"y":189} or
        ret.get("world_arrival_stable_neutral_frames")!=360 or
        ret.get("last_observed_world_frame")!=664132 or
        ret.get("native_handler_CPU_PC_proven") is not False or
        ret.get("world_destination_other_saves_universal") is not False or
        ret.get("source_exact_exit_hotspot_proven") is not False or
        ret.get("source_entrance_originally_cheat_seeded") is not True or
        ret.get("return_gamepad_xy_coordinate_cheated") is not False or
        ret.get("raw_screenshots_frames_states_or_ROM_committed") is not False or
        len(ret.get("raw_frame_sha256",[]))!=4 or
        len(ret.get("screenshot_sha256",[]))!=4):
        raise ValueError("Exact pack82 saved-origin real world exit evidence mismatch")
    result_edges=deepcopy(candidates)
    result_edges.append({
      "transition_id":EDGE,"tier":"tier1_confirmed",
      "source_config_id":"cfg_t04_l059_v2","source_pack":"0x82",
      "source_layout":source["layout_id"],"source_tileset":source["tileset_id"],
      "script_pack":None,"script_record":None,"script_entry":None,
      "trigger_type":"runtime_village_dialogue12_then_Down_saved_world",
      "trigger_addr":None,"source_hotspot_binding":None,
      "destination_pack":"0x4C","destination_entry_id":None,
      "destination_config_id":"cfg_t01_l001_v1",
      "destination_tileset":1,"destination_layout":1,"destination_variant":1,
      "destination_x":175,"destination_y":189,
      "destination_secondary_x":None,"destination_secondary_y":None,
      "destination_coordinate_addr":None,
      "destination_coordinate_origin":"real_world_return_after_twelve_dialogue_A_presses_in_cheat_seeded_saved_context",
      "confidence":"confirmed",
      "condition":"Exactly this local scene/game state after 12 A dialogue presses then real Down96. World saved-origin coordinate; unknown other story states.",
      "evidence":"12 real A presses+neutral20 each, real Down96, world pack0x4C at frame663683, 360 neutral frames stable (175,189); raw SHA256 hashes.",
      "provenance":PATH,
      "runtime_pack82_dialogue_saved_world_return_proof":{
         "observed_runtime_map_switch":True,
         "original_world_entrance_cheat_seeded":True,
         "reverse_gamepad_coordinate_cheat_used":False,
         "dialogue_A_press_count":12,
         "return_SNES_gamepad_direction":"Down",
         "world_switch_frame":663683,
         "world_arrival_xy_in_this_saved_context":{"x":175,"y":189},
         "stable_neutral_frame_count":360,
         "world_destination_in_other_saves_verified":False,
         "exact_source_event_trigger_tile_proven":False,
         "CPU_handler_PC_observed":False,
         "story_activation_gates_proven":False,
         "normal_world_access_proven":False,
         "evidence":PATH
      }
    })
    return result_maps,result_edges,{
      "scenes_replayed_after_real_A":5,
      "actual_directional_scene_trials":20,
      "dungeon_packs_with_local_movement":3,
      "village_dialogue_sequences_tested":2,
      "new_verified_pack82_world_return_edges":1,
      "unresolved_pack60_return":True,
      "all_story_gates_proven":False,
      "native_CPU_handler_PC_proven":False,
      "provenance":PATH,
    }
