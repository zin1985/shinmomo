#!/usr/bin/env python3
"""Catalog and probe Shinmomo's shared C7:0000 source-family system.

The canonical ROM is FastROM HiROM. This tool emits metadata only:
- the 250 source-family entry roots and modes;
- optional metadata for explicitly requested (family, subindex) pairs.

Important: master entries are overlapping source start points. The next master
pointer is NOT a family end boundary.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

MASTER_OFFSET = 0x070000
FAMILY_COUNT = 250
SOURCE_REGION_END = 0x0AC000
SPECIAL_SUBINDEX_OFFSET = 0x04AE7E
SPECIAL_FAMILY_OFFSET = 0x04AE89
SPECIAL_POINTER_OFFSET = 0x04AE94
SPECIAL_COUNT = 10

TERM = 0xBDE4
T0 = 0xBDEC
M0 = 0xBEEB
T1 = 0xBF0B
M1 = 0xC00A
def source_offset(bank: int, addr: int) -> int:
    return (bank - 0xC0) * 0x10000 + addr


def read_master(rom: bytes) -> list[dict]:
    entries = []
    prev = -1
    for family_id in range(FAMILY_COUNT):
        table_offset = MASTER_OFFSET + family_id * 3
        lo, hi, bank = rom[table_offset:table_offset + 3]
        addr = lo | (hi << 8)
        root = source_offset(bank, addr)
        if not (0xC7 <= bank <= 0xCA):
            raise ValueError(f"unexpected family bank {bank:02X} at {table_offset:06X}")
        if root <= prev:
            raise ValueError(f"master pointers not increasing at family {family_id}")
        prev = root
        entries.append({
            "family_id": family_id,
            "table_offset": table_offset,
            "bank": bank,
            "addr": addr,
            "root_offset": root,
            "mode": rom[root],
        })
    if entries[0]["root_offset"] != MASTER_OFFSET + FAMILY_COUNT * 3:
        raise ValueError("family 0 does not start immediately after the master table")
    return entries


def special_override(rom: bytes, family_id: int, subindex: int) -> dict | None:
    for i in range(SPECIAL_COUNT):
        if rom[SPECIAL_SUBINDEX_OFFSET + i] != subindex:
            continue
        if rom[SPECIAL_FAMILY_OFFSET + i] != family_id:
            continue
        p = SPECIAL_POINTER_OFFSET + i * 3
        lo, hi, bank = rom[p:p + 3]
        return {
            "special_index": i,
            "bank": bank,
            "addr": lo | (hi << 8),
            "pointer": f"{bank:02X}:{(lo | (hi << 8)):04X}",
            "storage": "WRAM" if bank in (0x7E, 0x7F) else "ROM",
        }
    return None
class RawReader:
    def __init__(self, rom: bytes, start: int, end: int):
        self.rom = rom
        self.src = start
        self.end = end

    def next_byte(self) -> int:
        if self.src >= self.end:
            raise EOFError
        value = self.rom[self.src]
        self.src += 1
        return value

    def cursor(self) -> dict:
        return {"src": self.src}


class BD28Reader:
    """C0:BCEE/BCFA initialization + one-byte C0:BD28 reader."""

    def __init__(self, rom: bytes, start: int, end: int):
        self.rom = rom
        self.src = start
        self.end = end
        self.ring = [0] * 256
        self.write_ptr = 0xEF
        self.back_ptr = 0
        self.flag = 0
        self.flag_left = 0
        self.length_toggle = 0
        self.length_byte = 0
        self.remaining = 0

    def _read_source(self) -> int:
        if self.src >= self.end:
            raise EOFError
        value = self.rom[self.src]
        self.src += 1
        return value

    def _put(self, value: int) -> None:
        self.ring[self.write_ptr] = value
        self.write_ptr = (self.write_ptr + 1) & 0xFF

    def next_byte(self) -> int:
        if self.remaining:
            self.remaining = (self.remaining - 1) & 0xFF
            value = self.ring[self.back_ptr]
            self.back_ptr = (self.back_ptr + 1) & 0xFF
            self._put(value)
            return value

        if self.flag_left == 0:
            self.flag = self._read_source()
            self.flag_left = 8

        literal = bool(self.flag & 0x80)
        self.flag = (self.flag << 1) & 0xFF
        self.flag_left -= 1
        value = self._read_source()

        if literal:
            self._put(value)
            return value

        self.back_ptr = value
        if self.length_toggle == 0:
            self.length_toggle = 1
            self.length_byte = self._read_source()
            self.remaining = ((self.length_byte >> 4) & 0x0F) + 1
        else:
            self.length_toggle = 0
            self.remaining = (self.length_byte & 0x0F) + 1

        value = self.ring[self.back_ptr]
        self.back_ptr = (self.back_ptr + 1) & 0xFF
        self._put(value)
        return value

    def cursor(self) -> dict:
        return {
            "src": self.src,
            "flag_left": self.flag_left,
            "remaining": self.remaining,
            "write_ptr": self.write_ptr,
        }
class BD98Reader:
    """One-symbol C0:BD98 tree reader."""

    def __init__(self, rom: bytes, start: int, end: int):
        self.rom = rom
        self.src = start
        self.end = end
        self.bitbuf = 0
        self.bitcnt = 0

    def next_byte(self) -> int:
        node = 0
        for _ in range(80):
            old = node
            low = old & 7
            high = old >> 3
            self.bitcnt = (self.bitcnt - 1) & 0xFF
            if self.bitcnt >= 0x80:
                if self.src >= self.end:
                    raise EOFError
                self.bitbuf = self.rom[self.src]
                self.src += 1
                self.bitcnt = 7
            one = bool(self.bitbuf & 0x80)
            self.bitbuf = (self.bitbuf << 1) & 0xFF
            if one:
                node = self.rom[T1 + old]
                mask = self.rom[M1 + high]
            else:
                node = self.rom[T0 + old]
                mask = self.rom[M0 + high]
            if (mask & self.rom[TERM + low]) == 0:
                return node
        raise ValueError("BD98 tree depth guard")

    def cursor(self) -> dict:
        return {"src": self.src, "bitcnt": self.bitcnt, "bitbuf": self.bitbuf}
def make_reader(rom: bytes, family: dict):
    start = family["root_offset"] + 1
    mode = family["mode"]
    if mode == 0:
        return RawReader(rom, start, SOURCE_REGION_END)
    if mode == 1:
        return BD28Reader(rom, start, SOURCE_REGION_END)
    if mode == 2:
        return BD98Reader(rom, start, SOURCE_REGION_END)
    raise ValueError(f"unsupported mode {mode:02X} for family {family['family_id']}")


def read_logical_record(reader, max_tokens: int = 20000) -> list[int]:
    out: list[int] = []
    for _ in range(max_tokens):
        token = reader.next_byte()
        out.append(token)
        if 0x18 <= token < 0x20:
            out.append(reader.next_byte())
            continue
        if token == 0:
            return out
    raise ValueError("logical-record token guard")


def probe_pair(rom: bytes, entries: list[dict], family_id: int, subindex: int) -> dict:
    if not 0 <= family_id < FAMILY_COUNT:
        raise ValueError("family must be 0..249")
    if not 0 <= subindex <= 0xFF:
        raise ValueError("subindex must be 0..255")

    override = special_override(rom, family_id, subindex)
    family = entries[family_id]
    base = {
        "family_id": family_id,
        "subindex": subindex,
        "family_root": f"{family['bank']:02X}:{family['addr']:04X}",
        "mode": family["mode"],
    }
    if override is not None:
        base.update({
            "selection": "special_override",
            "override_pointer": override["pointer"],
            "override_storage": override["storage"],
        })
        return base

    reader = make_reader(rom, family)
    for _ in range(subindex):
        read_logical_record(reader)
    before = reader.cursor()
    record = read_logical_record(reader)
    after = reader.cursor()

    dictionary_refs = 0
    kanji_pairs = 0
    controls = 0
    i = 0
    while i < len(record):
        token = record[i]
        if token == 2 and i + 1 < len(record):
            dictionary_refs += 1
            i += 2
            continue
        if 0x18 <= token < 0x20 and i + 1 < len(record):
            kanji_pairs += 1
            i += 2
            continue
        if 0 < token < 0x50:
            controls += 1
        i += 1

    base.update({
        "selection": "normal_master",
        "token_count": len(record),
        "dictionary_02_count": dictionary_refs,
        "kanji_pair_count": kanji_pairs,
        "other_control_count": controls,
        "token_sha256": hashlib.sha256(bytes(record)).hexdigest(),
        "cursor_before": before,
        "cursor_after": after,
    })
    return base
def write_family_outputs(rom: bytes, entries: list[dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, entry in enumerate(entries):
        if i + 1 < len(entries):
            nxt = entries[i + 1]
            next_root = f"{nxt['bank']:02X}:{nxt['addr']:04X}"
            delta = nxt["root_offset"] - entry["root_offset"]
        else:
            next_root = ""
            delta = ""
        rows.append({
            "family_id": entry["family_id"],
            "table_offset": f"0x{entry['table_offset']:06X}",
            "family_root": f"{entry['bank']:02X}:{entry['addr']:04X}",
            "root_file_offset": f"0x{entry['root_offset']:06X}",
            "mode": entry["mode"],
            "next_family_root": next_root,
            "delta_to_next_root": delta,
            "next_root_is_end": 0,
        })

    with (out_dir / "source_family_catalog.csv").open(
        "w", encoding="utf-8-sig", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "rom_sha256": hashlib.sha256(rom).hexdigest().upper(),
        "family_count": len(entries),
        "mode_counts": {
            str(mode): sum(1 for entry in entries if entry["mode"] == mode)
            for mode in (0, 1, 2)
        },
        "other_mode_count": sum(entry["mode"] not in (0, 1, 2) for entry in entries),
        "master_table_file_range": "0x070000..0x0702ED",
        "first_family_root": rows[0]["family_root"],
        "last_family_root": rows[-1]["family_root"],
        "boundary_model": "overlapping entry-point streams; next pointer is not an end",
        "record_inventory_status": "usage-driven (family,subindex) enumeration required",
    }
    (out_dir / "source_family_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
def parse_pair(value: str) -> tuple[int, int]:
    family, subindex = value.split(":", 1)
    return int(family, 0), int(subindex, 0)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("data/dialogue"))
    parser.add_argument(
        "--probe",
        action="append",
        default=[],
        metavar="FAMILY:SUBINDEX",
        help="probe one usage pair; numbers accept 0x prefix",
    )
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    if len(rom) != 2_097_152:
        raise SystemExit(f"unexpected ROM size: {len(rom)}")

    entries = read_master(rom)
    write_family_outputs(rom, entries, args.out_dir)

    for value in args.probe:
        family, subindex = parse_pair(value)
        print(json.dumps(probe_pair(rom, entries, family, subindex),
                         ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
