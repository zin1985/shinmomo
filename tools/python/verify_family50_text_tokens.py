#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECKED_DECODER = ROOT / "data/text_trace/shinmomo_trace_text_jp_decode_snes9x_20260426.lua"
CANONICAL_SHA256 = "F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"
FALLBACK_ROOT_FILE = 0x0702EE
PAYLOAD_START_FILE = 0x0702EF

EXPECTED = {
    0xC5: {"value": 0x25, "file_offset": 0x070477, "cpu": "C7:0477", "bytes": bytes.fromhex("97 DA 9A 91"), "decoded": "ください"},
    0xC9: {"value": 0x29, "file_offset": 0x070489, "cpu": "C7:0489", "bytes": bytes.fromhex("BB 9F 9B"), "decoded": "わたし"},
}

def parse_momo3() -> dict[int, str]:
    text = CHECKED_DECODER.read_text(encoding="utf-8")
    start = text.index("local MOMO3 = {")
    end = text.index("local MOMO4 = {", start)
    momo3_block = text[start:end]
    mappings = {
        int(code, 16): value
        for code, value in re.findall(r'\["([0-9A-F]{2})"\]\s*=\s*"([^"]*)"', momo3_block)
    }
    if mappings.get(0x5B) != "?":
        raise AssertionError("checked MOMO3 table no longer maps 0x5B to '?'")
    if "elseif b == 0x03 then" not in text or "tableId = 3" not in text:
        raise AssertionError("checked decoder no longer proves 0x03 -> table 3")
    if "elseif b == 0x04 then" not in text or "tableId = 4" not in text:
        raise AssertionError("checked decoder no longer proves 0x04 -> table 4")
    return mappings

def skip_logical_records(rom: bytes, start: int, count: int) -> int:
    pos = start
    for _ in range(count):
        while True:
            token = rom[pos]
            pos += 1
            if 0x18 <= token <= 0x1F:
                pos += 1
                continue
            if token == 0x00:
                break
    return pos

def read_record(rom: bytes, start: int) -> bytes:
    end = start
    while rom[end] != 0:
        end += 1
    return rom[start:end]

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True, type=Path)
    args = ap.parse_args()

    rom = args.rom.read_bytes()
    sha = hashlib.sha256(rom).hexdigest().upper()
    if sha != CANONICAL_SHA256:
        raise SystemExit(f"canonical ROM hash mismatch: {sha}")
    if rom[FALLBACK_ROOT_FILE] != 0x00:
        raise AssertionError("family type01 fallback root byte at C7:02EE changed")

    momo3 = parse_momo3()
    rows = []
    for low, expected in EXPECTED.items():
        value = low - 0xA0
        if value != expected["value"]:
            raise AssertionError(f"selector arithmetic mismatch for {low:02X}")
        pos = skip_logical_records(rom, PAYLOAD_START_FILE, value)
        record = read_record(rom, pos)
        decoded = "".join(momo3.get(b, f"{{{b:02X}}}") for b in record)
        if pos != expected["file_offset"]:
            raise AssertionError(f"02{low:02X} pointer mismatch: 0x{pos:06X}")
        if record != expected["bytes"]:
            raise AssertionError(f"02{low:02X} bytes mismatch: {record.hex(' ')}")
        if decoded != expected["decoded"]:
            raise AssertionError(f"02{low:02X} decode mismatch")
        rows.append({
            "token": f"02{low:02X}",
            "selector_value": f"0x{value:02X}",
            "cpu_pointer": expected["cpu"],
            "record_bytes": record.hex(" ").upper() + " 00",
            "decoded": decoded,
        })

    print(json.dumps({
        "rom_sha256": sha,
        "fallback_root": "C7:02EE",
        "payload_start": "C7:02EF",
        "logical_skip_rule": "0x18..0x1F consume one payload byte even if it is 0x00",
        "recursive_tokens": rows,
        "single_byte_5B": "?",
        "table_switch_04": "table4",
        "table_switch_03": "table3",
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
