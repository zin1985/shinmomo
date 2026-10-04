#!/usr/bin/env python3
"""Decode usage-driven Shinmomo dialogue source pairs to readable Japanese.

This tool reuses the canonical source-family readers in catalog_dialogue_sources.py:
mode 0 = raw, mode 1 = C0:BD28 ring decoder, mode 2 = C0:BD98 tree decoder.

Character rendering is taken from the checked v28 dialogue Lua table.  The tool
never scans arbitrary subindices by default; it decodes only pairs already
present in source_pair_usage_catalog.csv, avoiding source-stream overrun noise.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
CATALOG_TOOL = HERE / "catalog_dialogue_sources.py"
DEFAULT_USAGE = REPO / "data/dialogue/source_pair_usage_catalog.csv"
DEFAULT_LUA = REPO / "scripts/lua/dialogue/shinmomo_trace_dialogue_v28_mode02_bd98_decoder_smallkana_checked_snes9x_20260427.lua"


def load_catalog_module():
    spec = importlib.util.spec_from_file_location("shinmomo_catalog_dialogue_sources", CATALOG_TOOL)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {CATALOG_TOOL}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_render_tables(lua_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    text = lua_path.read_text(encoding="utf-8", errors="replace")
    if "local MOMO3 = {" not in text:
        raise ValueError("MOMO3 table not found")
    momo_block = text.split("local MOMO3 = {", 1)[1].split("}", 1)[0]
    momo = dict(re.findall(r'\["([^"]+)"\]\s*=\s*"([^"]*)"', momo_block))
    # Apply explicit corrections later in the Lua source (small kana etc.).
    for key, value in re.findall(r'MOMO3\["([^"]+)"\]\s*=\s*"([^"]*)"', text):
        momo[key] = value

    dictionary: dict[str, str] = {}
    if "local DICT02 = {" in text:
        dict_block = text.split("local DICT02 = {", 1)[1].split("}", 1)[0]
        dictionary.update(re.findall(r'\["([^"]+)"\]\s*=\s*"([^"]*)"', dict_block))
    return momo, dictionary


def render_record(record: list[int], momo: dict[str, str], dictionary: dict[str, str]) -> str:
    out: list[str] = []
    i = 0
    while i < len(record):
        token = record[i]
        if token == 0x00:
            break
        if token == 0x01:
            out.append("\n")
            i += 1
            continue
        if token == 0x02 and i + 1 < len(record):
            low = record[i + 1]
            out.append(dictionary.get(f"{low:02X}", f"{{02{low:02X}}}"))
            i += 2
            continue
        if 0x18 <= token < 0x20 and i + 1 < len(record):
            low = record[i + 1]
            key = f"{token:02X}{low:02X}"
            out.append(momo.get(key, f"{{K{key}}}"))
            i += 2
            continue
        out.append(momo.get(f"{token:02X}", f"{{{token:02X}}}"))
        i += 1
    return "".join(out)


def read_usage_pairs(path: Path, families: set[int] | None) -> list[dict]:
    pairs: dict[tuple[int, int], dict] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            family = int(row["family_id"])
            if families is not None and family not in families:
                continue
            subindex = int(row["subindex"])
            pairs[(family, subindex)] = {
                "family": family,
                "subindex": subindex,
                "selected_source_cpu": row.get("selected_source_cpu", ""),
                "script_cpus": row.get("script_cpus", ""),
                "evidence_classes": row.get("evidence_classes", ""),
            }
    return [pairs[key] for key in sorted(pairs)]


def decode_pair(rom: bytes, entries, cat, usage: dict,
                momo: dict[str, str], dictionary: dict[str, str]) -> dict:
    family = usage["family"]
    subindex = usage["subindex"]
    entry = entries[family]
    base = {
        "family_id": family,
        "family_hex": f"0x{family:02X}",
        "subindex": subindex,
        "subindex_hex": f"0x{subindex:02X}",
        "source_root": f"{entry['bank']:02X}:{entry['addr']:04X}",
        "source_mode": entry["mode"],
    }

    override = cat.special_override(rom, family, subindex)
    if override is not None:
        return {
            **base,
            "selection": "special_override",
            "selected_source_cpu": override["pointer"],
            "token_count": 0,
            "token_sha256": "",
            "decoded_text": "",
            "decode_status": f"special_override_{override['storage'].lower()}",
        }

    reader = cat.make_reader(rom, entry)
    try:
        for _ in range(subindex):
            cat.read_logical_record(reader)
        before = reader.cursor()
        record = cat.read_logical_record(reader)
        text = render_record(record, momo, dictionary)
        return {
            **base,
            "selection": "normal_master",
            "selected_source_cpu": usage.get("selected_source_cpu", ""),
            "script_cpus": usage.get("script_cpus", ""),
            "evidence_classes": usage.get("evidence_classes", ""),
            "token_count": len(record),
            "token_sha256": hashlib.sha256(bytes(record)).hexdigest(),
            "cursor_before": json.dumps(before, sort_keys=True),
            "decoded_text": text,
            "decode_status": "ok",
        }
    except Exception as exc:
        return {
            **base,
            "selection": "normal_master",
            "selected_source_cpu": "",
            "token_count": 0,
            "token_sha256": "",
            "cursor_before": "",
            "decoded_text": "",
            "decode_status": f"error:{type(exc).__name__}:{exc}",
        }


def parse_family(value: str) -> int:
    v = int(value, 0)
    if not 0 <= v < 250:
        raise argparse.ArgumentTypeError("family must be 0..249")
    return v


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rom", type=Path)
    ap.add_argument("--usage-csv", type=Path, default=DEFAULT_USAGE)
    ap.add_argument("--lua-table", type=Path, default=DEFAULT_LUA)
    ap.add_argument("--family", action="append", type=parse_family, default=[])
    ap.add_argument("--out-csv", type=Path)
    ap.add_argument("--out-json", type=Path)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    if len(rom) != 2_097_152:
        raise SystemExit(f"unexpected ROM size: {len(rom)}")

    cat = load_catalog_module()
    entries = cat.read_master(rom)
    momo, dictionary = load_render_tables(args.lua_table)
    families = set(args.family) if args.family else None
    pairs = read_usage_pairs(args.usage_csv, families)
    rows = [
        decode_pair(rom, entries, cat, usage, momo, dictionary)
        for usage in pairs
    ]

    if args.out_csv:
        args.out_csv.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "family_id", "family_hex", "subindex", "subindex_hex", "source_root",
            "source_mode", "selection", "selected_source_cpu", "script_cpus",
            "evidence_classes", "token_count", "token_sha256", "cursor_before",
            "decode_status", "decoded_text",
        ]
        with args.out_csv.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(
            json.dumps(
                {
                    "rom_sha256": hashlib.sha256(rom).hexdigest().upper(),
                    "usage_csv": args.usage_csv.as_posix(),
                    "families": sorted(families) if families else "all",
                    "row_count": len(rows),
                    "rows": rows,
                },
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )

    if not args.out_csv and not args.out_json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({
            "row_count": len(rows),
            "ok_count": sum(r["decode_status"] == "ok" for r in rows),
            "error_count": sum(r["decode_status"].startswith("error:") for r in rows),
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
