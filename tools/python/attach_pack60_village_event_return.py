"""Inject strict contextual pack60 after story-scene world return, not universal route."""
from __future__ import annotations
from copy import deepcopy

PATH="data/maps/transitions/pack60_dialogue_phase_world_return_20261011.json"
EDGE_ID="runtime_pack60_A36_event_Down_saved_world_20261011"

def attach(maps:list[dict],candidates:list[dict],p:dict):
    if (p.get("schema_version")!=1 or
        p.get("kind")!="pack60_36_dialogue_A_scene_visual_change_then_real_world_return" or
        p.get("source_world_transition_id")!="catalog_transition_0755" or
        p.get("source_config_id")!="cfg_t04_l035_v2" or
        p.get("source_pack")!="0x60" or
        p.get("source_arrival_xy")!={"x":37,"y":56} or
        p.get("original_world_entry_cheat_seeded") is not True or
        p.get("scene_controller_XY_coordinate_cheat_used") is not False or
        p.get("exact_story_gates_proven") is not False or
        p.get("dialogue_event_cpu_handler_pc_observed") is not False or
        p.get("A_presses_in_initial_village_study")!=12 or
        p.get("additional_A_presses_in_extension")!=24 or
        p.get("all_real_SNES_A_presses")!=36 or
        p.get("A_held_frames_each")!=8 or p.get("A_neutral_frames_each")!=20 or
        len(p.get("recorded_A_screen_phases",[]))!=24 or
        p.get("A17_to_A21_additional_black_screenshot_identical") is not True or
        p.get("visual_transformation_described_from_local_screenshots")!="pink_flowery_village_to_brown_withered_vegetation" or
        p.get("exact_visual_event_trigger_A_count_proven") is not False or
        p.get("return_after_A36_controller")!="Down" or
        p.get("return_after_A36_controller_frames")!=96 or
        p.get("return_world_pack")!="0x4C" or
        p.get("return_world_config_id")!="cfg_t01_l001_v1" or
        p.get("return_world_xy_this_saved_context")!={"x":59,"y":155} or
        p.get("world_scene_switch_frame")!=664366 or
        p.get("world_stable_neutral_frames")!=360 or
        p.get("return_destination_for_other_saves_proven") is not False or
        p.get("source_exact_return_trigger_cell_proven") is not False or
        p.get("original_world_access_without_cheat_proven") is not False or
        p.get("runtime_source_emulator_restored_after_probes") is not True or
        p.get("raw_ROM_screenshots_traces_savestates_committed") is not False or
        len(p.get("long_return_frame_sha256",[]))!=4 or
        len(p.get("long_return_screen_sha256",[]))!=4 or
        any(not isinstance(x,str) or len(x)!=64 for x in p["long_return_frame_sha256"])):
        raise ValueError("Pack60 scene / saved-world proof is incomplete or overclaimed")
    actual=p.get("after_A36_four_direction_real_controller_results") or {}
    expected={"Down":("0x4C",{"x":59,"y":155}),
              "Up":("0x60",{"x":37,"y":40}),
              "Left":("0x60",{"x":36,"y":56}),
              "Right":("0x60",{"x":38,"y":56})}
    if set(actual)!=set(expected):
        raise ValueError("Missing four genuine directions")
    for key,(pack,xy) in expected.items():
        item=actual[key]
        if (item.get("scene_pack_after")!=pack or
            item.get("xy")!=[xy["x"],xy["y"]] or
            any(not isinstance(item.get(f),str) or len(item[f])!=64
                for f in ("controller_sha256","neutral_sha256"))):
            raise ValueError("Forged directional results")
    m_by_id={m["config_id"]:m for m in maps}
    if len(m_by_id)!=len(maps):raise ValueError("Duplicate configs")
    scene=m_by_id.get("cfg_t04_l035_v2");world=m_by_id.get("cfg_t01_l001_v1")
    by_id={e["transition_id"]:e for e in candidates}
    if len(by_id)!=len(candidates) or EDGE_ID in by_id:
        raise ValueError("Duplicate pack60 return")
    initial=by_id.get("catalog_transition_0755")
    h=(initial or {}).get("source_hotspot_binding") or {}
    if (not scene or not world or
        (scene.get("tileset_id"),scene.get("layout_id"))!=(4,35) or
        (world.get("tileset_id"),world.get("layout_id"))!=(1,1) or
        initial.get("source_config_id")!="cfg_t01_l001_v1" or
        initial.get("destination_config_id")!="cfg_t04_l035_v2" or
        initial.get("destination_pack")!="0x60" or
        [initial.get("destination_x"),initial.get("destination_y")]!=[37,56] or
        [h.get("source_grid_x"),h.get("source_grid_y")]!=[59,155] or
        (initial.get("runtime_world_entry_batch_probe") or {}).get("actual_SNES_gamepad_triggered_event") is not True):
        raise ValueError("Pack60 world entry ROM/X/Y or runtime evidence mismatch")
    copied=deepcopy(maps)
    cm=next(m for m in copied if m["config_id"]=="cfg_t04_l035_v2")
    context={
      "source_pack":"0x60",
      "original_world_transition_id":"catalog_transition_0755",
      "original_world_to_scene_cheat_adjacent":True,
      "no_XY_cheat_during_dialogue_or_exit":True,
      "sequence_A12_plus_A24_in_this_save_state":True,
      "onscreen_pink_flowers_to_brown_withered_village":True,
      "black_transition_screenshot_sha256":p["black_screenshot_sha256"],
      "before_village_screenshot_sha256":p["original_pre_event_screenshot_sha256"],
      "after_village_screenshot_sha256":p["transformed_village_onscreen_sha256"],
      "event_exact_minimal_A_count_proven":False,
      "story_gates_unknown":True,
      "provenance":PATH,
    }
    if any(x.get("source_pack")=="0x60" for x in cm.get("runtime_pack60_village_visual_event_contexts",[])):
        raise ValueError("Pack60 context already attached")
    cm.setdefault("runtime_pack60_village_visual_event_contexts",[]).append(context)
    edges=deepcopy(candidates)
    edges.append({
      "transition_id":EDGE_ID,"tier":"tier1_confirmed",
      "source_config_id":"cfg_t04_l035_v2",
      "source_pack":"0x60","source_tileset":4,"source_layout":35,
      "script_pack":None,"script_record":None,"script_entry":None,
      "trigger_type":"runtime_pack60_after_dialogue_visual_event_real_Down_saved_world",
      "trigger_addr":None,"source_hotspot_binding":None,
      "destination_pack":"0x4C","destination_entry_id":None,
      "destination_config_id":"cfg_t01_l001_v1",
      "destination_tileset":1,"destination_layout":1,"destination_variant":1,
      "destination_x":59,"destination_y":155,
      "destination_secondary_x":None,"destination_secondary_y":None,
      "destination_coordinate_addr":None,
      "confidence":"confirmed",
      "condition":"This saved phase after 36 observed A presses and a visual village transformation; universal story gates unknown.",
      "evidence":"24 additional contiguous A8/neutral20 screenshot+WRAM captures after earlier 12, real Down96 pack0x60->world0x4C frame664366, neutral360 XY stable.",
      "provenance":PATH,
      "runtime_pack60_village_phase_world_return_proof":{
          "observed_runtime_map_switch":True,
          "original_world_entrance_cheat_seeded":True,
          "scene_return_controller_coordinate_cheat_used":False,
          "observed_screen_visual_change":True,
          "actual_A_presses_in_test":36,
          "exact_minimum_A_count_to_exit_proven":False,
          "return_SNES_controller_button":"Down",
          "world_switch_frame":p["world_scene_switch_frame"],
          "return_world_xy_this_saved_context":{"x":59,"y":155},
          "world_stable_neutral_frames":360,
          "world_destination_other_saves_verified":False,
          "exact_source_trigger_cell_proven":False,
          "CPU_handler_PC_observed":False,
          "story_activation_gates_proven":False,
          "normal_world_access_proven":False,
          "provenance":PATH,
      }
    })
    return copied,edges,{
      "new_verified_pack60_saved_world_return":1,
      "confirmed_visual_transformation_in_one_scene_state":True,
      "other_saves_or_story_gates_proven":False,
      "event_exact_cpu_pc_observed":False,
      "event_minimal_A_presses_proven":False,
      "provenance":PATH,
    }
