#!/usr/bin/env python3
"""Catalog Shinmomo's C7:0000 source-family master table.

This emits metadata only. It never writes decoded dialogue text or ROM bytes.
Modes mirror the game readers:
  0 -> raw byte reader
  1 -> C0:BD28 LZ-style reader
  2 -> C0:BD98 bit/tree reader
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

MASTER_OFFSET = 0x070000
FAMILY_COUNT = 250
LAST_FAMILY_END = 0x0AA5B4  # start of 0xFF padding through CA:C000
TERM = 0xBDE4
T0 = 0xBDEC
M0 = 0xBEEB
T1 = 0xBF0B
M1 = 0xC00A
def source_offset(bank: int, addr: int) -> int:
    """Historical source notation C7:xxxx -> file offset 0x07xxxx."""
    return (bank - 0xC0) * 0x10000 + addr


def source_label(offset: int) -> str:
    return f"{0xC0 + (offset >> 16):02X}:{offset & 0xFFFF:04X}"


def read_master(rom: bytes) -> list[dict]:
    entries = []
    previous = -1
    for index in range(FAMILY_COUNT):
        off = MASTER_OFFSET + index * 3
        lo, hi, bank = rom[off:off + 3]
        addr = lo | (hi << 8)
        root = source_offset(bank, addr)
        if bank < 0xC7 or bank > 0xCA:
            raise ValueError(f"unexpected family bank {bank:02X} at {off:06X}")
        if root <= previous:
            raise ValueError(f"non-monotonic family pointer at index {index}")
        previous = root
        entries.append({
            "family_id": index,
            "table_offset": off,
            "bank": bank,
            "addr": addr,
            "root_offset": root,
        })
    if entries[0]["root_offset"] != MASTER_OFFSET + FAMILY_COUNT * 3:
        raise ValueError("family 0 does not begin immediately after master table")
    return entries
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

        copy_literal = bool(self.flag & 0x80)
        self.flag = (self.flag << 1) & 0xFF
        self.flag_left -= 1
        value = self._read_source()

        if copy_literal:
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

        # First copied byte is emitted before $7D is decremented.
        value = self.ring[self.back_ptr]
        self.back_ptr = (self.back_ptr + 1) & 0xFF
        self._put(value)
        return value
class BD98Reader:
    """One-symbol C0:BD98 tree reader using tables embedded in the ROM."""

    def __init__(self, rom: bytes, start: int, end: int):
        self.rom = rom
        self.src = start
        self.end = end
        self.bitbuf = 0
        self.bitcnt = 0

    def _table(self, offset: int) -> int:
        return self.rom[offset]

    def next_symbol(self) -> int:
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
                node = self._table(T1 + old)
                mask = self._table(M1 + high)
            else:
                node = self._table(T0 + old)
                mask = self._table(M0 + high)
            term = self._table(TERM + low)
            if (mask & term) == 0:
                return node
        raise ValueError("BD98 tree depth guard")
def split_records(tokens: list[int]) -> tuple[list[list[int]], list[int]]:
    records: list[list[int]] = []
    current: list[int] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        current.append(token)
        i += 1
        if 0x18 <= token < 0x20 and i < len(tokens):
            current.append(tokens[i])
            i += 1
            continue
        if token == 0:
            records.append(current)
            current = []
    return records, current


def read_mode0(rom: bytes, start: int, end: int) -> tuple[list[list[int]], int]:
    records, tail = split_records(list(rom[start:end]))
    if tail:
        raise ValueError(f"mode0 family has unterminated tail of {len(tail)} tokens")
    return records, end - start
def read_mode1(rom: bytes, start: int, end: int) -> tuple[list[list[int]], int]:
    reader = BD28Reader(rom, start, end)
    tokens: list[int] = []
    while True:
        try:
            tokens.append(reader.next_byte())
        except EOFError:
            break
    records, tail = split_records(tokens)
    if tail:
        raise ValueError(f"mode1 family has unterminated tail of {len(tail)} tokens")
    return records, reader.src - start


def read_mode2(rom: bytes, start: int, end: int) -> tuple[list[list[int]], int]:
    reader = BD98Reader(rom, start, end)
    records: list[list[int]] = []
    while reader.src < end:
        record: list[int] = []
        try:
            for _ in range(10000):
                symbol = reader.next_symbol()
                record.append(symbol)
                # 9DBB treats 18..1F as a two-byte kanji token.
                # The following low byte is data even when its value is 00.
                if 0x18 <= symbol < 0x20:
                    record.append(reader.next_symbol())
                    continue
                if symbol == 0:
                    break
            else:
                raise ValueError("mode2 record symbol guard")
        except EOFError:
            if record:
                raise ValueError("mode2 family ended inside a record")
            break
        records.append(record)
    return records, reader.src - start
def record_metadata(family: dict, mode: int, ordinal: int, record: list[int]) -> dict:
    dictionary_refs = 0
    kanji_pairs = 0
    newlines = 0
    controls = 0
    i = 0
    while i < len(record):
        token = record[i]
        if token == 1:
            newlines += 1
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
    return {
        "family_id": family["family_id"],
        "record_index": ordinal,
        "mode": mode,
        "family_root": f"{family['bank']:02X}:{family['addr']:04X}",
        "token_count": len(record),
        "payload_token_count": max(0, len(record) - 1),
        "dictionary_02_count": dictionary_refs,
        "kanji_pair_count": kanji_pairs,
        "newline_count": newlines,
        "other_control_count": controls,
        "token_sha256": hashlib.sha256(bytes(record)).hexdigest(),
    }
def build_catalog(rom: bytes) -> tuple[list[dict], list[dict]]:
    entries = read_master(rom)
    families: list[dict] = []
    record_rows: list[dict] = []

    for index, family in enumerate(entries):
        root = family["root_offset"]
        end = entries[index + 1]["root_offset"] if index + 1 < len(entries) else LAST_FAMILY_END
        mode = rom[root]
        start = root + 1
        if mode == 0:
            records, used = read_mode0(rom, start, end)
        elif mode == 1:
            records, used = read_mode1(rom, start, end)
        elif mode == 2:
            records, used = read_mode2(rom, start, end)
        else:
            raise ValueError(f"unknown source mode {mode:02X} in family {index}")

        flat = b"".join(bytes(record) for record in records)
        families.append({
            "family_id": index,
            "table_offset": f"0x{family['table_offset']:06X}",
            "family_root": f"{family['bank']:02X}:{family['addr']:04X}",
            "root_file_offset": f"0x{root:06X}",
            "mode": mode,
            "boundary_basis": "next_master_pointer" if index < FAMILY_COUNT - 1 else "ff_padding_to_CA_C000",
            "compressed_span": end - root,
            "compressed_payload_used": used,
            "decoded_token_count": len(flat),
            "record_count": len(records),
            "empty_placeholder": int(len(records) == 0),
            "decoded_sha256": hashlib.sha256(flat).hexdigest(),
        })
        for ordinal, record in enumerate(records):
            record_rows.append(record_metadata(family, mode, ordinal, record))
    return families, record_rows
def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("data/dialogue"))
    args = parser.parse_args()

    rom = args.rom.read_bytes()
    if len(rom) != 2_097_152:
        raise SystemExit(f"unexpected ROM size: {len(rom)}")

    families, records = build_catalog(rom)
    out = args.out_dir
    write_csv(out / "source_family_catalog.csv", families)
    write_csv(out / "source_record_index.csv", records)

    summary = {
        "rom_sha256": hashlib.sha256(rom).hexdigest().upper(),
        "family_count": len(families),
        "mode_counts": {str(mode): sum(1 for row in families if row["mode"] == mode) for mode in (0, 1, 2)},
        "record_counts_by_mode": {str(mode): sum(row["record_count"] for row in families if row["mode"] == mode) for mode in (0, 1, 2)},
        "total_record_count": len(records),
        "empty_family_count": sum(row["empty_placeholder"] for row in families),
        "master_table_file_range": "0x070000..0x0702ED",
        "first_family_root": families[0]["family_root"],
        "last_family_root": families[-1]["family_root"],
        "last_family_boundary": "0x0AA5B4 (start of 6732-byte FF padding to 0x0AC000)",
    }
    (out / "source_family_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
