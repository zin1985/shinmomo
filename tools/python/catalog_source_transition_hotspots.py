#!/usr/bin/env python3
"""Build source-transition hotspot crosslinks for proven coordinate guards."""
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
WORLD_PACK = 0x4C
WORLD_CONFIG = "cfg_t01_l001_v1"
ANCHOR_TRIGGER = "CC:0B08"

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


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def current_head(root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()


def verify_opcode_5d(rom: bytes) -> None:
    dispatch = cpu_to_file("C4:87D4")
    ptr = rom[dispatch + 0x5D * 2] | (rom[dispatch + 0x5D * 2 + 1] << 8)
    if ptr != 0x908D:
        raise SystemExit(f"opcode 0x5D dispatch changed: C4:{ptr:04X}")
    expected = bytes.fromhex(
        "AD 73 15 D7 98 90 1D C8 AD 7D 15 D7 98 90 15 C8 "
        "B7 98 CD 73 15 90 0D C8 B7 98 CD 7D 15 90 05 "
        "20 87 83 80 03 20 8C 83 A9 05 4C 10 84"
    )
    off = cpu_to_file("C4:908D")
    if rom[off:off + len(expected)] != expected:
        raise SystemExit("opcode 0x5D handler signature changed")


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
                    "trigger_addr": cpu_addr(entry["start"] + i + 7),
                    "destination_pack": body[i + 8],
                    "destination_entry": body[i + 9],
                    "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax,
                })
    return found


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument(
        "--out", type=Path,
        default=Path("data/maps/transitions/source_transition_hotspots.csv"),
    )
    ap.add_argument(
        "--summary", type=Path,
        default=Path("data/maps/transitions/source_transition_hotspots_summary.json"),
    )
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    rom = args.rom.read_bytes()
    sha = hashlib.sha256(rom).hexdigest().upper()
    if len(rom) != EXPECTED_SIZE or sha != EXPECTED_SHA256:
        raise SystemExit(f"unexpected ROM identity: size={len(rom)} sha256={sha}")
    verify_opcode_5d(rom)

    transitions = read_csv(root / "data/maps/transitions/map_transition_candidates.csv")
    by_trigger = {r["trigger_addr"]: r for r in transitions if r["trigger_addr"]}

    anchor = by_trigger.get(ANCHOR_TRIGGER)
    if not anchor or not (
        anchor["source_config_id"] == WORLD_CONFIG
        and anchor["source_pack"] == "0x4C"
        and anchor["script_pack"] == "0x4C"
        and anchor["confidence"] == "confirmed"
    ):
        raise SystemExit("confirmed world/source anchor missing or changed")

    layer = json.loads(
        (root / "viewer/data/layers/t01_l001.json").read_text(encoding="utf-8")
    )
    grid_w = int(layer["metatile_width"])
    grid_h = int(layer["metatile_height"])
    metatiles = layer["metatile_ids"]

    rows = []
    for item in exact_guards(rom, WORLD_PACK):
        tr = by_trigger.get(item["trigger_addr"])
        if not tr:
            continue
        if int(tr["destination_pack"], 16) != item["destination_pack"]:
            raise SystemExit(f"{item['trigger_addr']}: destination pack mismatch")
        if int(tr["destination_entry_id"], 16) != item["destination_entry"]:
            raise SystemExit(f"{item['trigger_addr']}: destination entry mismatch")

        x, y = item["xmin"], item["ymin"]
        xmax, ymax = item["xmax"], item["ymax"]
        if not (0 <= x <= xmax < grid_w and 0 <= y <= ymax < grid_h):
            raise SystemExit(f"{item['trigger_addr']}: hotspot outside world grid")
        ids = [
            str(metatiles[yy * grid_w + xx])
            for yy in range(y, ymax + 1)
            for xx in range(x, xmax + 1)
        ]

        trigger = item["trigger_addr"]
        confidence = (
            "confirmed_runtime_and_static"
            if trigger == ANCHOR_TRIGGER else "strong_candidate"
        )
        evidence = (
            f"0x5D@C4:908D inclusive rect X={x}..{xmax} Y={y}..{ymax}; "
            f"B3 zero-skip -> {trigger}; world metatiles={'/'.join(ids)}; "
            "pack0x4C/world binding anchored by confirmed runtime row"
        )
        if trigger == ANCHOR_TRIGGER:
            evidence += (
                "; runtime Down from (54,236) enters (54..55,237), switches "
                "0x4C->0x50, and arrives at (29,55)"
            )
        provenance = (
            f"rom={EXPECTED_SHA256};C4:908D;"
            "data/maps/transitions/map_transition_candidates.csv;"
            "viewer/data/layers/t01_l001.json"
        )
        if trigger == ANCHOR_TRIGGER:
            provenance += (
                ";data/maps/transitions/"
                "world_pack4c_to_pack50_entry02_20260929.json"
            )

        rows.append({
            "hotspot_id": f"hotspot_{trigger.replace(':', '_')}",
            "source_config_id": WORLD_CONFIG,
            "source_grid_x": x,
            "source_grid_y": y,
            "source_width": xmax - x + 1,
            "source_height": ymax - y + 1,
            "hotspot_type": "vm_opcode_0x5D_inclusive_rect",
            "trigger_type": tr["trigger_type"],
            "trigger_addr": trigger,
            "event_record": tr["event_record"],
            "transition_id": f"transition_{trigger.replace(':', '_')}",
            "destination_config_id": tr["destination_config_id"],
            "destination_x": tr["destination_x"],
            "destination_y": tr["destination_y"],
            "confidence": confidence,
            "evidence": evidence,
            "provenance": provenance,
        })

    rows.sort(key=lambda r: r["trigger_addr"])
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
    summary = {
        "schema_version": 1,
        "kind": "source_transition_hotspot_catalog_summary",
        "canonical_rom_sha256": EXPECTED_SHA256,
        "generated_from_head": current_head(root),
        "hotspot_count": len(rows),
        "source_config_resolved_count": sum(bool(r["source_config_id"]) for r in rows),
        "source_xy_resolved_count": sum(
            r["source_grid_x"] != "" and r["source_grid_y"] != "" for r in rows
        ),
        "destination_config_resolved_count": sum(
            bool(r["destination_config_id"]) for r in rows
        ),
        "destination_coordinate_resolved_count": sum(
            r["destination_x"] != "" and r["destination_y"] != "" for r in rows
        ),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "world_to_tabidachi_closed": True,
        "scope": (
            "Exact opcode0x5D inclusive-rectangle guards in independently "
            "anchored world pack 0x4C only; no generic script_pack==source-map inference."
        ),
    }
    (root / args.summary).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
