"""Bind pack0x96 modal-cleared real Up exit to one saved-origin world context.

This is a screenshot+raw-frame witnessed runtime scene->world transition;
it does NOT prove the VM instruction PC or all story-state activation.
"""
from __future__ import annotations
from copy import deepcopy

EDGE_ID="runtime_pack96_modal_Up_world_20261011"
PROOF="data/maps/transitions/pack96_5way_modal_and_world_return_20261011.json"

def inject(candidates:list[dict],proof:dict,maps:list[dict]):
    if (proof.get("schema_version")!=1 or
        proof.get("kind")!="pack96_five_way_no_input_and_modal_unlocked_world_escape" or
        proof.get("source_world_transition_id")!="catalog_transition_0756" or
        proof.get("source_config_id")!="cfg_t09_l098_v2" or
        proof.get("source_pack")!="0x96" or
        proof.get("location_title_onscreen")!="音無しの洞窟" or
        proof.get("conditions")!=["Down","Up","Left","Right","None"] or
        proof.get("five_conditions_full_204_frame_position_identity") is not True or
        proof.get("identical_frame_count_each")!=204 or
        proof.get("same_frame_range")!=[663329,663532] or
        proof.get("real_left_right_gamepad_presses_observed") is not True or
        proof.get("neutral_no_buttons_test_observed") is not True or
        proof.get("end_of_automatic_descent_xy")!={"x":39,"y":24} or
        len(proof.get("descent_steps",[]))!=7 or
        [s.get("frame") for s in proof["descent_steps"]]!=[663333,663342,663351,663360,663369,663378,663387] or
        proof.get("title_modal_blocked_directional_movement") is not True or
        proof.get("no_button_then_right_72_blocked_verified") is not True or
        proof.get("A_then_right_72_walkable_verified") is not True or
        len(proof.get("no_button_right_traces_sha256",[]))!=2 or
        len(proof.get("A_then_right_traces_sha256",[]))!=3 or
        proof.get("A_press_then_Up_world_return_observed") is not True or
        proof.get("post_title_A_frames")!=8 or
        proof.get("post_title_neutral_frames")!=64 or
        proof.get("world_return_actual_gamepad_direction")!="Up" or
        proof.get("world_return_actual_gamepad_frames")!=96 or
        proof.get("pack_switch_frame")!=663807 or
        proof.get("temporary_world_pack_xy")!={"x":39,"y":7} or
        proof.get("world_arrival_first_stable_frame")!=663897 or
        proof.get("world_arrival_xy")!={"x":50,"y":129} or
        proof.get("world_pack")!="0x4C" or
        proof.get("world_config_id")!="cfg_t01_l001_v1" or
        proof.get("world_stable_through_frame")!=664216 or
        proof.get("world_raw_selector_converged") is not True or
        proof.get("source_world_entry_was_cheat_seeded") is not True or
        proof.get("scene_controller_probe_wram_xy_cheat_used") is not False or
        proof.get("world_arrival_for_other_savestates_proven") is not False or
        proof.get("all_story_phases_verified") is not False or
        proof.get("exact_CPU_instruction_PC_observed") is not False or
        proof.get("natural_world_entry_walkability_proven") is not False or
        proof.get("modal_causal_code_handler_proven") is not False or
        proof.get("source_exit_exact_hotspot_tile_proven") is not False or
        proof.get("raw_traces_screens_ROM_or_states_committed") is not False or
        len(proof.get("modal_escape_full_trace_sha256",[]))!=7 or
        set(proof.get("five_way_trace_sha256",{}))!={"Down","Up","Left","Right","None"}):
        raise ValueError("Pack96 source, modal, five conditions, or saved-world return proof is incomplete")
    for v in proof["modal_escape_full_trace_sha256"]:
        if not isinstance(v,str) or len(v)!=64:
            raise ValueError("Missing raw SHA256")
    configs={m["config_id"]:m for m in maps}
    source=configs.get("cfg_t09_l098_v2")
    world=configs.get("cfg_t01_l001_v1")
    if (not source or not world or
        (source.get("tileset_id"),source.get("layout_id"))!=(9,98) or
        (world.get("tileset_id"),world.get("layout_id"))!=(1,1)):
        raise ValueError("Wrong original source or world map")
    inbound=[c for c in candidates if c.get("transition_id")=="catalog_transition_0756"]
    if len(inbound)!=1:raise ValueError("Expected unique real world->pack96 initial scene")
    e=inbound[0]
    h=e.get("source_hotspot_binding") or {}
    if (e.get("source_config_id")!="cfg_t01_l001_v1" or
        e.get("destination_config_id")!="cfg_t09_l098_v2" or
        e.get("destination_pack")!="0x96" or
        (e.get("destination_x"),e.get("destination_y"))!=(39,17) or
        (h.get("source_grid_x"),h.get("source_grid_y"))!=(50,129) or
        e.get("runtime_world_entry_batch_probe",{}).get("actual_SNES_gamepad_triggered_event") is not True):
        raise ValueError("The initial world->cave runtime event no longer matches")
    if any(c.get("transition_id")==EDGE_ID for c in candidates):
        raise ValueError("Already attached pack96 world escape")
    out=deepcopy(candidates)
    out.append({
      "transition_id":EDGE_ID,
      "tier":"tier1_confirmed",
      "source_config_id":"cfg_t09_l098_v2",
      "source_pack":"0x96",
      "source_tileset":9,
      "source_layout":98,
      "script_pack":None,"script_record":None,"script_entry":None,
      "trigger_type":"runtime_pack96_modal_dismissed_return_to_saved_world",
      "trigger_addr":None,
      "source_hotspot_binding":None,
      "destination_pack":"0x4C",
      "destination_entry_id":None,
      "destination_config_id":"cfg_t01_l001_v1",
      "destination_tileset":1,
      "destination_layout":1,
      "destination_variant":1,
      "destination_x":50,"destination_y":129,
      "destination_coordinate_origin":"actual_gamepad_world_return_after_90frame_loading_phase_with_original_saved_world_origin",
      "destination_secondary_x":None,"destination_secondary_y":None,
      "destination_coordinate_addr":None,
      "confidence":"confirmed",
      "condition":"Scoped to an analysis-cheat-origin scene, title-dismissing A then Up; world return location depends on saved world origin; story gates unknown.",
      "evidence":"Five input modes including no-button identical 204 frames; A8+neutral64 unlock, Up96 real controller; pack switch663807, saved world position fix663897, stable through664216.",
      "provenance":PROOF,
      "runtime_pack96_modal_world_return_proof":{
         "source_reached_from_cheat_adjacent_world_entry":True,
         "source_normal_world_walkability_proven":False,
         "initial_pack96_xy":{"x":39,"y":17},
         "forced_direction_independent_204_frames":True,
         "title_modal_A_button_cleared":True,
         "no_button_right72_blocked":True,
         "A_then_right72_walkable":True,
         "actual_controller_exit_direction":"Up",
         "last_scoped_source_xy_before_transition":{"x":39,"y":7},
         "exact_trigger_tile_proven":False,
         "pack_switch_frame":663807,
         "temporary_world_xy_after_switch":{"x":39,"y":7},
         "first_world_saved_origin_xy_frame":663897,
         "world_arrival_xy_for_this_saved_context":{"x":50,"y":129},
         "stable_through_frame":664216,
         "other_saved_contexts_universal":False,
         "actual_CPU_instruction_PC_observed":False,
         "all_story_phases_proven":False,
         "raw_screenshots_committed":False,
         "proof":PROOF
      }
    })
    return out,{
       "new_verified_modal_world_return_edge_count":1,
       "source_config_id":"cfg_t09_l098_v2",
       "destination_config_id":"cfg_t01_l001_v1",
       "actual_world_arrival_xy":{"x":50,"y":129},
       "five_input_204_frame_identity":True,
       "actual_CPU_handler_PC_observed":False,
       "story_conditions_all_verified":False,
       "world_walkable_start_proven":False,
       "provenance":PROOF,
    }
