#!/usr/bin/env python3
"""Build source-transition hotspot crosslinks from proven coordinate predicates."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

import catalog_map_selectors as cms

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA256 = "F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"
ANCHOR_TRIGGER = "CC:0B08"

SOURCE_SPECS = {
    0x4C: {
        "config_id": "cfg_t01_l001_v1",
        "label": "world",
        "layer": "viewer/data/layers/t01_l001.json",
        "anchor": "data/maps/transitions/world_pack4c_to_pack50_entry02_20260929.json",
    },
    0x50: {
        "config_id": "cfg_t04_l008_v2",
        "label": "tabidachi",
        "layer": "viewer/data/layers/t04_l008.json",
        "anchor": "data/maps/transitions/tabidachi_village_to_world_pack4c_restore_20260929.json",
    },
}

COLUMNS = [
    "hotspot_id", "source_config_id", "source_grid_x", "source_grid_y",
    "source_width", "source_height", "hotspot_type", "trigger_type",
    "trigger_addr", "event_record", "transition_id", "destination_config_id",
    "destination_x", "destination_y", "confidence", "evidence", "provenance",
]


def cpu_addr(off: int) -> str:
    return f"{0xC0 + (off >> 16):02X}:{off & 0xFFFF:04X}"


def cpu_to_file(text: str) -> int:
    bank, addr = text.split(":")
    return ((int(bank, 16) - 0xC0) << 16) | int(addr, 16)


def hx(v: int) -> str:
    return f"0x{v:02X}"


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def current_head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def verify_handlers(rom: bytes) -> None:
    dispatch = cpu_to_file("C4:87D4")
    checks = {
        0x5D: (
            0x908D,
            bytes.fromhex(
                "AD 73 15 D7 98 90 1D C8 AD 7D 15 D7 98 90 15 C8 "
                "B7 98 CD 73 15 90 0D C8 B7 98 CD 7D 15 90 05 "
                "20 87 83 80 03 20 8C 83 A9 05 4C 10 84"
            ),
        ),
        0x69: (
            0x9320,
            bytes.fromhex(
                "B7 98 CD 73 15 D0 0D C8 B7 98 CD 7D 15 D0 05 "
                "20 87 83 80 03 20 8C 83 A9 03 4C 10 84"
            ),
        ),
    }
    for op, (expected_ptr, signature) in checks.items():
        ptr = rom[dispatch + op * 2] | (rom[dispatch + op * 2 + 1] << 8)
        if ptr != expected_ptr:
            raise SystemExit(f"opcode {op:#04x} dispatch changed: C4:{ptr:04X}")
        off = cpu_to_file(f"C4:{expected_ptr:04X}")
        if rom[off:off + len(signature)] != signature:
            raise SystemExit(f"opcode {op:#04x} handler signature changed")


def exact_guards(rom: bytes, pack_id: int) -> list[dict]:
    pack = cms.parse_pack(rom, pack_id)
    if not pack:
        return []
    found = []
    for record in pack["records"]:
        if (pack_id, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
            continue
        header = cms.parse_record_header(rom, record)
        if not header:
            continue
        for entry in header["entries"]:
            body = rom[entry["start"]:entry["end"]]

            # Inclusive rectangle: 5D xmin ymin xmax ymax B3 05 53/56 pp ee B0
            for i in range(max(0, len(body) - 10)):
                if i + 11 > len(body):
                    break
                if not (
                    body[i] == 0x5D
                    and body[i + 5] == 0xB3
                    and body[i + 6] == 0x05
                    and body[i + 7] in (0x53, 0x56)
                    and body[i + 10] == 0xB0
                ):
                    continue
                xmin, ymin, xmax, ymax = body[i + 1:i + 5]
                if xmin > xmax or ymin > ymax:
                    continue
                found.append({
                    "hotspot_type": "vm_opcode_0x5D_inclusive_rect",
                    "handler": "C4:908D",
                    "trigger_addr": cpu_addr(entry["start"] + i + 7),
                    "destination_pack": body[i + 8],
                    "destination_entry": body[i + 9],
                    "x": xmin, "y": ymin,
                    "width": xmax - xmin + 1, "height": ymax - ymin + 1,
                })

            # Exact point: 69 x y B3 05 53/56 pp ee B0
            for i in range(max(0, len(body) - 8)):
                if i + 9 > len(body):
                    break
                if not (
                    body[i] == 0x69
                    and body[i + 3] == 0xB3
                    and body[i + 4] == 0x05
                    and body[i + 5] in (0x53, 0x56)
                    and body[i + 8] == 0xB0
                ):
                    continue
                found.append({
                    "hotspot_type": "vm_opcode_0x69_exact_point",
                    "handler": "C4:9320",
                    "trigger_addr": cpu_addr(entry["start"] + i + 5),
                    "destination_pack": body[i + 6],
                    "destination_entry": body[i + 7],
                    "x": body[i + 1], "y": body[i + 2],
                    "width": 1, "height": 1,
                })
    return found


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--out", type=Path, default=Path("data/maps/transitions/source_transition_hotspots.csv"))
    ap.add_argument("--summary", type=Path, default=Path("data/maps/transitions/source_transition_hotspots_summary.json"))
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    rom = args.rom.read_bytes()
    sha = hashlib.sha256(rom).hexdigest().upper()
    if len(rom) != EXPECTED_SIZE or sha != EXPECTED_SHA256:
        raise SystemExit(f"unexpected ROM identity: size={len(rom)} sha256={sha}")
    verify_handlers(rom)

    transitions = read_csv(root / "data/maps/transitions/map_transition_candidates.csv")
    by_trigger = {r["trigger_addr"]: r for r in transitions if r["trigger_addr"]}

    layers = {}
    for pack_id, spec in SOURCE_SPECS.items():
        anchored = any(
            r["confidence"] == "confirmed"
            and r["source_pack"] == hx(pack_id)
            and r["source_config_id"] == spec["config_id"]
            for r in transitions
        )
        if not anchored:
            raise SystemExit(
                f"independent source-pack/config anchor missing for {hx(pack_id)} "
                f"{spec['config_id']}"
            )
        layers[pack_id] = json.loads((root / spec["layer"]).read_text(encoding="utf-8"))

    rows = []
    for pack_id, spec in SOURCE_SPECS.items():
        layer = layers[pack_id]
        grid_w = int(layer["metatile_width"])
        grid_h = int(layer["metatile_height"])
        metatiles = layer["metatile_ids"]

        for item in exact_guards(rom, pack_id):
            tr = by_trigger.get(item["trigger_addr"])
            if not tr:
                raise SystemExit(f"{item['trigger_addr']}: transition row missing")
            if int(tr["destination_pack"], 16) != item["destination_pack"]:
                raise SystemExit(f"{item['trigger_addr']}: destination pack mismatch")
            if int(tr["destination_entry_id"], 16) != item["destination_entry"]:
                raise SystemExit(f"{item['trigger_addr']}: destination entry mismatch")

            x, y = item["x"], item["y"]
            width, height = item["width"], item["height"]
            if not (0 <= x and 0 <= y and x + width <= grid_w and y + height <= grid_h):
                raise SystemExit(f"{item['trigger_addr']}: hotspot outside source grid")
            ids = [
                str(metatiles[yy * grid_w + xx])
                for yy in range(y, y + height)
                for xx in range(x, x + width)
            ]

            trigger = item["trigger_addr"]
            confidence = (
                "confirmed_runtime_and_static"
                if trigger == ANCHOR_TRIGGER else "strong_candidate"
            )
            if item["hotspot_type"] == "vm_opcode_0x69_exact_point":
                evidence = (
                    f"0x69@C4:9320 exact coordinate predicate X={x} Y={y}; "
                    f"B3 zero-skip -> {trigger}; source metatile={ids[0]}; "
                    f"{spec['label']} source-pack/config relation independently "
                    "anchored by confirmed runtime transition"
                )
            else:
                evidence = (
                    f"0x5D@C4:908D inclusive rect X={x}..{x + width - 1} "
                    f"Y={y}..{y + height - 1}; B3 zero-skip -> {trigger}; "
                    f"source metatiles={'/'.join(ids)}; {spec['label']} "
                    "source-pack/config relation independently anchored by "
                    "confirmed runtime transition"
                )
            if trigger == ANCHOR_TRIGGER:
                evidence += (
                    "; runtime Down from (54,236) enters (54..55,237), switches "
                    "0x4C->0x50, and arrives at (29,55)"
                )

            rows.append({
                "hotspot_id": f"hotspot_{trigger.replace(':', '_')}",
                "source_config_id": spec["config_id"],
                "source_grid_x": x,
                "source_grid_y": y,
                "source_width": width,
                "source_height": height,
                "hotspot_type": item["hotspot_type"],
                "trigger_type": tr["trigger_type"],
                "trigger_addr": trigger,
                "event_record": tr["event_record"],
                "transition_id": f"transition_{trigger.replace(':', '_')}",
                "destination_config_id": tr["destination_config_id"],
                "destination_x": tr["destination_x"],
                "destination_y": tr["destination_y"],
                "confidence": confidence,
                "evidence": evidence,
                "provenance": (
                    f"rom={EXPECTED_SHA256};{item['handler']};"
                    "data/maps/transitions/map_transition_candidates.csv;"
                    f"{spec['layer']};{spec['anchor']}"
                ),
            })

    native_path = root / "data/maps/transitions/tabidachi_south_boundary_to_world_20260930.json"
    native = json.loads(native_path.read_text(encoding="utf-8"))
    src = native["source"]
    obs = native["transition_observation"]
    if not (
        src["config_id"] == "cfg_t04_l008_v2"
        and src["pack_id_hex"] == "0x50"
        and src["confirmed_hotspot"] == {"x": 28, "y": 55, "width": 1, "height": 1}
        and src["first_out_of_bounds"] == {"x": 28, "y": 56}
        and src["native_bounds"] == {"min_x": 9, "max_x": 70, "min_y": 8, "max_y": 55}
        and obs["destination_pack_after"] == "0x4C"
        and obs["destination_config_id"] == "cfg_t01_l001_v1"
        and obs["destination_coordinate"] == [54, 237]
        and native["confidence"] == "confirmed_runtime_and_static"
    ):
        raise SystemExit("Tabidachi native boundary fixture changed")

    rows.append({
        "hotspot_id": "hotspot_native_tabidachi_south_exit_x28_y55",
        "source_config_id": "cfg_t04_l008_v2",
        "source_grid_x": 28,
        "source_grid_y": 55,
        "source_width": 1,
        "source_height": 1,
        "hotspot_type": "native_boundary_saved_return_exit",
        "trigger_type": "native_out_of_bounds_saved_state_restore",
        "trigger_addr": "C1:8955",
        "event_record": "",
        "transition_id": "runtime_restore_cfg_t04_l008_v2_to_cfg_t01_l001_v1",
        "destination_config_id": "cfg_t01_l001_v1",
        "destination_x": 54,
        "destination_y": 237,
        "confidence": "confirmed_runtime_and_static",
        "evidence": (
            "runtime frame 16065 current=(28,55) with bounds X=9..70,Y=8..55; "
            "Down reaches (28,56) at frame 16070; static C1:8943/81:81DD "
            "classifies that coordinate out of bounds, C1:8955 calls 81:895A, "
            "and C1:97BC/81:8244 restores saved map state; within the next "
            "8 neutral frames pack 0x50->0x4C and current coordinate=(54,237)"
        ),
        "provenance": (
            "data/maps/transitions/tabidachi_south_boundary_to_world_20260930.json;"
            "data/maps/transitions/tabidachi_village_to_world_pack4c_restore_20260929.json;"
            "C1:8943;81:81DD;C1:8955;81:895A;C1:97BC;81:8244;C1:8255"
        ),
    })

    pack2e_native_path = root / "data/maps/transitions/pack2e_south_boundary_to_tabidachi_20260930.json"
    pack2e_native = json.loads(pack2e_native_path.read_text(encoding="utf-8"))
    pack2e_src = pack2e_native["source"]
    pack2e_dest = pack2e_native["destination"]
    pack2e_corridor = pack2e_src["candidate_exit_corridor"]
    if not (
        pack2e_src["config_id"] == "cfg_t07_l015_v2"
        and pack2e_src["pack_id_hex"] == "0x2E"
        and pack2e_src["native_bounds"] == {"min_x": 0, "max_x": 19, "min_y": 0, "max_y": 12}
        and pack2e_corridor["x_min"] == 8
        and pack2e_corridor["x_max"] == 10
        and pack2e_corridor["y"] == 12
        and pack2e_dest["config_id"] == "cfg_t04_l008_v2"
        and pack2e_dest["saved_return_coordinate"] == [29, 17]
        and pack2e_native["confidence"] == "strong_static_runtime_candidate"
    ):
        raise SystemExit("pack0x2E native south-return candidate fixture changed")

    rows.append({
        "hotspot_id": "hotspot_native_pack2e_south_exit_candidate",
        "source_config_id": "cfg_t07_l015_v2",
        "source_grid_x": 8,
        "source_grid_y": 12,
        "source_width": 3,
        "source_height": 1,
        "hotspot_type": "native_boundary_saved_return_candidate_corridor",
        "trigger_type": "native_out_of_bounds_saved_state_restore",
        "trigger_addr": "C1:8955",
        "event_record": "",
        "transition_id": "runtime_restore_cfg_t07_l015_v2_to_cfg_t04_l008_v2",
        "destination_config_id": "cfg_t04_l008_v2",
        "destination_x": 29,
        "destination_y": 17,
        "confidence": "strong_candidate",
        "evidence": (
            "opcode 0x52 at CB:DE74 proves native bounds X=0..19,Y=0..12; "
            "decoded layer t07/l015 has a central floor opening x=8..10 at y=12; "
            "the forward CC:1CDA transition arrives at center (9,12); runtime "
            "evidence independently confirms walking south through the central exit "
            "returns pack 0x2E->0x50. Exact runtime pre-exit X and collision "
            "passability of all three cells were not captured."
        ),
        "provenance": (
            "data/maps/transitions/pack2e_south_boundary_to_tabidachi_20260930.json;"
            "data/maps/transitions/map_native_bounds_catalog.csv;"
            "viewer/data/layers/t07_l015.json;"
            "data/maps/transitions/stable_interior_to_pack50_shrine_exterior_20260928.json;"
            "data/maps/transitions/source_saved_return_origins.csv;"
            "C4:8B16;C1:8943;81:81DD;C1:8955;81:895A;81:8244"
        ),
    })

    rows.sort(key=lambda r: (r["source_config_id"], r["trigger_addr"]))
    if len({r["hotspot_id"] for r in rows}) != len(rows):
        raise SystemExit("duplicate hotspot ids")
    if not any(
        r["trigger_addr"] == ANCHOR_TRIGGER
        and r["confidence"] == "confirmed_runtime_and_static"
        for r in rows
    ):
        raise SystemExit("world-to-Tabidachi anchor not extracted")

    out = root / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    confidence_counts = Counter(r["confidence"] for r in rows)
    type_counts = Counter(r["hotspot_type"] for r in rows)
    source_counts = Counter(r["source_config_id"] for r in rows)
    pack2e = next(r for r in rows if r["trigger_addr"] == "CC:1CDA")

    summary = {
        "schema_version": 3,
        "kind": "source_transition_hotspot_catalog_summary",
        "canonical_rom_sha256": EXPECTED_SHA256,
        "generated_from_head": current_head(root),
        "hotspot_count": len(rows),
        "source_config_resolved_count": sum(bool(r["source_config_id"]) for r in rows),
        "source_xy_resolved_count": sum(
            r["source_grid_x"] != "" and r["source_grid_y"] != "" for r in rows
        ),
        "destination_config_resolved_count": sum(bool(r["destination_config_id"]) for r in rows),
        "destination_coordinate_resolved_count": sum(
            r["destination_x"] != "" and r["destination_y"] != "" for r in rows
        ),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "hotspot_type_counts": dict(sorted(type_counts.items())),
        "source_config_counts": dict(sorted(source_counts.items())),
        "world_to_tabidachi_closed": True,
        "tabidachi_to_world_source_hotspot_closed": True,
        "tabidachi_to_world_source_hotspot": {
            "source_grid_x": 28,
            "source_grid_y": 55,
            "source_width": 1,
            "source_height": 1,
            "first_out_of_bounds_x": 28,
            "first_out_of_bounds_y": 56,
            "native_bounds": {"min_x": 9, "max_x": 70, "min_y": 8, "max_y": 55},
            "trigger_addr": "C1:8955",
            "destination_config_id": "cfg_t01_l001_v1",
            "destination_x": 54,
            "destination_y": 237,
            "status": "confirmed_runtime_and_static",
        },
        "tabidachi_to_pack2e_hotspot": {
            "trigger_addr": pack2e["trigger_addr"],
            "source_grid_x": pack2e["source_grid_x"],
            "source_grid_y": pack2e["source_grid_y"],
            "destination_config_id": pack2e["destination_config_id"],
            "status": "strong_static_crosslink",
        },
        "pack2e_to_tabidachi_source_hotspot_closed": False,
        "pack2e_to_tabidachi_native_candidate": {
            "source_grid_x": 8,
            "source_grid_y": 12,
            "source_width": 3,
            "source_height": 1,
            "center_candidate_x": 9,
            "native_bounds": {"min_x": 0, "max_x": 19, "min_y": 0, "max_y": 12},
            "trigger_addr": "C1:8955",
            "destination_config_id": "cfg_t04_l008_v2",
            "destination_x": 29,
            "destination_y": 17,
            "status": "strong_candidate_exact_source_cell_open",
        },
        "scope": (
            "Exact opcode0x5D rectangle and opcode0x69 point predicates from "
            "independently runtime-anchored source packs, plus runtime+static "
            "native boundary saved-return hotspots; no generic "
            "script_pack==source-map inference."
        ),
    }
    (root / args.summary).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
