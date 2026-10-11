"""Pack-scoped failed-escape observations; no invented map transitions."""
from __future__ import annotations
from copy import deepcopy

UP_SOURCE="data/maps/transitions/six_scene_up_no_pack_switch_20261011.json"
FORCED_SOURCE="data/maps/transitions/pack96_up_down_identical_forced_movement_20261011.json"
EXPECTED={"0x96","0xBD","0xB9","0xAB","0x82","0x60"}

def attach(maps:list[dict],up:dict,down:dict,pack96:dict):
    if (up.get("schema_version")!=1 or
        up.get("kind")!="six_protected_up_direction_dungeon_and_village_no_switch_observations" or
        up.get("previous_down_trial_proof")!="data/maps/transitions/world_14_reverse_returns_after_cheat_arrivals_20261011.json" or
        up.get("all_original_hidden_emulator_states_restored") is not True or
        up.get("original_world_to_scene_entry_cheat_positioned") is not True or
        up.get("Up_trial_no_coordinate_cheat") is not True or
        up.get("each_trial_duration_input_plus_neutral_frames")!=192 or
        up.get("six_observed_no_scene_switch") is not True or
        up.get("universal_no_exit_claim") is not False or
        up.get("raw_samples_ROM_states_screens_not_committed") is not True or
        len(up.get("probes",[]))!=6 or
        set(up.get("six_exact_scopes",[]))!=EXPECTED or
        down.get("confirmed_world_returns")!=14 or
        down.get("local_nonreturns")!=6 or
        len(down.get("unconfirmed_local_direction_returns",[]))!=6):
        raise ValueError("Incomplete six-scene local direction audit")
    if (pack96.get("schema_version")!=1 or
        pack96.get("kind")!="pack96_input_direction_independent_downward_movement_local_state" or
        pack96.get("source_config_id")!="cfg_t09_l098_v2" or
        pack96.get("pack")!="0x96" or
        pack96.get("compared_actual_buttons")!=["Down","Up"] or
        pack96.get("same_game_frame_range")!=[663329,663532] or
        pack96.get("both_direction_position_series_identical_frame_count")!=204 or
        pack96.get("downward_every_nine_frames") is not True or
        pack96.get("same_pack_during_entire_span") is not True or
        pack96.get("controller_path_no_xy_cheat") is not True or
        pack96.get("actual_CPU_opcode_PC_proven") is not False or
        pack96.get("generalizes_to_other_savestates") is not False or
        pack96.get("root_cause_interpretation")!="scripted_forced_walk_or_physics_unresolved" or
        pack96.get("raw_frame_traces_committed") is not False or
        pack96.get("last_xy")!={"x":39,"y":24} or
        len(pack96.get("observed_positions",[]))!=7):
        raise ValueError("Pack0x96 directional force movement lacks exact independent proof")
    prev={p["source_scene_pack"]:p for p in down["unconfirmed_local_direction_returns"]}
    if set(prev)!=EXPECTED:raise ValueError("The six originally unconfirmed Down scenes changed")
    seen=set()
    out=deepcopy(maps)
    by_id={m["config_id"]:m for m in out}
    if len(by_id)!=len(out):raise ValueError("Duplicate structural map configs")
    for item in up["probes"]:
        pack=item["source_pack"]
        if pack in seen or pack not in EXPECTED or pack not in prev:
            raise ValueError("Duplicate or nonmatching Up-negative scene")
        seen.add(pack)
        d=prev[pack]
        cfg=item["source_config_id"]
        m=by_id.get(cfg)
        spawn=item.get("source_scene_original_arrival_xy")
        if (not m or cfg!=d["source_config_id"] or
            not isinstance(spawn,list) or len(spawn)!=2 or
            spawn!=[d["scene_spawn_xy"]["x"],d["scene_spawn_xy"]["y"]] or
            item.get("original_world_transition_id")!=d["source_world_transition_id"] or
            item.get("controller")!="Up" or
            item.get("controller_frames")!=72 or
            item.get("neutral_frames")!=120 or
            item.get("no_pack_switch_in_observation") is not True or
            item.get("reverse_experiment_controller_has_no_cheat") is not True or
            item.get("other_direction_or_story_state_exits_proven_absent") is not False or
            item.get("source_original_world_approach_cheat") is not True or
            item.get("raw_frame_capture_committed") is not False or
            len(item.get("trace_sha256",[]))!=3 or
            not all(isinstance(x,str) and len(x)==64 for x in item["trace_sha256"])):
            raise ValueError("Incomplete exact scene+pack scoped negative Up controller trial")
        profile={
           "source_pack":pack,
           "scope":"this_runtime_pack_and_save_state_only",
           "original_world_entrance_cheat_seeded":True,
           "real_SNES_gamepad_steps_tested":["Down","Up"],
           "input_frames_each_direction":72,
           "local_down_no_map_switch":True,
           "local_up_no_map_switch":True,
           "other_stories_or_directions_excluded":False,
           "source_config_id":cfg,
           "original_scene_spawn_xy":{"x":spawn[0],"y":spawn[1]},
           "down_final_xy":d["source_after_probe_xy"],
           "up_final_xy":item["scene_final_xy_after_neutral"],
           "up_provenance":UP_SOURCE,
           "down_provenance":"data/maps/transitions/world_14_reverse_returns_after_cheat_arrivals_20261011.json"
        }
        if pack=="0x96":
            profile["controller_direction_independent_movement"]={
                "position_trace_identical_frame_count":204,
                "forced_path_from":{"x":39,"y":17},
                "forced_path_to":{"x":39,"y":24},
                "step_frames":[p["frame"] for p in pack96["observed_positions"]],
                "specific_native_handler_unknown":True,
                "source":FORCED_SOURCE
            }
        contexts=m.setdefault("runtime_scene_directional_probe_contexts",[])
        if any(x["source_pack"]==pack for x in contexts):
            raise ValueError("Duplicate local scene+pack directional probe")
        contexts.append(profile)
    if seen!=EXPECTED:raise ValueError("Six local scene probes weren't all attached")
    return out,{
       "up_local_trials_without_switch":6,
       "both_up_down_local_nonreturn_scene_count":6,
       "pack96_identical_directional_motion_frames":204,
       "world_transition_edges_created":0,
       "all_story_states_blocked_proven":False,
       "sources":[UP_SOURCE,FORCED_SOURCE]
    }
