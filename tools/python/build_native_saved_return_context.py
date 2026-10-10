#!/usr/bin/env python3
"""Context-safe native saved-return evidence for event-aware map viewer.

The two occurrences of C1:8955 are *not* separate opcode-address identities:
the same native handler restores different saved maps depending on source
map, movement boundary and saved-state stack. Never match by handler alone.
"""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOTSPOTS = ROOT / "data/maps/transitions/source_transition_hotspots.csv"
ORIGINS = ROOT / "data/maps/transitions/source_saved_return_origins.csv"

def rows(path: Path) -> list[dict[str,str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def _integer(text):
    try:
        return int(text)
    except (ValueError, TypeError):
        return None

def match_native_boundaries(
    edges: list[dict],
    hotspots: list[dict[str,str]],
    origins: list[dict[str,str]],
):
    """Enrich unique runtime edges; retain provenance and unresolved corridor flags.

    Never create duplicate edges, never promote confidence, and never assign
    a single fixed return target to an otherwise ambiguous shared handler.
    Return (new edges, diagnostics) without mutating inputs.
    """
    result = [dict(e) for e in edges]
    index = defaultdict(list)
    for i,e in enumerate(result):
        if e.get("source_config_id") and e.get("destination_config_id"):
            index[(e["source_config_id"], e["destination_config_id"])].append(i)
    native = [
        h for h in hotspots
        if h.get("trigger_type") == "native_out_of_bounds_saved_state_restore"
    ]
    attached = []
    rejected = []
    used = set()
    for h in native:
        hid = h.get("hotspot_id") or ""
        key = (h.get("source_config_id"), h.get("destination_config_id"))
        matches = index.get(key, [])
        if len(matches) != 1:
            rejected.append({"hotspot_id":hid, "reason":"missing_or_ambiguous_source_destination_edge"})
            continue
        edge_index = matches[0]
        if edge_index in used or result[edge_index].get("source_hotspot_binding"):
            rejected.append({"hotspot_id":hid, "reason":"duplicate_or_vm_hotspot_occupied"})
            continue
        edge = result[edge_index]
        if not edge.get("trigger_type") in (
            "runtime_observed_map_transition", "runtime_saved_map_state_restore_transition"
        ):
            rejected.append({"hotspot_id":hid,"reason":"not_a_runtime_return_edge"})
            continue
        matched_origins = [
            r for r in origins
            if r.get("entered_destination_config_id") == key[0]
            and r.get("saved_return_config_id") == key[1]
        ]
        if len(matched_origins) != 1:
            rejected.append({"hotspot_id":hid, "reason":"missing_or_ambiguous_saved_return_origin"})
            continue
        origin = matched_origins[0]
        x,y = _integer(h.get("destination_x")),_integer(h.get("destination_y"))
        xmin,ymin = _integer(origin.get("saved_return_x_min")),_integer(origin.get("saved_return_y_min"))
        xmax,ymax = _integer(origin.get("saved_return_x_max")),_integer(origin.get("saved_return_y_max"))
        sx,sy = _integer(h.get("source_grid_x")),_integer(h.get("source_grid_y"))
        sw,sh = _integer(h.get("source_width")),_integer(h.get("source_height"))
        if None in (x,y,xmin,ymin,xmax,ymax,sx,sy,sw,sh) or not (xmin<=x<=xmax and ymin<=y<=ymax) or sw<1 or sh<1:
            rejected.append({"hotspot_id":hid, "reason":"invalid_or_unbacked_source_or_return_coordinate"})
            continue
        # A source region inferred from a rendered floor opening is not a
        # runtime-proven full corridor just because reverse traversal occurred.
        exact_source_confirmed = (
            h.get("confidence") == "confirmed_runtime_and_static"
            and "candidate" not in (h.get("hotspot_type") or "")
            and sw == 1 and sh == 1
        )
        ctx = {
            "hotspot_id":hid,
            "handler_addr":h["trigger_addr"],
            "mechanism":"native_out_of_bounds_saved_state_restore",
            "source_map_config_id":key[0],
            "source_region":{"x":sx,"y":sy,"width":sw,"height":sh,
                             "evidence_status":"confirmed_exact_cell" if exact_source_confirmed else "candidate_corridor_not_all_cells_verified"},
            "saved_return_origin_hotspot_id":origin["origin_hotspot_id"],
            "saved_return_target_config_id":key[1],
            "saved_return_target":{"x":x,"y":y},
            "saved_return_source_rectangle":{
                "x_min":xmin,"y_min":ymin,"x_max":xmax,"y_max":ymax
            },
            "saved_return_evidence_status":origin.get("reverse_runtime_status") or "static_saved_return_context",
            "runtime_edge_status":"observed" if edge.get("confidence")=="confirmed" else "candidate",
            "current_state_evaluation":"unknown_without_saved_state_and_position",
            "evidence":h.get("evidence") or "",
            "provenance":(h.get("provenance") or "")+";"+(origin.get("provenance") or ""),
        }
        if edge.get("destination_x") is not None and int(edge["destination_x"])!=x:
            rejected.append({"hotspot_id":hid, "reason":"existing_arrival_x_conflict"})
            continue
        if edge.get("destination_y") is not None and int(edge["destination_y"])!=y:
            rejected.append({"hotspot_id":hid, "reason":"existing_arrival_y_conflict"})
            continue
        edge["native_boundary_context"] = ctx
        # Do not change original candidate confidence or source/dest pack.
        used.add(edge_index)
        attached.append({"hotspot_id":hid, "transition_id":edge["transition_id"],
                         "source_region_status":ctx["source_region"]["evidence_status"]})
    return result, {"native_hotspot_count":len(native), "attached_count":len(attached),
                    "attached":attached, "rejected":rejected}



def attach_confirmed_return_variants(edges: list[dict], proof: dict) -> tuple[list[dict], dict]:
    """Annotate one native edge with exactly proven coordinate-pair variants.

    This NEVER changes the graph's representative arrival, confidence,
    or navigable_now. A coordinate offset extrapolation is NOT inferred.
    """
    if proof.get("kind") != "verified_coordinate_sensitive_village_world_roundtrip":
        raise ValueError("Wrong native coordinate variant evidence")
    src=proof["village_to_world"]["source_config_id"]
    dst=proof["village_to_world"]["destination_config_id"]
    variants=proof["position_dependent_native_return"]["confirmed_coordinate_pairs"]
    if not isinstance(variants,list) or len(variants)<2:
        raise ValueError("At least two independently proven coordinate pairs required")
    if proof["position_dependent_native_return"]["general_coordinate_transform_proven"] is not False:
        raise ValueError("General coordinate transform is not independently proven")
    targets=[i for i,e in enumerate(edges) if
             e.get("source_config_id")==src and e.get("destination_config_id")==dst
             and e.get("native_boundary_context")]
    if len(targets)!=1:
        raise ValueError("No unique native saved-return context for coordinate variants")
    idx=targets[0]
    original=edges[idx]
    ctx=original["native_boundary_context"]
    if (ctx.get("source_region",{}).get("evidence_status")!="confirmed_exact_cell" or
        ctx.get("current_state_evaluation")!="unknown_without_saved_state_and_position"):
        raise ValueError("Native return edge source/context not independently proven")
    bound=ctx["saved_return_source_rectangle"]
    representative=(ctx["source_region"]["x"],ctx["source_region"]["y"],
                    original["destination_x"],original["destination_y"])
    seen_src=set()
    normalized=[]
    representative_count=0
    for variant in variants:
        spot=variant["source_village_cell"]
        arrival=variant["world_arrival"]
        x,y,dx,dy=spot["x"],spot["y"],arrival["x"],arrival["y"]
        if not all(type(v) is int for v in (x,y,dx,dy)):
            raise ValueError("Non-integer coordinate in native variant")
        if (x,y) in seen_src or not (bound["x_min"]<=dx<=bound["x_max"]
                                  and bound["y_min"]<=dy<=bound["y_max"]):
            raise ValueError("Duplicate/invalid native source or return coordinate")
        seen_src.add((x,y))
        representative_count+=int((x,y,dx,dy)==representative)
        normalized.append({
            "source_cell":{"x":x,"y":y},
            "arrival":{"x":dx,"y":dy},
            "confidence":"confirmed_runtime_exact_pair",
            "evidence":variant["evidence"],
        })
    if representative_count!=1:
        raise ValueError("Canonical representative edge is not contained in runtime variant pairs")
    if not any(v["source_cell"]==proof["village_to_world"]["confirmed_exit_cell"]
               and v["arrival"]==proof["village_to_world"]["arrival"] for v in normalized):
        raise ValueError("Newer runtime replay is not represented in native coordinate alternatives")
    result=[dict(e) for e in edges]
    new_ctx=dict(ctx)
    new_ctx["coordinate_variants"]=normalized
    new_ctx["destination_coordinate_is_source_dependent"]=True
    new_ctx["coordinate_variant_scope"]="observed_exact_cells_only"
    new_ctx["general_transform_verified"]=False
    # An observed historical transition is not necessarily currently navigable.
    result[idx]["native_boundary_context"]=new_ctx
    return result,{"variant_edge_count":1,"confirmed_coordinate_pairs":len(normalized),
                   "source_config_id":src,"destination_config_id":dst}


def edge_activation_gate(edge: dict):
    """Tri-state conservative execution metadata; not a fake predicate decoder.

    A runtime-observed edge is confirmed to have occurred under *some*
    history/state, not known executable in the viewer's current story state.
    """
    native = edge.get("native_boundary_context")
    spatial = edge.get("source_hotspot_binding")
    confidence = edge.get("confidence") or "unknown"
    if native:
        kind = "native_boundary_saved_return"
        required = ["player_at_native_exit", "out_of_bounds_movement",
                    "compatible_saved_map_return_stack"]
        status = "runtime_observed_context" if native["runtime_edge_status"]=="observed" else "candidate_native_context"
    elif spatial:
        kind = "coordinate_trigger_with_unresolved_vm_conditions"
        required = ["player_in_trigger_region", "vm_control_flow_and_story_flags"]
        status = "runtime_observed_context" if confidence=="confirmed" else "static_candidate"
    else:
        kind = "unresolved_transition_trigger"
        required = ["source_map_and_entry_context", "event_vm_story_state"]
        status = "runtime_observed_context" if confidence=="confirmed" else "static_candidate"
    return {
        "kind":kind,
        "evidence_status":status,
        "evaluation":"unknown",
        "navigable_now":False,
        "requirements":required,
        "notes":"An edge may be inspected in the analysis viewer. It is not proof the player can currently traverse it.",
    }


if __name__=="__main__":
    print("Import match_native_boundaries and edge_activation_gate from the viewer builder.")
