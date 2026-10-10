"""Attach independently audited runtime *movement* evidence to existing edges.

No source candidate is promoted to a proven CPU-opcode execution event.
No extra graph edges; strong_candidate and activation unknown remain.
"""
from __future__ import annotations
from copy import deepcopy


def apply_runtime_spatial_proofs(candidates:list[dict],proofs:list[dict]):
    out=deepcopy(candidates)
    audit=[]
    used=set()
    for proof in proofs:
        if (proof.get("kind")!="verified_spatial_event_map_transition" or
            proof.get("schema_version")!=1 or
            proof.get("runtime_map_movement_proven") is not True or
            proof.get("static_opcode_cpu_execution_proven") is not False or
            proof.get("new_graph_edges_promoted")!=0 or
            proof.get("raw_capture_committed") is not False):
            raise ValueError("Runtime evidence has unsupported confidence/provenance")
        transition=proof.get("existing_viewer_transition_id")
        if not transition or transition in used:
            raise ValueError("Missing or duplicate transition proof")
        used.add(transition)
        matches=[e for e in out if e.get("transition_id")==transition]
        if len(matches)!=1:
            raise ValueError("No unique existing edge ID for runtime proof")
        edge=matches[0]
        if (edge.get("source_config_id")!=proof.get("observed_source_config_id") or
            edge.get("destination_config_id")!=proof.get("destination_config_id") or
            edge.get("trigger_addr")!=proof.get("existing_static_opcode_address") or
            edge.get("confidence")!=proof.get("existing_graph_confidence_unchanged") or
            edge.get("destination_x")!=proof.get("settled_arrival",{}).get("x") or
            edge.get("destination_y")!=proof.get("settled_arrival",{}).get("y")):
            raise ValueError("Runtime proof does not match one static edge")
        if edge.get("runtime_spatial_proof"):
            raise ValueError("Existing edge already has a spatial proof")
        source=proof["confirmed_source_region"]
        if not isinstance(source,dict) or not all(
            type(source.get(k)) is int and source[k]>=0
            for k in ("x","y","width","height")):
            raise ValueError("Invalid confirmed source region")
        if source["width"]>8 or source["height"]>8 or source["width"]==0 or source["height"]==0:
            raise ValueError("Invalid confirmed source-region bounds")
        if proof["first_observed_source_contact_frame"]>=proof["pack_switch_frame"]:
            raise ValueError("No source contact before pack switch")
        if not (proof["pack_switch_frame"]<
                proof["first_selector_pair_convergence_frame"]<=
                proof["first_settled_arrival_frame"]):
            raise ValueError("Missing phased selector/coordinate convergence")
        edge["runtime_spatial_proof"]={
            "runtime_path_confirmed":True,
            "script_opcode_PC_observed":False,
            "source_hotspot_id":proof["source_hotspot_id"],
            "source_region":source,
            "pack_switch_frame":proof["pack_switch_frame"],
            "selectors_converged_frame":proof["first_selector_pair_convergence_frame"],
            "first_settled_arrival_frame":proof["first_settled_arrival_frame"],
            "settled_arrival":proof["settled_arrival"],
            "source_pack":proof["observed_source_pack"],
            "destination_pack":proof["destination_pack"],
            "story_conditions_proven":False,
            "confidence_tier_unchanged":True
        }
        audit.append({"transition_id":transition,
                      "source_config_id":edge["source_config_id"],
                      "destination_config_id":edge["destination_config_id"],
                      "switch_frame":proof["pack_switch_frame"]})
    return out,{"attached_count":len(audit),"attached":audit,"new_graph_edges":0}
