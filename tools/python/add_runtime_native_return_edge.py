"""Add a uniquely proven pack4D -> world native exit as ONE new graph edge.

This proof is a saved-map-return state observation, not a VM opcode
execution trace. Fail closed on conflicting preexisting graph records.
"""
from __future__ import annotations
from copy import deepcopy

EDGE_ID="runtime_native_pack4d_south_return_20261011"
PROOF_PATH="data/maps/transitions/pack4d_south_native_return_20261011.json"


def inject(candidates:list[dict], proof:dict)->tuple[list[dict],dict]:
    if (proof.get("kind")!="verified_native_boundary_return_new_edge" or
        proof.get("schema_version")!=1 or
        proof.get("source_config_id")!="cfg_t04_l006_v2" or
        proof.get("destination_config_id")!="cfg_t01_l001_v1" or
        proof.get("source_pack")!="0x4D" or proof.get("destination_pack")!="0x4C" or
        proof.get("confirmed_source_inside_cell")!={"x":17,"y":37} or
        proof.get("first_outside_cell")!={"x":17,"y":38} or
        proof.get("settled_arrival")!={"x":52,"y":233} or
        proof.get("first_outside_frame")!=663382 or proof.get("switch_frame")!=663387 or
        proof.get("selector_convergence_frame")!=663414 or
        proof.get("CPU_handler_PC_observed") is not False or
        proof.get("VM_opcode_56_executed_proven") is not False or
        proof.get("all_story_states_navigable_proven") is not False or
        proof.get("full_south_exit_width_proven") is not False or
        proof.get("raw_traces_committed") is not False or
        proof.get("return_mechanism")!="native_bounds_saved_map_restore_runtime_consistent" or
        proof.get("native_bounds")!={"x_min":1,"x_max":46,"y_min":1,"y_max":37}):
        raise ValueError("Unsupported/ambiguous native return proof")
    if any(e.get("transition_id")==EDGE_ID or
           (e.get("source_config_id")=="cfg_t04_l006_v2" and e.get("destination_config_id")=="cfg_t01_l001_v1")
           for e in candidates):
        raise ValueError("Native return would duplicate an existing transition")
    if not any(e.get("transition_id")=="catalog_transition_0746" and
               e.get("source_config_id")=="cfg_t01_l001_v1" and
               e.get("destination_config_id")=="cfg_t04_l006_v2" and
               e.get("runtime_spatial_proof",{}).get("runtime_path_confirmed") is True
               for e in candidates):
        raise ValueError("Independent world->pack4D entry edge missing")
    edge={
        "transition_id":EDGE_ID,
        "tier":"tier1_confirmed",
        "source_config_id":"cfg_t04_l006_v2",
        "source_pack":"0x4D",
        "source_layout":6,
        "source_tileset":4,
        "script_pack":None,
        "script_record":None,
        "script_entry":None,
        "trigger_type":"native_out_of_bounds_saved_map_return",
        "trigger_addr":None,
        "source_hotspot_binding":None,
        "event_record":None,
        "vm_context":None,
        "event_sources":None,
        "destination_pack":"0x4C",
        "destination_entry_id":None,
        "destination_config_id":"cfg_t01_l001_v1",
        "destination_layout":1,
        "destination_tileset":1,
        "destination_variant":1,
        "destination_x":52,
        "destination_y":233,
        "destination_secondary_x":None,
        "destination_secondary_y":None,
        "destination_coordinate_addr":None,
        "condition":"Requires source position x17,y37 and compatible saved-map return stack; other story states not verified",
        "confidence":"confirmed",
        "evidence":"Exact frame-end WRAM native crossing x17,y38, pack 4D->4C, stable world (52,233), independent ROM native bounds 1..37",
        "provenance":PROOF_PATH,
        "native_boundary_context":{
            "runtime_edge_status":"observed",
            "handler_CPU_PC_observed":False,
            "current_state_evaluation":"unknown_without_saved_state_and_position",
            "source_region":{"x":17,"y":37,"width":1,"height":1,
                             "evidence_status":"confirmed_exact_cell"},
            "first_outside_cell":{"x":17,"y":38},
            "confirmed_saved_map_return_target":{"x":52,"y":233},
            "static_bounds_opcode_addr":proof["native_bounds_opcode_address"],
            "crossing_frame":proof["first_outside_frame"],
            "map_switch_frame":proof["switch_frame"],
            "raw_selector_convergence_frame":proof["selector_convergence_frame"],
            "full_exit_width_verified":False,
            "saved_state_predicate_decoded":False,
        }
    }
    result=deepcopy(candidates)
    result.append(edge)
    return result,{"new_runtime_native_bound_edge_count":1,"edge_id":EDGE_ID,
                   "source_config_id":edge["source_config_id"],
                   "destination_config_id":edge["destination_config_id"],
                   "source_cell":{"x":17,"y":37},
                   "arrival":{"x":52,"y":233},
                   "cpu_handler_proven":False}
