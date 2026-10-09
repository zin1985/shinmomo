#!/usr/bin/env python3
"""Tri-state event-map transition preconditions.

A known spatial predicate can reject an incompatible inspected map position.
An in-range position alone can NEVER prove navigation is enabled: ROM VM branch
and story flag conditions remain unknown until independently decoded.
The inspected position is a research coordinate, not live emulator state.
"""
from __future__ import annotations

from typing import Any

UNKNOWN = "unknown"
FALSE = "false"


def spatial_gate_for(edge: dict[str, Any]) -> dict[str, Any] | None:
    source = edge.get("source_config_id")
    hotspot = edge.get("source_hotspot_binding")
    if not source or not hotspot:
        return None
    x, y = hotspot.get("source_grid_x"), hotspot.get("source_grid_y")
    w, h = hotspot.get("source_width"), hotspot.get("source_height")
    if any(v is None for v in (x, y, w, h)):
        return None
    if w <= 0 or h <= 0:
        return None
    return {
        "status": "confirmed_vm_coordinate_region_with_unknown_story_control",
        "source_config_id": source,
        "x_min": x, "x_max": x + w - 1,
        "y_min": y, "y_max": y + h - 1,
        "source_hotspot_id": hotspot["hotspot_id"],
        "provenance": hotspot.get("provenance") or "",
    }


def annotate_edge_gate(edge: dict[str, Any], old_gate: dict[str, Any]) -> dict[str, Any]:
    result = dict(old_gate)
    result["spatial_condition"] = spatial_gate_for(edge)
    result["story_condition"] = {
        "status": "unresolved_vm_control_flow_or_saved_return_state",
        "evaluation": UNKNOWN,
    }
    result["viewer_evaluation_policy"] = (
        "Known VM region can exclude a selected research coordinate, but "
        "cannot prove that an event fires. Native boundary candidates "
        "are not exclusive passability regions."
    )
    return result


def evaluate_inspected_position(
    gate: dict[str, Any],
    *,
    config_id: str | None,
    grid_x: int | None = None,
    grid_y: int | None = None,
) -> dict[str, str]:
    """Return conservative result for an explicitly selected research position."""
    p = gate.get("spatial_condition")
    if not p:
        return {"spatial": UNKNOWN, "activation": UNKNOWN, "reason": "no_proven_exclusive_spatial_predicate"}
    if not config_id:
        return {"spatial": UNKNOWN, "activation": UNKNOWN, "reason": "source_map_not_selected"}
    if config_id != p["source_config_id"]:
        return {"spatial": FALSE, "activation": FALSE, "reason": "inspected_map_differs_from_trigger_source"}
    if grid_x is None or grid_y is None:
        return {"spatial": UNKNOWN, "activation": UNKNOWN, "reason": "inspected_grid_position_unknown"}
    if not (
        p["x_min"] <= grid_x <= p["x_max"]
        and p["y_min"] <= grid_y <= p["y_max"]
    ):
        return {"spatial": FALSE, "activation": FALSE, "reason": "inspected_position_outside_proven_vm_trigger"}
    return {"spatial": "true", "activation": UNKNOWN, "reason": "spatial_match_but_story_condition_unknown"}


def phase_ambiguity_for(edge: dict[str, Any], phase_doc: dict[str, Any]) -> dict[str, Any] | None:
    if ((edge.get("trigger_addr") or "").strip().upper()
            != (phase_doc.get("trigger_addr") or "").strip().upper()):
        return None
    if edge.get("destination_config_id"):
        raise ValueError("Do not attach unresolved destination alternatives to an already-resolved configuration.")
    if (edge.get("destination_pack") or "").upper() != (phase_doc.get("destination_pack") or "").upper():
        raise ValueError("Phase candidate pack does not match transition.")
    if (edge.get("destination_entry_id") or "").upper() != (phase_doc.get("destination_entry_id") or "").upper():
        raise ValueError("Phase entry ID differs.")
    if [edge.get("destination_x"), edge.get("destination_y")] != phase_doc.get("arrival_xy"):
        raise ValueError("Phase arrival coordinates differ.")
    if edge.get("source_config_id") != phase_doc.get("source_config_id"):
        raise ValueError("Phase source map differs.")
    variants = phase_doc.get("candidate_config_ids") or []
    if len(variants) < 2 or len(set(variants)) != len(variants):
        raise ValueError("Phase configuration alternatives must be distinct and genuinely ambiguous.")
    return {
        "status": "unresolved_phase_dependent_destination",
        "candidate_config_ids": variants,
        "arrival_xy": phase_doc["arrival_xy"],
        "source_xy": phase_doc["source_xy"],
        "resolved_by_current_story_state": False,
        "selection_predicate_status": "not_yet_decoded",
        "provenance": ";".join(phase_doc.get("provenance") or []),
        "note": "Do not select one map config without verified destination-side flag/branch evidence.",
    }
