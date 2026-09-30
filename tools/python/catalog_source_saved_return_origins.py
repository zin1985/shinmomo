#!/usr/bin/env python3
"""Build saved-return target crosslinks from proven opcode-0x53 source hotspots."""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter
from pathlib import Path

COLUMNS = [
    "origin_hotspot_id", "origin_trigger_addr", "entered_destination_config_id",
    "saved_return_config_id", "saved_return_x_min", "saved_return_y_min",
    "saved_return_x_max", "saved_return_y_max", "saved_return_width",
    "saved_return_height", "return_position_mode", "reverse_runtime_status",
    "reverse_runtime_evidence", "confidence", "evidence", "provenance",
]


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def current_head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--hotspots", type=Path,
        default=Path("data/maps/transitions/source_transition_hotspots.csv"),
    )
    ap.add_argument(
        "--out", type=Path,
        default=Path("data/maps/transitions/source_saved_return_origins.csv"),
    )
    ap.add_argument(
        "--summary", type=Path,
        default=Path("data/maps/transitions/source_saved_return_origins_summary.json"),
    )
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    hotspots = [
        r for r in read_csv(root / args.hotspots)
        if r["trigger_type"] == "vm_opcode_0x53_transition_wrapper_terminal"
    ]

    world_rev = json.loads(
        (root / "data/maps/transitions/tabidachi_village_to_world_pack4c_restore_20260929.json")
        .read_text(encoding="utf-8-sig")
    )
    pack2e_rev = json.loads(
        (root / "data/maps/transitions/stable_interior_to_pack50_shrine_exterior_20260928.json")
        .read_text(encoding="utf-8-sig")
    )

    rows = []
    for r in hotspots:
        x = int(r["source_grid_x"])
        y = int(r["source_grid_y"])
        width = int(r["source_width"])
        height = int(r["source_height"])
        exact = width == 1 and height == 1

        reverse_status = ""
        reverse_evidence = ""
        confidence = "strong_static_saved_return_origin"

        if r["trigger_addr"] == "CC:0B08":
            if not (
                world_rev["from"]["config_id"] == r["destination_config_id"]
                and world_rev["to"]["config_id"] == r["source_config_id"]
            ):
                raise SystemExit("world reverse runtime fixture mismatch")
            coord = world_rev["to"]["coordinate"]
            reverse_status = "confirmed_reverse_edge_and_return_coordinate"
            reverse_evidence = (
                f"{world_rev['from']['config_id']}->{world_rev['to']['config_id']}; "
                f"runtime arrival=({coord['x']},{coord['y']})"
            )
            confidence = "confirmed_runtime_and_static_saved_return"

        elif r["trigger_addr"] == "CC:1CDA":
            if not (
                pack2e_rev["from"]["config_id"] == r["destination_config_id"]
                and pack2e_rev["to"]["config_id"] == r["source_config_id"]
            ):
                raise SystemExit("pack2e reverse runtime fixture mismatch")
            reverse_status = "confirmed_reverse_edge_target_config_only"
            reverse_evidence = (
                f"{pack2e_rev['from']['config_id']}->{pack2e_rev['to']['config_id']}; "
                "source-side return trigger and runtime arrival X/Y not captured"
            )
            confidence = "strong_static_saved_return_with_confirmed_reverse_edge"

        rows.append({
            "origin_hotspot_id": r["hotspot_id"],
            "origin_trigger_addr": r["trigger_addr"],
            "entered_destination_config_id": r["destination_config_id"],
            "saved_return_config_id": r["source_config_id"],
            "saved_return_x_min": x,
            "saved_return_y_min": y,
            "saved_return_x_max": x + width - 1,
            "saved_return_y_max": y + height - 1,
            "saved_return_width": width,
            "saved_return_height": height,
            "return_position_mode": (
                "exact_saved_coordinate"
                if exact else "runtime_coordinate_within_saved_hotspot_region"
            ),
            "reverse_runtime_status": reverse_status,
            "reverse_runtime_evidence": reverse_evidence,
            "confidence": confidence,
            "evidence": (
                "opcode 0x53 handler C4:8B3F saves active map state through "
                "81:8207 before destination switch; saved state includes "
                "$0305/$1573/$157D/$15C3/$15C4/$13B9. Therefore a later "
                "saved-state restore returns to the actual source coordinate"
                + (" exactly at this one-cell hotspot."
                   if exact else " within this inclusive hotspot region.")
            ),
            "provenance": (
                "data/maps/transitions/source_transition_hotspots.csv;"
                "C4:8B3F;81:8207;C1:8244;C1:8255"
                + (
                    ";data/maps/transitions/tabidachi_village_to_world_pack4c_restore_20260929.json"
                    if r["trigger_addr"] == "CC:0B08" else
                    ";data/maps/transitions/stable_interior_to_pack50_shrine_exterior_20260928.json"
                    if r["trigger_addr"] == "CC:1CDA" else ""
                )
            ),
        })

    rows.sort(key=lambda r: (r["saved_return_config_id"], r["origin_trigger_addr"]))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with (root / args.out).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    exact_count = sum(r["return_position_mode"] == "exact_saved_coordinate" for r in rows)
    summary = {
        "schema_version": 1,
        "kind": "source_saved_return_origin_catalog_summary",
        "generated_from_head": current_head(root),
        "origin_count": len(rows),
        "exact_saved_coordinate_count": exact_count,
        "region_saved_coordinate_count": len(rows) - exact_count,
        "reverse_runtime_crosslink_count": sum(bool(r["reverse_runtime_status"]) for r in rows),
        "confidence_counts": dict(sorted(Counter(r["confidence"] for r in rows).items())),
        "native_boundary_return_mechanism": {
            "current_coordinate_checker": "C1:8943",
            "bounds_helper": "81:81DD",
            "bounds_fields": ["$15CA", "$15CB", "$15CC", "$15CD"],
            "out_of_bounds_request_callsite": "C1:8955",
            "transition_request_helper": "81:895A",
            "restore_gate": "C1:97BC..C1:97C5",
            "saved_state_restore": "81:8244",
            "pack_restore_write": "C1:8255",
            "status": "static_mechanism_proven_concrete_source_bounds_unresolved",
        },
        "known_reverse_edges": {
            "cfg_t04_l008_v2_to_cfg_t01_l001_v1": (
                "runtime confirmed; saved return target runtime-confirmed at (54,237)"
            ),
            "cfg_t07_l015_v2_to_cfg_t04_l008_v2": (
                "runtime confirmed; static saved return target from CC:1CDA is "
                "exact (29,17), but runtime arrival X/Y was not captured"
            ),
        },
    }
    (root / args.summary).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
