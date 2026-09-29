#!/usr/bin/env python3
"""Catalog conservative Shinmomo map-transition candidates.

No ROM payload is written. Outputs contain only derived addresses, IDs,
configuration metadata, coordinates and evidence labels.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import catalog_map_selectors as cms

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA256 = "F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"

COLUMNS = [
    "source_config_id", "source_pack", "source_layout", "source_tileset",
    "script_pack", "script_record", "script_entry",
    "trigger_type", "trigger_addr", "event_record", "vm_context",
    "event_sources", "destination_pack", "destination_entry_id", "destination_config_id",
    "destination_layout", "destination_tileset", "destination_variant",
    "destination_x", "destination_y",
    "destination_secondary_x", "destination_secondary_y",
    "destination_coordinate_addr", "condition", "confidence",
    "evidence", "provenance",
]


def cpu_addr(off: int) -> str:
    return f"{0xC0 + (off >> 16):02X}:{off & 0xFFFF:04X}"


def cpu_to_file(text: str) -> int:
    bank_text, addr_text = text.split(":")
    return ((int(bank_text, 16) - 0xC0) << 16) | int(addr_text, 16)


def hx(value: int) -> str:
    return f"0x{value:02X}"


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def current_head(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return ""


def coordinate_setter(rom: bytes, entry: dict | None) -> dict | None:
    """Recognize only instruction-aligned 0x58 forms proven by existing grammar."""
    if entry is None:
        return None
    body = rom[entry["start"]:entry["end"]]
    pos = None
    alignment = ""
    if len(body) >= 5 and body[0] == 0x58:
        pos, alignment = 0, "entry_start"
    elif len(body) >= 7 and body[0] == 0x96 and body[2] == 0x58:
        pos, alignment = 2, "proven_0x96_two_byte_prefix"
    if pos is None:
        return None
    return {
        "x": body[pos + 1],
        "y": body[pos + 2],
        "secondary_x": body[pos + 3],
        "secondary_y": body[pos + 4],
        "addr": cpu_addr(entry["start"] + pos),
        "alignment": alignment,
    }


def blank_row() -> dict:
    return {key: "" for key in COLUMNS}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("data/maps/transitions/map_transition_candidates.csv"),
    )
    ap.add_argument(
        "--summary",
        type=Path,
        default=Path("data/maps/transitions/map_transition_candidates_summary.json"),
    )
    ap.add_argument(
        "--doc",
        type=Path,
        default=Path("docs/analysis/map_transition_candidate_catalog.md"),
    )
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[2]
    rom = args.rom.read_bytes()
    sha = hashlib.sha256(rom).hexdigest().upper()
    if len(rom) != EXPECTED_SIZE or sha != EXPECTED_SHA256:
        raise SystemExit(f"unexpected ROM identity: size={len(rom)} sha256={sha}")

    selector_rows = read_csv(root / "data/maps/selectors/primary_map_selector_catalog.csv")
    config_rows = read_csv(root / "data/maps/configurations/map_configuration_index.csv")
    frame_rows = read_csv(root / "data/events/event_record_frame_catalog.csv")
    source_xref_rows = read_csv(root / "data/events/event_source_crosslink.csv")
    config_by_id = {r["config_id"]: r for r in config_rows}
    config_by_tuple = {
        (int(r["primary_tileset_id"]), int(r["primary_layout_id"]), int(r["map_variant"])): r
        for r in config_rows
    }

    pack_configs: dict[int, set[str]] = defaultdict(set)
    for r in selector_rows:
        if (
            int(r["record_index"]) == 0
            and int(r["entry_id_dec"]) == 1
            and r["normal_mode_confirmed"].lower() == "true"
        ):
            key = (
                int(r["primary_tileset_id"]),
                int(r["primary_layout_id"]),
                int(r["map_variant"]),
            )
            cfg = config_by_tuple.get(key)
            if cfg:
                pack_configs[int(r["pack_id_dec"])].add(cfg["config_id"])

    frames_by_family: dict[int, list[dict]] = defaultdict(list)
    for frame in frame_rows:
        item = dict(frame)
        item["_start"] = cpu_to_file(frame["record_start"])
        item["_end"] = cpu_to_file(frame["record_end_exclusive"])
        frames_by_family[int(frame["family_id"])].append(item)

    sources_by_record: dict[str, list[str]] = defaultdict(list)
    for xref in source_xref_rows:
        label = f"{xref['subindex_hex']}->{xref['selected_source_cpu']}"
        if label not in sources_by_record[xref["record_id"]]:
            sources_by_record[xref["record_id"]].append(label)

    packs = {}
    for pack_id in range(cms.FIRST_REAL_PACK, cms.LAST_REAL_PACK + 1):
        parsed = cms.parse_pack(rom, pack_id)
        if parsed:
            packs[pack_id] = parsed


    def record0_entry(pack_id: int, entry_id: int) -> dict | None:
        pack = packs.get(pack_id)
        if not pack or not pack["records"]:
            return None
        header = cms.parse_record_header(rom, pack["records"][0])
        if not header:
            return None
        return next(
            (e for e in header["entries"] if e["entry_id"] == entry_id),
            None,
        )

    def destination_config(pack_id: int) -> dict | None:
        ids = pack_configs.get(pack_id, set())
        if len(ids) != 1:
            return None
        return config_by_id[next(iter(ids))]

    def event_context(pack_id: int, trigger_addr: str) -> tuple[str, str]:
        off = cpu_to_file(trigger_addr)
        for frame in frames_by_family.get(pack_id, []):
            if frame["_start"] <= off < frame["_end"]:
                record_id = frame["record_id"]
                return record_id, ";".join(sources_by_record.get(record_id, []))
        return "", ""

    def apply_destination(row: dict, pack_id: int, entry_id: int) -> tuple[bool, bool]:
        row["destination_pack"] = hx(pack_id)
        row["destination_entry_id"] = hx(entry_id)
        cfg = destination_config(pack_id)
        if cfg:
            row["destination_config_id"] = cfg["config_id"]
            row["destination_layout"] = cfg["primary_layout_id"]
            row["destination_tileset"] = cfg["primary_tileset_id"]
            row["destination_variant"] = cfg["map_variant"]
        entry = record0_entry(pack_id, entry_id)
        coord = coordinate_setter(rom, entry)
        if coord:
            row["destination_x"] = coord["x"]
            row["destination_y"] = coord["y"]
            row["destination_secondary_x"] = coord["secondary_x"]
            row["destination_secondary_y"] = coord["secondary_y"]
            row["destination_coordinate_addr"] = coord["addr"]
        return entry is not None, coord is not None

    def route57_final(route_index: int) -> dict | None:
        if not 0 <= route_index < 16:
            return None
        table_off = cpu_to_file("C6:8060") + route_index * 2
        ptr = rom[table_off] | (rom[table_off + 1] << 8)
        pos = cpu_to_file(f"C6:{ptr:04X}")
        context_0306 = rom[pos]
        pos += 1
        nodes = []
        while pos + 3 < len(rom):
            pack_id = rom[pos]
            pos += 1
            if pack_id == 0:
                break
            x = rom[pos]
            y = rom[pos + 1]
            entrance = rom[pos + 2]
            pos += 3
            nodes.append((pack_id, x, y, entrance))
        if not nodes:
            return None
        pack_id, x, y, entrance = nodes[-1]
        return {
            "route_ptr": f"C6:{ptr:04X}",
            "context_0306": context_0306,
            "pack_id": pack_id,
            "x": x,
            "y": y,
            "entrance": entrance,
            "saved_node_count": max(0, len(nodes) - 1),
        }

    rows: list[dict] = []
    seen_triggers: set[str] = set()

    # Runtime-confirmed edge already preserved in canonical evidence.
    confirmed = blank_row()
    confirmed.update({
        "source_config_id": "cfg_t07_l015_v2",
        "source_pack": "0x2E",
        "source_layout": "15",
        "source_tileset": "7",
        "trigger_type": "runtime_observed_map_transition",
        "destination_pack": "0x50",
        "destination_entry_id": "",
        "destination_config_id": "cfg_t04_l008_v2",
        "destination_layout": "8",
        "destination_tileset": "4",
        "destination_variant": "2",
        "condition": (
            "walk south through the central-room exit; exact event opcode "
            "address is not yet identified"
        ),
        "confidence": "confirmed",
        "evidence": (
            "runtime trace shows $0305 0x2E->0x50, then $126E/$12B4 converge "
            "to 0x50 and selector 4/8/2 becomes active"
        ),
        "provenance": (
            "data/maps/transitions/stable_interior_to_pack50_shrine_exterior_20260928.json;"
            "docs/analysis/map_runtime_transition_pack2e_to_pack50_20260928.md"
        ),
    })
    rows.append(confirmed)

    terminal_count = 0
    terminal_dest_entry = 0
    terminal_coord = 0
    nonterminal_coord = 0
    terminal53_count = 0
    terminal53_dest_entry = 0
    terminal53_coord = 0
    nonterminal53_coord = 0
    terminal55_count = 0
    terminal55_dest_entry = 0
    terminal55_coord = 0
    nonterminal55_coord = 0
    terminal57_count = 0

    # Conservative static family: bounded substreams whose exact tail is
    # 56 <destination_pack> <destination_entry> B0.
    for script_pack, pack in sorted(packs.items()):
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue

            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                if len(body) < 4 or body[-4] != 0x56 or body[-1] != 0xB0:
                    continue
                dest_pack, dest_entry = body[-3], body[-2]
                if not (cms.FIRST_REAL_PACK <= dest_pack <= cms.LAST_REAL_PACK):
                    continue
                addr = cpu_addr(entry["end"] - 4)
                seen_triggers.add(addr)
                terminal_count += 1

                record_id, event_sources = event_context(script_pack, addr)
                row = blank_row()
                row.update({
                    "script_pack": hx(script_pack),
                    "script_record": record["record_index"],
                    "script_entry": hx(entry["entry_id"]),
                    "trigger_type": "vm_opcode_0x56_terminal",
                    "trigger_addr": addr,
                    "event_record": record_id,
                    "vm_context": (
                        f"pack={hx(script_pack)};record={record['record_index']};"
                        f"entry={hx(entry['entry_id'])}"
                    ),
                    "event_sources": event_sources,
                })
                dest_exists, coord_exists = apply_destination(
                    row, dest_pack, dest_entry
                )
                if dest_exists:
                    terminal_dest_entry += 1
                    row["confidence"] = "strong_candidate"
                    row["condition"] = (
                        f"bounded substream tail; destination record0 entry "
                        f"{hx(dest_entry)} exists"
                    )
                else:
                    row["confidence"] = "structural_candidate"
                    row["condition"] = (
                        f"bounded substream tail; destination record0 entry "
                        f"{hx(dest_entry)} not resolved"
                    )
                if coord_exists:
                    terminal_coord += 1

                    row["condition"] += (
                        f"; destination entry has aligned 0x58 coordinate setter "
                        f"at {row['destination_coordinate_addr']}"
                    )
                row["evidence"] = (
                    "C4:8B6A handler for opcode 0x56 stores operand1 to $15D0/$0305, "
                    "copies old $0305 to $15CF, stores operand2 to $13B8/$13B9, "
                    "calls 81:837F, and advances three bytes; exact bounded tail "
                    "ends in compact B0"
                )
                if coord_exists:
                    row["evidence"] += (
                        "; C4:8BE2 opcode 0x58 writes destination entry operands "
                        "to $1573/$157D/$15C3/$15C4"
                    )
                row["provenance"] = (
                    f"canonical_rom_sha256={sha};"
                    "tools/python/catalog_map_transition_candidates.py;"
                    "tools/python/catalog_map_selectors.py;"
                    "C4:8B6A;C4:8BE2"
                )
                if record_id:
                    row["provenance"] += (
                        ";data/events/event_record_frame_catalog.csv"
                        ";data/events/event_source_crosslink.csv"
                    )
                rows.append(row)

    # Preserve non-terminal shapes only when the destination entry itself has
    # an aligned 0x58 coordinate setter. Opcode boundary at the source remains
    # intentionally unpromoted, so these stay structural candidates.
    for script_pack, pack in sorted(packs.items()):
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue
            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                for pos in range(max(0, len(body) - 2)):
                    if body[pos] != 0x56:
                        continue
                    addr = cpu_addr(entry["start"] + pos)
                    if addr in seen_triggers:
                        continue

                    dest_pack, dest_entry = body[pos + 1], body[pos + 2]
                    if not (cms.FIRST_REAL_PACK <= dest_pack <= cms.LAST_REAL_PACK):
                        continue
                    dent = record0_entry(dest_pack, dest_entry)
                    coord = coordinate_setter(rom, dent)
                    if coord is None:
                        continue

                    record_id, event_sources = event_context(script_pack, addr)
                    row = blank_row()
                    row.update({
                        "script_pack": hx(script_pack),
                        "script_record": record["record_index"],
                        "script_entry": hx(entry["entry_id"]),
                        "trigger_type": "vm_opcode_0x56_nonterminal_shape",
                        "trigger_addr": addr,
                        "event_record": record_id,
                        "vm_context": (
                            f"pack={hx(script_pack)};record={record['record_index']};"
                            f"entry={hx(entry['entry_id'])}"
                        ),
                        "event_sources": event_sources,
                        "confidence": "structural_candidate",
                        "condition": (
                            "source opcode boundary not yet proven; destination "
                            "record0 entry exists and has aligned 0x58 setter"
                        ),
                        "evidence": (
                            "raw 0x56 shape inside a structurally bounded VM substream; "
                            "destination pack/entry cross-links to aligned opcode 0x58 "
                            "coordinate setter; source alignment deliberately unpromoted"
                        ),
                        "provenance": (
                            f"canonical_rom_sha256={sha};"
                            "tools/python/catalog_map_transition_candidates.py;"
                            "C4:8B6A;C4:8BE2"
                        ),
                    })
                    if record_id:
                        row["provenance"] += (
                            ";data/events/event_record_frame_catalog.csv"
                            ";data/events/event_source_crosslink.csv"
                        )
                    apply_destination(row, dest_pack, dest_entry)
                    rows.append(row)
                    seen_triggers.add(addr)
                    nonterminal_coord += 1


    # Opcode 0x53 is a transition wrapper: C4:8B3F performs pre-work and
    # directly JSRs C4:8B6A, so it inherits the same two transition operands.
    for script_pack, pack in sorted(packs.items()):
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue
            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                if len(body) < 4 or body[-4] != 0x53 or body[-1] != 0xB0:
                    continue
                dest_pack, dest_entry = body[-3], body[-2]
                if not (cms.FIRST_REAL_PACK <= dest_pack <= cms.LAST_REAL_PACK):
                    continue
                addr = cpu_addr(entry["end"] - 4)
                seen_triggers.add(addr)
                terminal53_count += 1
                record_id, event_sources = event_context(script_pack, addr)
                row = blank_row()
                row.update({
                    "script_pack": hx(script_pack),
                    "script_record": record["record_index"],
                    "script_entry": hx(entry["entry_id"]),
                    "trigger_type": "vm_opcode_0x53_transition_wrapper_terminal",
                    "trigger_addr": addr,
                    "event_record": record_id,
                    "vm_context": (
                        f"pack={hx(script_pack)};record={record['record_index']};"
                        f"entry={hx(entry['entry_id'])}"
                    ),
                    "event_sources": event_sources,
                })
                dest_exists, coord_exists = apply_destination(row, dest_pack, dest_entry)
                if dest_exists:
                    terminal53_dest_entry += 1
                    row["confidence"] = "strong_candidate"
                    row["condition"] = (
                        f"bounded substream tail; destination record0 entry "
                        f"{hx(dest_entry)} exists"
                    )
                else:
                    row["confidence"] = "structural_candidate"
                    row["condition"] = (
                        f"bounded substream tail; destination record0 entry "
                        f"{hx(dest_entry)} not resolved"
                    )
                if coord_exists:
                    terminal53_coord += 1
                    row["condition"] += (
                        f"; destination entry has aligned 0x58 coordinate setter "
                        f"at {row['destination_coordinate_addr']}"
                    )
                row["evidence"] = (
                    "C4:8B3F opcode 0x53 wrapper calls C4:8B6A transition core; "
                    "the core writes operand1 to $0305 and operand2 to $13B8/$13B9; "
                    "exact bounded tail ends in compact B0"
                )
                if coord_exists:
                    row["evidence"] += (
                        "; C4:8BE2 opcode 0x58 writes destination coordinates"
                    )
                row["provenance"] = (
                    f"canonical_rom_sha256={sha};"
                    "tools/python/catalog_map_transition_candidates.py;"
                    "C4:8B3F;C4:8B6A;C4:8BE2"
                )
                if record_id:
                    row["provenance"] += (
                        ";data/events/event_record_frame_catalog.csv"
                        ";data/events/event_source_crosslink.csv"
                    )
                rows.append(row)


    # Non-terminal 0x53 shapes stay structural unless destination coordinates
    # independently anchor the same destination pack/entry relation.
    for script_pack, pack in sorted(packs.items()):
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue
            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                for pos in range(max(0, len(body) - 2)):
                    if body[pos] != 0x53:
                        continue
                    addr = cpu_addr(entry["start"] + pos)
                    if addr in seen_triggers:
                        continue
                    dest_pack, dest_entry = body[pos + 1], body[pos + 2]
                    if not (cms.FIRST_REAL_PACK <= dest_pack <= cms.LAST_REAL_PACK):
                        continue
                    dent = record0_entry(dest_pack, dest_entry)
                    coord = coordinate_setter(rom, dent)
                    if coord is None:
                        continue
                    record_id, event_sources = event_context(script_pack, addr)
                    row = blank_row()
                    row.update({
                        "script_pack": hx(script_pack),
                        "script_record": record["record_index"],
                        "script_entry": hx(entry["entry_id"]),
                        "trigger_type": "vm_opcode_0x53_nonterminal_shape",
                        "trigger_addr": addr,
                        "event_record": record_id,
                        "vm_context": (
                            f"pack={hx(script_pack)};record={record['record_index']};"
                            f"entry={hx(entry['entry_id'])}"
                        ),
                        "event_sources": event_sources,
                        "confidence": "structural_candidate",
                        "condition": (
                            "source opcode boundary not yet proven; destination "
                            "record0 entry exists and has aligned 0x58 setter"
                        ),
                        "evidence": (
                            "raw 0x53 shape inside bounded VM substream; C4:8B3F "
                            "is the transition wrapper for C4:8B6A; destination "
                            "entry independently has aligned 0x58 coordinates"
                        ),
                        "provenance": (
                            f"canonical_rom_sha256={sha};"
                            "tools/python/catalog_map_transition_candidates.py;"
                            "C4:8B3F;C4:8B6A;C4:8BE2"
                        ),
                    })
                    if record_id:
                        row["provenance"] += (
                            ";data/events/event_record_frame_catalog.csv"
                            ";data/events/event_source_crosslink.csv"
                        )
                    apply_destination(row, dest_pack, dest_entry)
                    rows.append(row)
                    seen_triggers.add(addr)
                    nonterminal53_coord += 1


    # Opcode 0x55 restores an indexed saved map state through 81:8244,
    # preserves the current primary X/Y pair, then falls through to the
    # C4:8B6A transition core. It therefore uses the same explicit
    # <destination_pack> <destination_entry> operand pair as 0x56.
    for script_pack, pack in sorted(packs.items()):
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue
            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                if len(body) < 4 or body[-4] != 0x55 or body[-1] != 0xB0:
                    continue
                dest_pack, dest_entry = body[-3], body[-2]
                if not (cms.FIRST_REAL_PACK <= dest_pack <= cms.LAST_REAL_PACK):
                    continue
                addr = cpu_addr(entry["end"] - 4)
                seen_triggers.add(addr)
                terminal55_count += 1
                record_id, event_sources = event_context(script_pack, addr)
                row = blank_row()
                row.update({
                    "script_pack": hx(script_pack),
                    "script_record": record["record_index"],
                    "script_entry": hx(entry["entry_id"]),
                    "trigger_type": "vm_opcode_0x55_restore_context_terminal",
                    "trigger_addr": addr,
                    "event_record": record_id,
                    "vm_context": (
                        f"pack={hx(script_pack)};record={record['record_index']};"
                        f"entry={hx(entry['entry_id'])}"
                    ),
                    "event_sources": event_sources,
                })
                dest_exists, coord_exists = apply_destination(
                    row, dest_pack, dest_entry
                )
                if dest_exists:
                    terminal55_dest_entry += 1
                    row["confidence"] = "strong_candidate"
                    row["condition"] = (
                        f"bounded substream tail; destination record0 entry "
                        f"{hx(dest_entry)} exists"
                    )
                else:
                    row["confidence"] = "structural_candidate"
                    row["condition"] = (
                        f"bounded substream tail; destination record0 entry "
                        f"{hx(dest_entry)} not resolved"
                    )
                if coord_exists:
                    terminal55_coord += 1
                    row["condition"] += (
                        f"; destination entry has aligned 0x58 coordinate setter "
                        f"at {row['destination_coordinate_addr']}"
                    )
                row["evidence"] = (
                    "C4:8B56 opcode 0x55 saves current $157D/$1573 on the CPU "
                    "stack, calls 81:8244 to restore indexed map state, restores "
                    "the current primary X/Y pair, then falls through to C4:8B6A; "
                    "the transition core writes operand1 to $0305 and operand2 "
                    "to $13B8/$13B9"
                )
                if coord_exists:
                    row["evidence"] += (
                        "; C4:8BE2 opcode 0x58 writes destination coordinates"
                    )
                row["provenance"] = (
                    f"canonical_rom_sha256={sha};"
                    "tools/python/catalog_map_transition_candidates.py;"
                    "C4:8B56;C1:8244;C4:8B6A;C4:8BE2"
                )
                if record_id:
                    row["provenance"] += (
                        ";data/events/event_record_frame_catalog.csv"
                        ";data/events/event_source_crosslink.csv"
                    )
                rows.append(row)

    # Non-terminal 0x55 shapes are kept only when destination coordinates
    # independently anchor the destination pack/entry relationship.
    for script_pack, pack in sorted(packs.items()):
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue
            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                for pos in range(max(0, len(body) - 2)):
                    if body[pos] != 0x55:
                        continue
                    addr = cpu_addr(entry["start"] + pos)
                    if addr in seen_triggers:
                        continue
                    dest_pack, dest_entry = body[pos + 1], body[pos + 2]
                    if not (cms.FIRST_REAL_PACK <= dest_pack <= cms.LAST_REAL_PACK):
                        continue
                    dent = record0_entry(dest_pack, dest_entry)
                    coord = coordinate_setter(rom, dent)
                    if coord is None:
                        continue
                    record_id, event_sources = event_context(script_pack, addr)
                    row = blank_row()
                    row.update({
                        "script_pack": hx(script_pack),
                        "script_record": record["record_index"],
                        "script_entry": hx(entry["entry_id"]),
                        "trigger_type": "vm_opcode_0x55_nonterminal_shape",
                        "trigger_addr": addr,
                        "event_record": record_id,
                        "vm_context": (
                            f"pack={hx(script_pack)};record={record['record_index']};"
                            f"entry={hx(entry['entry_id'])}"
                        ),
                        "event_sources": event_sources,
                        "confidence": "structural_candidate",
                        "condition": (
                            "source opcode boundary not yet proven; destination "
                            "record0 entry exists and has aligned 0x58 setter"
                        ),
                        "evidence": (
                            "raw 0x55 shape inside bounded VM substream; C4:8B56 "
                            "restores saved map context then falls through to the "
                            "C4:8B6A transition core; destination entry independently "
                            "has aligned 0x58 coordinates"
                        ),
                        "provenance": (
                            f"canonical_rom_sha256={sha};"
                            "tools/python/catalog_map_transition_candidates.py;"
                            "C4:8B56;C1:8244;C4:8B6A;C4:8BE2"
                        ),
                    })
                    if record_id:
                        row["provenance"] += (
                            ";data/events/event_record_frame_catalog.csv"
                            ";data/events/event_source_crosslink.csv"
                        )
                    apply_destination(row, dest_pack, dest_entry)
                    rows.append(row)
                    seen_triggers.add(addr)
                    nonterminal55_coord += 1


    # Opcode 0x57 selects one of the 16 native C6:8000 route-stack
    # definitions. Only exact terminal 57 <index> B0 forms are promoted here;
    # non-terminal raw 0x57 shapes remain unpromoted until source opcode
    # alignment is proven.
    for script_pack, pack in sorted(packs.items()):
        for record in pack["records"]:
            if (script_pack, record["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:
                continue
            header = cms.parse_record_header(rom, record)
            if not header:
                continue
            for entry in header["entries"]:
                body = rom[entry["start"]:entry["end"]]
                if len(body) < 3 or body[-3] != 0x57 or body[-1] != 0xB0:
                    continue
                route_index = body[-2]
                route = route57_final(route_index)
                if route is None:
                    continue
                addr = cpu_addr(entry["end"] - 3)
                seen_triggers.add(addr)
                terminal57_count += 1
                record_id, event_sources = event_context(script_pack, addr)

                row = blank_row()
                row.update({
                    "script_pack": hx(script_pack),
                    "script_record": record["record_index"],
                    "script_entry": hx(entry["entry_id"]),
                    "trigger_type": "vm_opcode_0x57_native_route_terminal",
                    "trigger_addr": addr,
                    "event_record": record_id,
                    "vm_context": (
                        f"pack={hx(script_pack)};record={record['record_index']};"
                        f"entry={hx(entry['entry_id'])}"
                    ),
                    "event_sources": event_sources,
                    "destination_pack": hx(route["pack_id"]),
                    "destination_x": route["x"],
                    "destination_y": route["y"],
                    "confidence": "strong_candidate",
                    "condition": (
                        f"exact bounded tail 57 {hx(route_index)} B0; "
                        f"C4:8BD4 guard $13B8 != 0; route_ptr={route['route_ptr']}; "
                        f"context_0306={hx(route['context_0306'])}; "
                        f"destination_entrance={hx(route['entrance'])}"
                    ),
                    "evidence": (
                        "C4:8BD4 opcode 0x57 reads one route-index operand when "
                        "$13B8 != 0 and JSLs 86:8000 (LoROM mirror of C6:8000). "
                        "C6:8000 doubles the index, loads a route pointer from "
                        "C6:8060, clears the saved-map-state stack via 81:8204, "
                        "walks [pack,x,y,entrance] nodes, saves non-final nodes "
                        "through 81:8207, and leaves the final node active"
                    ),
                    "provenance": (
                        f"canonical_rom_sha256={sha};"
                        "tools/python/catalog_map_transition_candidates.py;"
                        "C4:8BD4;C6:8000;C6:8060;81:8204;81:8207"
                    ),
                })
                cfg = destination_config(route["pack_id"])
                if cfg:
                    row["destination_config_id"] = cfg["config_id"]
                    row["destination_layout"] = cfg["primary_layout_id"]
                    row["destination_tileset"] = cfg["primary_tileset_id"]
                    row["destination_variant"] = cfg["map_variant"]
                if record_id:
                    row["provenance"] += (
                        ";data/events/event_record_frame_catalog.csv"
                        ";data/events/event_source_crosslink.csv"
                    )
                rows.append(row)


    # Promote static transition rows only when a canonical runtime evidence file
    # names the exact static trigger and all destination fields agree.
    runtime_static_confirmation_count = 0
    runtime_static_confirmation_triggers: list[str] = []
    transitions_dir = root / "data/maps/transitions"
    for evidence_path in sorted(transitions_dir.glob("*.json")):
        try:
            runtime_evidence = json.loads(evidence_path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if runtime_evidence.get("kind") != "runtime_map_transition_evidence":
            continue
        static_match = runtime_evidence.get("trigger", {}).get("static_match")
        if not static_match or not static_match.get("trigger_addr"):
            continue

        trigger_addr = static_match["trigger_addr"]
        matches = [r for r in rows if r["trigger_addr"] == trigger_addr]
        if len(matches) != 1:
            raise SystemExit(
                f"runtime confirmation {evidence_path.name} expected exactly one "
                f"static row for {trigger_addr}, found {len(matches)}"
            )
        row = matches[0]

        expected_pairs = {
            "script_pack": static_match.get("script_pack", ""),
            "destination_pack": static_match.get("destination_pack", ""),
            "destination_entry_id": static_match.get("destination_entry_id", ""),
        }
        for key, expected in expected_pairs.items():
            if expected and row[key] != expected:
                raise SystemExit(
                    f"runtime confirmation mismatch {evidence_path.name}: "
                    f"{key} static={row[key]!r} runtime={expected!r}"
                )

        destination = runtime_evidence.get("to", {})
        coord = destination.get("coordinate", {})
        if coord:
            if str(coord.get("x", "")) != str(row["destination_x"]):
                raise SystemExit(
                    f"runtime confirmation x mismatch at {trigger_addr}: "
                    f"static={row['destination_x']} runtime={coord.get('x')}"
                )
            if str(coord.get("y", "")) != str(row["destination_y"]):
                raise SystemExit(
                    f"runtime confirmation y mismatch at {trigger_addr}: "
                    f"static={row['destination_y']} runtime={coord.get('y')}"
                )

        source = runtime_evidence.get("from", {})
        source_selector = source.get("selector", {})
        row["source_config_id"] = source.get("config_id", "")
        row["source_pack"] = source.get("pack_id_hex", "")
        row["source_layout"] = source_selector.get("primary_layout", "")
        row["source_tileset"] = source_selector.get("primary_tileset", "")
        row["confidence"] = "confirmed"
        row["condition"] += (
            f"; runtime frame {runtime_evidence.get('trigger', {}).get('observed_frame')} "
            f"confirms {row['source_pack']} -> {row['destination_pack']}"
        )
        row["evidence"] += (
            f"; runtime $0305 switch at frame "
            f"{runtime_evidence.get('trigger', {}).get('observed_frame')} and "
            f"arrival coordinates ({row['destination_x']},{row['destination_y']}) "
            f"match the static destination entry"
        )
        visible_name = destination.get("human_location_name")
        if visible_name:
            row["evidence"] += f"; visible destination label={visible_name}"
        row["provenance"] += (
            f";data/maps/transitions/{evidence_path.name}"
        )
        runtime_static_confirmation_count += 1
        runtime_static_confirmation_triggers.append(trigger_addr)

    # Runtime-only edges can be projected into the catalog even when the
    # exact execution PC was not captured. These remain confirmed edges while
    # any proposed static mechanism keeps its own lower confidence in evidence.
    runtime_only_confirmation_count = 0
    for evidence_path in sorted(transitions_dir.glob("*.json")):
        try:
            runtime_evidence = json.loads(evidence_path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if runtime_evidence.get("kind") != "runtime_map_transition_evidence":
            continue
        projection = runtime_evidence.get("catalog_projection")
        if not projection:
            continue
        if runtime_evidence.get("relation_status") != "confirmed_runtime_transition":
            raise SystemExit(
                f"runtime-only projection {evidence_path.name} is not a confirmed edge"
            )

        source = runtime_evidence.get("from", {})
        destination = runtime_evidence.get("to", {})
        source_selector = source.get("selector", {})
        dest_selector = destination.get("selector", {})
        coord = destination.get("coordinate", {})
        trigger = runtime_evidence.get("trigger", {})
        mechanism = runtime_evidence.get("mechanism", {})

        row = blank_row()
        row.update({
            "source_config_id": source.get("config_id", ""),
            "source_pack": source.get("pack_id_hex", ""),
            "source_layout": source_selector.get("primary_layout", ""),
            "source_tileset": source_selector.get("primary_tileset", ""),
            "trigger_type": projection.get("trigger_type", "runtime_only_transition"),
            "trigger_addr": projection.get("trigger_addr", ""),
            "destination_pack": destination.get("pack_id_hex", ""),
            "destination_config_id": destination.get("config_id", ""),
            "destination_layout": dest_selector.get("primary_layout", ""),
            "destination_tileset": dest_selector.get("primary_tileset", ""),
            "destination_variant": dest_selector.get("map_variant", ""),
            "destination_x": coord.get("x", ""),
            "destination_y": coord.get("y", ""),
            "confidence": projection.get("confidence", "confirmed"),
            "condition": (
                f"runtime frame {trigger.get('observed_frame')} confirms "
                f"{source.get('pack_id_hex', '')} -> "
                f"{destination.get('pack_id_hex', '')}; exact execution PC not observed"
            ),
            "evidence": (
                f"atomic capture hash={trigger.get('atomic_capture_sha256', '')}; "
                f"arrival selector="
                f"{dest_selector.get('primary_tileset', '')}/"
                f"{dest_selector.get('primary_layout', '')}/"
                f"{dest_selector.get('map_variant', '')}; "
                f"arrival coordinate=({coord.get('x', '')},{coord.get('y', '')}); "
                f"mechanism={mechanism.get('status', 'unresolved')}"
            ),
            "provenance": f"data/maps/transitions/{evidence_path.name}",
        })
        mechanism_addr = projection.get("mechanism_addr", "")
        if mechanism_addr:
            row["evidence"] += (
                f"; candidate mechanism writer={mechanism_addr} "
                f"(execution PC not observed)"
            )
        rows.append(row)
        runtime_only_confirmation_count += 1


    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    native_0305_writers = []
    needle = bytes.fromhex("8D 05 03")
    pos = 0
    while True:
        pos = rom.find(needle, pos)
        if pos < 0:
            break
        addr = cpu_addr(pos)
        if addr != "C4:8B7B":
            native_0305_writers.append(addr)
        pos += 1

    confidence_counts = Counter(r["confidence"] for r in rows)
    destination_pack_count = sum(bool(r["destination_pack"]) for r in rows)
    destination_config_count = sum(bool(r["destination_config_id"]) for r in rows)
    coordinate_count = sum(
        r["destination_x"] != "" and r["destination_y"] != ""
        for r in rows
    )
    event_record_count = sum(bool(r["event_record"]) for r in rows)
    event_source_count = sum(bool(r["event_sources"]) for r in rows)
    unique_destination_packs = sorted({
        r["destination_pack"] for r in rows if r["destination_pack"]
    })

    summary = {
        "schema_version": 1,
        "kind": "map_transition_candidate_catalog",
        "generated_against_git_head": current_head(root),
        "rom_sha256": sha,
        "candidate_count": len(rows),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "source_config_resolved_count": sum(bool(r["source_config_id"]) for r in rows),
        "runtime_static_confirmation_count": runtime_static_confirmation_count,
        "runtime_static_confirmation_triggers": runtime_static_confirmation_triggers,
        "runtime_only_confirmation_count": runtime_only_confirmation_count,
        "destination_pack_identified_count": destination_pack_count,
        "destination_config_resolved_count": destination_config_count,
        "destination_coordinate_resolved_count": coordinate_count,
        "event_record_crosslink_count": event_record_count,
        "event_source_crosslink_count": event_source_count,
        "additional_native_0305_writer_sites": native_0305_writers,
        "unique_destination_pack_count": len(unique_destination_packs),
        "terminal_opcode56_candidate_count": terminal_count,
        "terminal_opcode56_destination_entry_match_count": terminal_dest_entry,
        "terminal_opcode56_coordinate_match_count": terminal_coord,
        "nonterminal_opcode56_coordinate_crosslink_count": nonterminal_coord,
        "terminal_opcode53_candidate_count": terminal53_count,
        "terminal_opcode53_destination_entry_match_count": terminal53_dest_entry,
        "terminal_opcode53_coordinate_match_count": terminal53_coord,
        "nonterminal_opcode53_coordinate_crosslink_count": nonterminal53_coord,
        "terminal_opcode55_candidate_count": terminal55_count,
        "terminal_opcode55_destination_entry_match_count": terminal55_dest_entry,
        "terminal_opcode55_coordinate_match_count": terminal55_coord,
        "nonterminal_opcode55_coordinate_crosslink_count": nonterminal55_coord,
        "terminal_opcode57_route_candidate_count": terminal57_count,
        "handler_findings": {
            "opcode_0x53": {
                "handler": "C4:8B3F",
                "instruction_length": 3,
                "effect": (
                    "transition wrapper; performs pre-work then JSR C4:8B6A, "
                    "therefore sharing the 0x56 destination-pack/entry core"
                ),
            },
            "opcode_0x55": {
                "handler": "C4:8B56",
                "instruction_length": 3,
                "effect": (
                    "save current primary X/Y on CPU stack; JSL 81:8244 to "
                    "restore indexed saved map state; restore current primary X/Y; "
                    "fall through to C4:8B6A destination-pack/entry transition core"
                ),
            },
            "opcode_0x56": {
                "handler": "C4:8B6A",
                "instruction_length": 3,
                "effect": (
                    "operand1 -> $15D0 and $0305; old $0305 -> $15CF; "
                    "operand2 -> $13B8/$13B9; JSL 81:837F"
                ),
            },
            "opcode_0x57": {
                "handler": "C4:8BD4",
                "instruction_length": 2,
                "guard": "$13B8 != 0",
                "effect": (
                    "operand is route index; JSL 86:8000/C6:8000; index selects "
                    "C6:8060 pointer table; route stack leaves final pack/x/y/entrance active"
                ),
            },
            "opcode_0x58": {
                "handler": "C4:8BE2",
                "instruction_length": 5,
                "guard": "$13B8 != 0",
                "effect": (
                    "four operands -> $1573/$157D/$15C3/$15C4"
                ),
            },
        },

        "unresolved_patterns": [
            "static source map/config is not inferred from script-pack identity",
            "five terminal 0x56 shapes and twenty-one terminal 0x53 shapes do not resolve a destination record0 entry",
            "non-terminal 0x53/0x55/0x56 shapes remain structural unless source instruction alignment is proven",
            "non-terminal raw 0x57 route-index shapes are not promoted until source opcode alignment is proven",
            "destination config stays null when destination pack record0/entry1 has multiple confirmed selectors",
            "0x58 coordinate setter is promoted only at entry start or after proven two-byte opcode 0x96 prefix",
            "exact trigger/event opcode for the runtime-confirmed 0x2E -> 0x50 edge remains unidentified",
            "opcode 0x04 changes VM pack context $126E and is not promoted as a map transition by itself",
            "event-record crosslink coverage is partial; rows outside the structural frame catalog retain vm_context only",
            "native STA $0305 restore/context writers outside the explicit 0x53/0x55/0x56 destination operand grammar remain separately inventoried",
        ],
    }
    args.summary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    doc = """# Map transition candidate catalog

Updated: 2026-09-29

## Scope

This pass catalogs map-transition candidates only. It does not implement the
HTML viewer and does not integrate NPC or sprite data.

Canonical ROM SHA-256: {sha}
Git HEAD used for generation: {head}

## Handler-level promotion

Normal VM opcode 0x53 dispatches to C4:8B3F, performs transition pre-work,
then directly JSRs C4:8B6A. It therefore shares the same two transition
operands and three-byte advance as the 0x56 core.

Normal VM opcode 0x55 dispatches to C4:8B56. It saves the current primary
X/Y pair on the CPU stack, calls 81:8244 to restore an indexed saved map state,
restores the current primary X/Y pair, and then falls through to the C4:8B6A
transition core. It therefore also consumes destination pack/entry operands.

Normal VM opcode 0x56 dispatches to C4:8B6A and is three bytes total.
The handler copies the old global map pack $0305 to $15CF, writes operand 1
to both $15D0 and $0305, writes operand 2 to $13B8/$13B9, calls
81:837F, clears $1984, and advances by three bytes.

Normal VM opcode 0x57 dispatches to C4:8BD4. When $13B8 != 0, its one-byte
operand is passed to 86:8000, the LoROM mirror of C6:8000. C6:8000 doubles
the route index, loads a route pointer from C6:8060, builds saved map-state
nodes, and leaves the final pack/X/Y/entrance active.

Normal VM opcode 0x58 dispatches to C4:8BE2. When $13B8 != 0, its four
operands are written to primary map coordinates $1573/$157D and secondary
map coordinates $15C3/$15C4. Existing map analysis independently identifies
these fields as current-map coordinates.
""".format(sha=sha, head=summary["generated_against_git_head"])

    doc += """
## Confidence policy

- confirmed: preserved runtime-observed transition evidence.
- strong_candidate: an exact bounded VM-substream tail of
  53 <destination_pack> <destination_entry> B0,
  55 <destination_pack> <destination_entry> B0, or
  56 <destination_pack> <destination_entry> B0, with the same destination
  entry present in destination record 0. Exact terminal
  57 <route_index> B0 is also strong_candidate when route_index resolves through
  the proven C6:8060 route table.
- structural_candidate: a terminal form whose destination entry is unresolved,
  or a non-terminal raw 0x53/0x55/0x56 shape retained only because its
  destination entry independently contains an aligned 0x58 coordinate setter.

The script-pack containing 0x53/0x55/0x56 is not automatically treated as the source map
pack. VM pack context and global map pack can differ, so static source map fields
remain blank unless independently proven.

## Counts

- total candidate rows: {candidate_count}
- confirmed: {confirmed}
- strong candidates: {strong}
- structural candidates: {structural}
- rows with source configuration: {source_configs}
- runtime-confirmed static triggers: {runtime_static}
- runtime-confirmed edges without observed trigger PC: {runtime_only}
- rows with destination pack: {dest_pack}
- rows with unique destination configuration: {dest_config}
- rows with destination X/Y: {coords}
- rows cross-linked to structural event records: {event_records}
- rows carrying existing event-source xrefs: {event_sources}
- terminal 0x56 forms: {terminal56}
- terminal 0x56 forms with matching destination entry: {terminal56_entry}
- terminal 0x56 forms with aligned destination 0x58 coordinates: {terminal56_coords}
- non-terminal 0x56 coordinate-crosslinked structural rows: {nonterminal56}
- terminal 0x53 forms: {terminal53}
- terminal 0x53 forms with matching destination entry: {terminal53_entry}
- terminal 0x53 forms with aligned destination 0x58 coordinates: {terminal53_coords}
- non-terminal 0x53 coordinate-crosslinked structural rows: {nonterminal53}
- terminal 0x55 forms: {terminal55}
- terminal 0x55 forms with matching destination entry: {terminal55_entry}
- terminal 0x55 forms with aligned destination 0x58 coordinates: {terminal55_coords}
- non-terminal 0x55 coordinate-crosslinked structural rows: {nonterminal55}
- terminal 0x57 route-table forms: {terminal57}

Opcode 0x54 is destination-indirect: it requests a saved-map-state return
rather than encoding a destination beside the opcode. Its exact terminal forms
are cataloged separately in saved_state_return_candidates.csv.

## Runtime-confirmed anchor

Three runtime anchors are now preserved.

The earlier trace confirms cfg_t07_l015_v2 / pack 0x2E transitions to
cfg_t04_l008_v2 / pack 0x50. During that transition, $0305 changes first,
then $126E/$12B4 converge to 0x50, and selector 4/8/2 becomes active.
The exact event opcode address for that interior-to-exterior edge remains unknown.

The 2026-09-29 world-map trace confirms cfg_t01_l001_v1 / pack 0x4C at
coordinate (54,236) entering pack 0x50. At frame 14455 $0305 changes
0x4C -> 0x50. The only matching terminal 0x53 static row in script pack 0x4C
is record 2 / entry 0x77 / trigger CC:0B08, targeting destination entry 0x02.
That entry's aligned 0x58 setter at CC:1C4E predicts (29,55), and runtime
coordinates become exactly (29,55) by frame 14657. The visible destination
label is 旅立ちの村. This promotes CC:0B08 from strong_candidate to confirmed.

A second 2026-09-29 trace captures the reverse edge from 旅立ちの村 /
cfg_t04_l008_v2 / pack 0x50 back to cfg_t01_l001_v1 / pack 0x4C.
During a Down atomic capture, $0305 changes 0x50 -> 0x4C at frame 14787
while the active DP pointer remains CD:FA4F. By frame 14937 selector 1/1/1 is
active under pack 0x4C at coordinate (54,237). The edge is confirmed, but the
exact execution PC was not captured. C1:8244/C1:8255 saved-map-state restore is
therefore recorded only as a strong mechanism candidate, not as the observed
trigger address.

## Important structural finding

The second transition operand used by 0x53, 0x55 and 0x56 behaves as a
destination entry selector. Across the conservative terminal corpus,
destination record 0 contains the same entry ID for
{terminal_matches} of {terminal_total} rows. Where that entry begins with opcode
0x58, or with the independently proven two-byte 0x96 prefix followed by 0x58,
the arrival/current-map coordinates can be extracted without guessing.

For pack 0x50, the independently found 0x56 shapes using entry IDs 0x04, 0x0B
and 0x10 cross-link to record-0 entries carrying 0x58 coordinate setters,
including coordinates (29,55) and (34,49).

Opcode 0x57 forms a second transition grammar: the operand is a native route
index rather than a destination pack. Two exact terminal forms are currently
proven, route index 3 ending at pack 0x50 / (39,37) / entrance 0x02 and route
index 14 ending at pack 0x6A / (88,20) / entrance 0x02.

## Deliberate non-promotions

Opcode 0x04 is a proven VM pack-context switch for $126E, but it is not treated
as a global map transition because it does not itself write $0305.

Raw 0x53/0x55/0x56-shaped bytes outside the bounded policy are not cataloged.
Non-terminal shapes are retained only when a destination-entry/0x58 coordinate cross-link
provides an independent structural anchor.

## Related state fields

- $0305 is the global current-map pack field written by the C4:8B6A core used by opcodes 0x53, 0x55 and 0x56.
- $126E is VM pack context. Opcode 0x04 changes $126E, so it is useful context
  but is not sufficient evidence for a global map transition.
- $12B4 is the resolved current source family/pack context used by source
  selection. In the confirmed runtime transition it converges with $126E after
  $0305 has already changed.
- normal opcode 0x50 writes primary selector state $139C/$139E/$139B
  (tileset/layout/variant).
- normal opcode 0x51 writes secondary selector state $139D/$139F.
- the destination configuration columns are therefore joined from the existing
  confirmed 0x50 selector catalog, not inferred from the transition operands.
- data/events/event_record_frame_catalog.csv is range-joined against each
  trigger address. Matching record IDs are stored in event_record.
- data/events/event_source_crosslink.csv is then joined by record ID and stored
  in event_sources. Rows outside the structural frame catalog keep event_record
  blank while vm_context preserves script pack/record/entry without guessing.

## Additional native $0305 writer inventory

Outside C4:8B7B inside opcode 0x56, exact STA-absolute $0305 byte patterns occur
at: {native_writers}

These sites are separately inventoried because some are save/restore or
temporary-context writes rather than explicit destination operands. Runtime-only
edges may still use them as mechanism candidates without claiming the execution
PC was observed.

## Reproducible outputs

- data/maps/transitions/map_transition_candidates.csv
- data/maps/transitions/map_transition_candidates_summary.json
- docs/analysis/map_transition_candidate_catalog.md
- tools/python/catalog_map_transition_candidates.py
- data/maps/transitions/world_pack4c_to_pack50_entry02_20260929.json
- data/maps/transitions/tabidachi_village_to_world_pack4c_restore_20260929.json
- data/maps/transitions/saved_state_return_candidates.csv
- data/maps/transitions/saved_state_return_summary.json
- docs/analysis/map_saved_state_return_catalog.md
- tools/python/catalog_saved_state_return_candidates.py

## Remaining blockers

""".format(
        candidate_count=summary["candidate_count"],
        confirmed=confidence_counts.get("confirmed", 0),
        strong=confidence_counts.get("strong_candidate", 0),
        structural=confidence_counts.get("structural_candidate", 0),
        source_configs=summary["source_config_resolved_count"],
        runtime_static=runtime_static_confirmation_count,
        runtime_only=runtime_only_confirmation_count,
        dest_pack=destination_pack_count,
        dest_config=destination_config_count,
        coords=coordinate_count,
        event_records=event_record_count,
        event_sources=event_source_count,
        native_writers=", ".join(native_0305_writers),
        terminal56=terminal_count,
        terminal56_entry=terminal_dest_entry,
        terminal56_coords=terminal_coord,
        nonterminal56=nonterminal_coord,
        terminal53=terminal53_count,
        terminal53_entry=terminal53_dest_entry,
        terminal53_coords=terminal53_coord,
        nonterminal53=nonterminal53_coord,
        terminal55=terminal55_count,
        terminal55_entry=terminal55_dest_entry,
        terminal55_coords=terminal55_coord,
        nonterminal55=nonterminal55_coord,
        terminal57=terminal57_count,
        terminal_matches=terminal_dest_entry + terminal53_dest_entry + terminal55_dest_entry,
        terminal_total=terminal_count + terminal53_count + terminal55_count,
    )

    for item in summary["unresolved_patterns"]:
        doc += "- " + item + "\n"
    args.doc.parent.mkdir(parents=True, exist_ok=True)
    args.doc.write_text(doc, encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
