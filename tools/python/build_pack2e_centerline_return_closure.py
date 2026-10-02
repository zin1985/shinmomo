#!/usr/bin/env python3
"""Build one conservative native-boundary return witness for pack 0x2E.

This distinguishes a mechanically closed static centerline witness from the
exact source cell used by the already-confirmed reverse runtime edge.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXPECTED = {
    "source_config_id": "cfg_t07_l015_v2",
    "source_pack": "0x2E",
    "source_tileset": 7,
    "source_layout": 15,
    "source_variant": 2,
    "bounds_trigger": "CB:DE74",
    "forward_trigger": "CC:1CDA",
    "forward_source_pack": "0x50",
    "entry_x": 9,
    "entry_y": 12,
    "return_config_id": "cfg_t04_l008_v2",
    "return_pack": "0x50",
    "return_x": 29,
    "return_y": 17,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def one(rows: list[dict[str, str]], pred, label: str) -> dict[str, str]:
    found = [row for row in rows if pred(row)]
    if len(found) != 1:
        raise SystemExit(f"{label}: expected exactly one row, got {len(found)}")
    return found[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--output",
        type=Path,
        default=Path(
            "data/maps/transitions/"
            "pack2e_centerline_return_closure_20261002.json"
        ),
    )
    args = ap.parse_args()

    bounds_rows = read_csv(
        ROOT / "data/maps/transitions/map_native_bounds_catalog.csv"
    )
    transition_rows = read_csv(
        ROOT / "data/maps/transitions/map_transition_candidates.csv"
    )
    return_rows = read_csv(
        ROOT / "data/maps/transitions/source_saved_return_origins.csv"
    )

    bounds = one(
        bounds_rows,
        lambda r: r["config_id"] == EXPECTED["source_config_id"]
        and r["pack_id_hex"] == EXPECTED["source_pack"],
        "pack2e bounds",
    )
    if (
        bounds["bounds_opcode_addr"] != EXPECTED["bounds_trigger"]
        or tuple(
            map(
                int,
                (
                    bounds["min_x"],
                    bounds["max_x"],
                    bounds["min_y"],
                    bounds["max_y"],
                ),
            )
        )
        != (0, 19, 0, 12)
    ):
        raise SystemExit(f"pack2e bounds changed: {bounds}")

    forward = one(
        transition_rows,
        lambda r: r["trigger_addr"] == EXPECTED["forward_trigger"],
        "forward CC:1CDA transition",
    )
    if (
        forward["script_pack"] != EXPECTED["forward_source_pack"]
        or forward["destination_pack"] != EXPECTED["source_pack"]
        or forward["destination_config_id"] != EXPECTED["source_config_id"]
        or (
            int(forward["destination_x"]),
            int(forward["destination_y"]),
        )
        != (EXPECTED["entry_x"], EXPECTED["entry_y"])
    ):
        raise SystemExit(f"forward transition changed: {forward}")

    saved = one(
        return_rows,
        lambda r: r["origin_trigger_addr"] == EXPECTED["forward_trigger"],
        "saved-return origin CC:1CDA",
    )
    if (
        saved["entered_destination_config_id"] != EXPECTED["source_config_id"]
        or saved["saved_return_config_id"] != EXPECTED["return_config_id"]
        or tuple(
            map(
                int,
                (
                    saved["saved_return_x_min"],
                    saved["saved_return_y_min"],
                    saved["saved_return_x_max"],
                    saved["saved_return_y_max"],
                ),
            )
        )
        != (
            EXPECTED["return_x"],
            EXPECTED["return_y"],
            EXPECTED["return_x"],
            EXPECTED["return_y"],
        )
    ):
        raise SystemExit(f"saved return changed: {saved}")

    reverse_runtime_path = (
        ROOT
        / "data/maps/transitions/"
        "stable_interior_to_pack50_shrine_exterior_20260928.json"
    )
    reverse_runtime = json.loads(
        reverse_runtime_path.read_text(encoding="utf-8")
    )
    if (
        reverse_runtime.get("relation_status") != "confirmed_runtime_transition"
        or reverse_runtime["from"]["config_id"] != EXPECTED["source_config_id"]
        or reverse_runtime["from"]["pack_id_hex"] != EXPECTED["source_pack"]
        or reverse_runtime["to"]["config_id"] != EXPECTED["return_config_id"]
        or reverse_runtime["to"]["pack_id_hex"] != EXPECTED["return_pack"]
    ):
        raise SystemExit("reverse runtime relation evidence changed")

    layer_path = ROOT / "viewer/data/layers/t07_l015.json"
    layer = json.loads(layer_path.read_text(encoding="utf-8"))
    if (
        int(layer["tileset_id"]) != EXPECTED["source_tileset"]
        or int(layer["layout_id"]) != EXPECTED["source_layout"]
    ):
        raise SystemExit("t07/l015 structural layer identity changed")

    width = int(layer["metatile_width"])
    height = int(layer["metatile_height"])
    flat = [int(v) for v in layer["metatile_ids"]]
    if len(flat) != width * height:
        raise SystemExit("t07/l015 metatile grid size mismatch")

    def tile(x: int, y: int) -> int:
        return flat[y * width + x]

    corridor = [
        {"x": x, "y": 12, "metatile_id": tile(x, 12)}
        for x in range(8, 11)
    ]
    if [cell["metatile_id"] for cell in corridor] != [68, 69, 69]:
        raise SystemExit(f"pack2e south corridor changed: {corridor}")

    min_x, max_x = int(bounds["min_x"]), int(bounds["max_x"])
    min_y, max_y = int(bounds["min_y"]), int(bounds["max_y"])
    current_x, current_y = EXPECTED["entry_x"], EXPECTED["entry_y"]
    attempted_x, attempted_y = current_x, current_y + 1
    x_in_bounds = min_x <= attempted_x <= max_x
    y_in_bounds = min_y <= attempted_y <= max_y
    if not x_in_bounds or y_in_bounds:
        raise SystemExit(
            "unexpected centerline boundary predicate: "
            f"x_in={x_in_bounds}, y_in={y_in_bounds}"
        )

    doc = {
        "schema_version": 1,
        "kind": "native_boundary_saved_return_static_witness",
        "scope": (
            "pack 0x2E centerline witness; does not assert the exact X used "
            "by the historical reverse runtime transition"
        ),
        "source": {
            "config_id": EXPECTED["source_config_id"],
            "pack_id_hex": EXPECTED["source_pack"],
            "tileset_id": EXPECTED["source_tileset"],
            "layout_id": EXPECTED["source_layout"],
            "variant": EXPECTED["source_variant"],
            "bounds": {
                "opcode_addr": bounds["bounds_opcode_addr"],
                "min_x": min_x,
                "max_x": max_x,
                "min_y": min_y,
                "max_y": max_y,
                "confidence": bounds["confidence"],
            },
            "south_opening": {
                "x_min": 8,
                "x_max": 10,
                "y": 12,
                "cells": corridor,
                "center_cell": {
                    "x": current_x,
                    "y": current_y,
                    "metatile_id": tile(current_x, current_y),
                },
            },
        },
        "centerline_entry_witness": {
            "forward_trigger_addr": forward["trigger_addr"],
            "forward_transition_type": forward["trigger_type"],
            "destination_entry_id": forward["destination_entry_id"],
            "coordinate_setter_addr": forward["destination_coordinate_addr"],
            "arrival": {"x": current_x, "y": current_y},
            "status": "confirmed_static_destination_coordinate",
            "note": (
                "This proves a static centerline entry witness, not that the "
                "historical reverse runtime sample exited from x=9."
            ),
        },
        "south_step_boundary_test": {
            "direction": "down",
            "current": {"x": current_x, "y": current_y},
            "attempted": {"x": attempted_x, "y": attempted_y},
            "x_in_bounds": x_in_bounds,
            "y_in_bounds": y_in_bounds,
            "outside_reason": "attempted_y_above_max_y",
            "native_chain": [
                "C1:8943 copies current map X/Y to $030B/$030D",
                "81:81DD compares against inclusive $15CA..$15CD bounds",
                "C1:8955 calls 81:895A on out-of-bounds",
                "81:895A requests native transition and clears $13B8",
                (
                    "C1:97BC..C1:97C5 selects saved-state restore "
                    "when $13B8==0"
                ),
                "81:8244 restores indexed saved map state",
                "C1:8255 restores the saved pack to $0305",
            ],
            "status": "confirmed_static_native_boundary_path",
        },
        "saved_return": {
            "origin_trigger_addr": saved["origin_trigger_addr"],
            "destination_config_id": saved["saved_return_config_id"],
            "destination_pack_hex": EXPECTED["return_pack"],
            "x": EXPECTED["return_x"],
            "y": EXPECTED["return_y"],
            "position_mode": saved["return_position_mode"],
            "status": "confirmed_static_exact_saved_coordinate",
        },
        "runtime_relation": {
            "status": reverse_runtime["relation_status"],
            "from_config_id": reverse_runtime["from"]["config_id"],
            "from_pack_id_hex": reverse_runtime["from"]["pack_id_hex"],
            "to_config_id": reverse_runtime["to"]["config_id"],
            "to_pack_id_hex": reverse_runtime["to"]["pack_id_hex"],
            "trigger_observation": reverse_runtime["trigger_observation"],
            "exact_pre_exit_x_captured": False,
            "runtime_return_xy_captured": False,
        },
        "closure": {
            "static_centerline_witness_closed": True,
            "reverse_relation_runtime_confirmed": True,
            "exact_historical_runtime_source_cell_closed": False,
            "exact_historical_runtime_return_xy_closed": False,
            "status": (
                "closed_static_centerline_witness_with_confirmed_runtime_relation"
            ),
            "confidence": (
                "confirmed_static_path_plus_confirmed_runtime_edge_relation"
            ),
        },
        "provenance": [
            "data/maps/transitions/map_native_bounds_catalog.csv",
            "data/maps/transitions/map_transition_candidates.csv",
            "data/maps/transitions/source_saved_return_origins.csv",
            (
                "data/maps/transitions/"
                "stable_interior_to_pack50_shrine_exterior_20260928.json"
            ),
            "viewer/data/layers/t07_l015.json",
            "C4:8B16",
            "C1:8943",
            "81:81DD",
            "C1:8955",
            "81:895A",
            "C1:97BC",
            "81:8244",
            "C1:8255",
        ],
    }

    out = args.output if args.output.is_absolute() else ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(out)
    print(doc["closure"]["status"])


if __name__ == "__main__":
    main()