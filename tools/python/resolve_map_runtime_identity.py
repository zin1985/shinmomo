#!/usr/bin/env python3
"""Resolve a derived runtime map-state record to the confirmed ROM selector corpus."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def config_id(tileset: int, layout: int, variant: int) -> str:
    return f"cfg_t{tileset:02d}_l{layout:03d}_v{variant}"


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runtime_identity", type=Path)
    ap.add_argument(
        "--primary",
        type=Path,
        default=Path("data/maps/selectors/primary_map_selector_catalog.csv"),
    )
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    identity = json.loads(args.runtime_identity.read_text(encoding="utf-8-sig"))
    state = identity["map_state"]
    rows = load_rows(args.primary)

    tileset = int(state["primary_tileset_139c"])
    layout = int(state["primary_layout_139e"])
    variant = int(state["map_variant_139b"])
    pack = state.get("current_pack_0305")
    mode = state.get("mode_1398")

    selector_matches = [
        r for r in rows
        if int(r["primary_tileset_id"]) == tileset
        and int(r["primary_layout_id"]) == layout
        and int(r["map_variant"]) == variant
        and r["normal_mode_confirmed"].lower() == "true"
    ]
    pack_matches = selector_matches
    if pack is not None:
        pack_matches = [r for r in selector_matches if int(r["pack_id_dec"]) == int(pack)]

    resolved = len(pack_matches) == 1
    chosen = pack_matches[0] if resolved else None
    result = {
        "schema_version": 1,
        "kind": "runtime_map_selector_resolution",
        "sample_id": identity.get("sample_id") or identity.get("capture_id"),
        "runtime_frame": identity.get("runtime_frame", identity.get("frame")),
        "runtime_state": {
            "mode_1398": mode,
            "current_pack_0305": pack,
            "vm_pack_126e": state.get("vm_pack_126e"),
            "resolved_pack_12b4": state.get("resolved_pack_12b4"),
            "primary_tileset_139c": tileset,
            "primary_layout_139e": layout,
            "map_variant_139b": variant,
        },
        "config_id": config_id(tileset, layout, variant),
        "selector_match_count": len(selector_matches),
        "selector_match_addresses": [r["command_addr"] for r in selector_matches],
        "pack_filtered_match_count": len(pack_matches),
        "pack_filtered_match_addresses": [r["command_addr"] for r in pack_matches],
        "resolved_unique_occurrence": resolved,
        "resolved_occurrence": None,
    }
    if chosen is not None:
        result["resolved_occurrence"] = {
            "pack_id_hex": chosen["pack_id_hex"],
            "record_index": int(chosen["record_index"]),
            "entry_id_hex": chosen["entry_id_hex"],
            "substream_start": chosen["substream_start"],
            "command_addr": chosen["command_addr"],
            "layout_ptr": chosen["layout_ptr"],
            "primary_tileset_ptr": chosen["primary_tileset_ptr"],
        }
    expected = identity.get("resolved_rom_identity")
    if expected:
        checks = {
            "config_id": expected.get("config_id") == result["config_id"],
            "command_addr": (
                chosen is not None
                and expected.get("command_addr") == chosen["command_addr"]
            ),
            "pack_id_hex": (
                chosen is not None
                and expected.get("pack_id_hex") == chosen["pack_id_hex"]
            ),
        }
        result["embedded_resolution_checks"] = checks
        if not all(checks.values()):
            raise SystemExit(
                "runtime resolver disagrees with embedded resolved_rom_identity"
            )

    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
