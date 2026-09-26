#!/usr/bin/env python3
"""Catalog structurally anchored Shinmomo event-record frames.

The canonical CA:C000 script-pack intervals contain a recurring trailer:

    7A <body16> 7C <next_plus_1_16> 00

A candidate is accepted only when body16 resolves exactly to the byte after
this 7-byte trailer and next_plus_1 resolves forward inside the same pack.
A linked record is then formed from two adjacent candidates when the previous
candidate's next boundary is a B0 byte and lies before the current trailer.

This intentionally catalogs framing only. It does not assign opcode semantics,
source-selection semantics, speaker identity, or runtime reachability.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict, Counter
from pathlib import Path

EXPECTED_SIZE = 2_097_152
EXPECTED_SHA256 = "F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"
CA_BOUNDARY_OFFSET = 0x0AC000
FIRST_REAL_PACK = 0x14
LAST_REAL_PACK = 0xF9
FINAL_SENTINEL_INDEX = 0xFA


def cpu_from_file(off: int) -> str:
    return f"{0xC0 + (off >> 16):02X}:{off & 0xFFFF:04X}"


def file_from_cpu(bank: int, addr: int) -> int:
    return ((bank - 0xC0) << 16) | addr


def read_ca_boundaries(rom: bytes) -> list[dict]:
    rows = []
    for idx in range(FINAL_SENTINEL_INDEX + 1):
        off = CA_BOUNDARY_OFFSET + idx * 3
        lo, hi, bank = rom[off:off + 3]
        addr = lo | (hi << 8)
        rows.append({
            "index": idx,
            "bank": bank,
            "addr": addr,
            "file": file_from_cpu(bank, addr),
            "cpu": f"{bank:02X}:{addr:04X}",
        })
    return rows


def ptr16_to_file_near(off: int, addr16: int) -> int:
    """Interpret a 16-bit in-pack pointer in the bank containing off."""
    bank_index = off >> 16
    return (bank_index << 16) | addr16


def find_trailers(rom: bytes, family: int, start: int, end: int) -> list[dict]:
    rows = []
    for p in range(start, max(start, end - 6)):
        if not (rom[p] == 0x7A and rom[p + 3] == 0x7C and rom[p + 6] == 0x00):
            continue
        body16 = rom[p + 1] | (rom[p + 2] << 8)
        next_plus_1 = rom[p + 4] | (rom[p + 5] << 8)
        body = ptr16_to_file_near(p, body16)
        next_start = ptr16_to_file_near(p, (next_plus_1 - 1) & 0xFFFF)
        if next_start < p and (p >> 16) + 1 <= 0x1F:
            next_start += 0x10000
        if body < p and (p >> 16) + 1 <= 0x1F:
            body += 0x10000
        if not (start <= body < next_start <= end):
            continue
        if body != p + 7:
            continue
        rows.append({
            "family": family,
            "trailer": p,
            "body": body,
            "next_start": next_start,
            "body16": body16,
            "next_plus_1": next_plus_1,
        })
    return rows


def build_records(rom: bytes, family: int, trailers: list[dict]) -> list[dict]:
    trailers = sorted(trailers, key=lambda r: r["trailer"])
    records = []
    for seq, (prev, cur) in enumerate(zip(trailers, trailers[1:]), start=1):
        start = prev["next_start"]
        if not (start <= cur["trailer"] < cur["body"] < cur["next_start"]):
            continue
        start_marker = rom[start]
        if start_marker != 0xB0:
            continue
        records.append({
            "family_id": family,
            "family_hex": f"0x{family:02X}",
            "record_seq": seq,
            "record_id": f"F{family:02X}-L{seq:03d}",
            "record_start": cpu_from_file(start),
            "trailer_start": cpu_from_file(cur["trailer"]),
            "body_start": cpu_from_file(cur["body"]),
            "record_end_exclusive": cpu_from_file(cur["next_start"]),
            "record_size": cur["next_start"] - start,
            "pre_trailer_size": cur["trailer"] - start,
            "trailer_size": 7,
            "body_size": cur["next_start"] - cur["body"],
            "start_marker": "0xB0",
            "trailer_grammar": "7A_body16_7C_next_plus_1_16_00",
            "evidence_class": "strong_structural_frame",
            "semantic_status": "unclassified",
        })
    return records


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--out-dir", type=Path, default=Path("data/events"))
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    sha = hashlib.sha256(rom).hexdigest().upper()
    if len(rom) != EXPECTED_SIZE:
        raise SystemExit(f"unexpected ROM size: {len(rom)}")
    if sha != EXPECTED_SHA256:
        raise SystemExit(f"unexpected ROM SHA-256: {sha}")

    ca = read_ca_boundaries(rom)
    trailers_by_family: dict[int, list[dict]] = defaultdict(list)
    records = []
    for family in range(FIRST_REAL_PACK, LAST_REAL_PACK + 1):
        start = ca[family]["file"]
        end = ca[family + 1]["file"]
        trailers = find_trailers(rom, family, start, end)
        if trailers:
            trailers_by_family[family] = trailers
            records.extend(build_records(rom, family, trailers))

    args.out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.out_dir / "event_record_frame_catalog.csv"
    if records:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
            w.writeheader()
            w.writerows(records)

    header_sizes = Counter(r["pre_trailer_size"] for r in records)
    body_sizes = Counter(r["body_size"] for r in records)
    summary = {
        "rom_sha256": sha,
        "real_script_pack_count": LAST_REAL_PACK - FIRST_REAL_PACK + 1,
        "families_with_valid_trailer": len(trailers_by_family),
        "valid_trailer_candidates": sum(len(v) for v in trailers_by_family.values()),
        "linked_b0_structural_records": len(records),
        "record_family_count": len({r["family_id"] for r in records}),
        "start_marker_invariant": "all emitted linked records start with 0xB0",
        "trailer_invariant": "7A body16 7C next_record_plus_1_16 00; body16 == byte after trailer",
        "semantic_scope": "structural framing only; not a claim of event meaning, source selection, speaker, or runtime reachability",
        "most_common_pre_trailer_sizes": [[k, v] for k, v in header_sizes.most_common(12)],
        "most_common_body_sizes": [[k, v] for k, v in body_sizes.most_common(12)],
        "family_0x50_linked_records": sum(r["family_id"] == 0x50 for r in records),
    }
    (args.out_dir / "event_record_frame_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
