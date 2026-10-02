#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/python"))
import catalog_dialogue_sources as cds

FAMILY = 0x4E
CANONICAL_SHA256 = "F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"
CHECKED_DECODER = ROOT / "data/text_trace/shinmomo_trace_text_jp_decode_snes9x_20260426.lua"
USAGE = ROOT / "data/dialogue/source_pair_usage_catalog.csv"
OUT = ROOT / "data/dialogue/location_dialogue_context_20261002.csv"

# Earlier A4 opcodes are clearly present in the pack body, but have not yet
# been promoted by the conservative source-pair scanner. Keep that distinction.
EARLY_A4_CANDIDATES = {
    0x00: "CC:194B", 0x01: "CC:1951", 0x02: "CC:197A", 0x03: "CC:1988",
    0x04: "CC:198E", 0x05: "CC:1994", 0x06: "CC:19B2", 0x07: "CC:19C0",
    0x08: "CC:19CC", 0x09: "CC:19E0", 0x0A: "CC:19E9", 0x0B: "CC:19EF",
}

PHASE = {
    0x00: ("後期・カルラ／ダイダ王子言及", "semantic_phase_candidate"),
    0x01: ("海底・勇気の鎧イベント期", "semantic_phase_candidate"),
    0x02: ("銀次加入後・装備案内", "strong_semantic_phase_candidate"),
    0x03: ("狛犬損傷イベント期（ひえん飛来との関係は未確定）", "event_phase_candidate"),
    0x04: ("初期・おむすびころりん案内", "strong_semantic_phase_candidate"),
    0x05: ("ひえん巻物飛来直後候補", "strong_semantic_phase_candidate"),
    0x06: ("初期・鬼退治出発前後", "generic_or_early_phase_candidate"),
    0x07: ("ひえん巻物飛来直後候補", "strong_semantic_phase_candidate"),
    0x08: ("初期〜常設・井戸回復案内", "generic_or_early_phase_candidate"),
    0x09: ("ひえん修行中・巻物探索期", "strong_semantic_phase_candidate"),
    0x0A: ("おむすびころりん封鎖期", "semantic_phase_candidate"),
    0x0B: ("おむすび村成立後", "semantic_phase_candidate"),
    0x0C: ("ひえん修行中・巻物探索期", "strong_semantic_phase_candidate"),
    0x0D: ("月から帰還後候補", "semantic_phase_candidate"),
    0x0E: ("ひえん修行中・巻物探索期", "strong_semantic_phase_candidate"),
    0x0F: ("おむすびころりん襲撃報告期", "semantic_phase_candidate"),
    0x10: ("お供加入後の一般会話候補", "semantic_phase_candidate"),
    0x11: ("ひえん修行中・巻物探索期", "strong_semantic_phase_candidate"),
    0x12: ("初期〜常設案内候補", "generic_or_early_phase_candidate"),
    0x13: ("初期〜常設案内候補", "generic_or_early_phase_candidate"),
    0x14: ("初期〜常設案内候補", "generic_or_early_phase_candidate"),
    0x15: ("雪だるま発見・再会イベント", "event_phase_strong"),
    0x16: ("落下物取得イベント（対象パラメータ未解決）", "event_phase_candidate"),
    0x17: ("飛来物イベント", "event_phase_candidate"),
}

# 0x4E:02 is independently available through family 0x4F:00 with a clean
# fresh-reader text. Use that exact text for display while retaining 0x4E:02
# as the location-stream coordinate.
DEFAULT_TABIDACHI = {
    0x03, 0x04, 0x05, 0x07, 0x09, 0x0A, 0x0B, 0x0C,
    0x0E, 0x0F, 0x11, 0x12, 0x13, 0x14, 0x15, 0x17,
}

DISPLAY_OVERRIDE = {
    0x02: """「桃太郎! 銀次の そうびを
 ととのえたか?
 銀次は 刀も そうびできる!」
「銀次の そうびは 着流しだ!
 はちまきと わらじは
 桃太郎と いっしょだがな!」""",
}

def lua_table(text: str, name: str, next_name: str | None = None) -> dict[str, str]:
    start = text.index("local " + name + " = {")
    end = text.index("local " + next_name + " = {", start) if next_name else text.index("\n}", start) + 2
    return {k.upper(): v for k, v in re.findall(r'\["([0-9A-F]+)"\]\s*=\s*"([^"]*)"', text[start:end])}

def skip_c7_records(rom: bytes, count: int) -> int:
    pos = 0x0702EF
    for _ in range(count):
        while True:
            token = rom[pos]
            pos += 1
            if 0x18 <= token <= 0x1F:
                pos += 1
                continue
            if token == 0:
                break
    return pos

def c7_record(rom: bytes, low: int) -> list[int] | None:
    if low < 0xA0:
        return None
    pos = skip_c7_records(rom, low - 0xA0)
    out: list[int] = []
    while True:
        token = rom[pos]
        pos += 1
        if token == 0:
            break
        out.append(token)
        if 0x18 <= token <= 0x1F:
            out.append(rom[pos])
            pos += 1
    return out

def decode_record(record: list[int], rom: bytes, m3: dict[str,str], m4: dict[str,str], table_id: int = 3, depth: int = 0) -> tuple[str,list[str]]:
    if depth > 4:
        return "{DICT_DEPTH}", ["DICT_DEPTH"]
    out: list[str] = []
    unknown: list[str] = []
    i = 0
    while i < len(record):
        b = record[i]
        if b == 0:
            break
        if b == 1:
            out.append("\n"); i += 1; continue
        if b == 2 and i + 1 < len(record):
            low = record[i+1]
            nested = c7_record(rom, low)
            if nested is None:
                key = f"02{low:02X}"; out.append("{" + key + "}"); unknown.append(key)
            else:
                txt, un = decode_record(nested, rom, m3, m4, table_id, depth + 1)
                out.append(txt); unknown.extend(un)
            i += 2; continue
        if b == 3:
            table_id = 3; i += 1; continue
        if b == 4:
            table_id = 4; i += 1; continue
        if 0x18 <= b < 0x20 and i + 1 < len(record):
            key = f"{b:02X}{record[i+1]:02X}"
            val = m3.get(key) or m4.get(key)
            if val is None:
                val = "{" + key + "}"; unknown.append(key)
            out.append(val); i += 2; continue
        key = f"{b:02X}"
        val = (m4.get(key) or m3.get(key)) if table_id == 4 else (m3.get(key) or m4.get(key))
        if val is None or val == "":
            if b in (0x09,):
                val = "{09}"; unknown.append("09")
            elif val == "":
                val = ""
            else:
                val = "{" + key + "}"; unknown.append(key)
        out.append(val); i += 1
    return "".join(out).replace("<00>", "").strip(), unknown

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True, type=Path)
    args = ap.parse_args()
    rom = args.rom.read_bytes()
    sha = hashlib.sha256(rom).hexdigest().upper()
    if sha != CANONICAL_SHA256:
        raise SystemExit(f"canonical ROM hash mismatch: {sha}")

    lua = CHECKED_DECODER.read_text(encoding="utf-8")
    m3 = lua_table(lua, "MOMO3", "MOMO4")
    m4 = lua_table(lua, "MOMO4")

    usage = {}
    if USAGE.exists():
        for row in csv.DictReader(USAGE.open(encoding="utf-8-sig", newline="")):
            if row.get("family_hex") == "0x4E":
                usage[int(row["subindex"])] = row

    entries = cds.read_master(rom)
    reader = cds.make_reader(rom, entries[FAMILY])
    rows = []
    for sub in range(0x18):
        before = reader.cursor().copy()
        rec = cds.read_logical_record(reader)
        text, unknown = decode_record(rec, rom, m3, m4)
        if sub in DISPLAY_OVERRIDE:
            text = DISPLAY_OVERRIDE[sub]
            unknown = []
        use = usage.get(sub)
        callsite = (use or {}).get("script_cpus") or EARLY_A4_CANDIDATES.get(sub, "")
        selection_status = (
            "catalogued_a4_source_selection"
            if use else
            "strong_a4_opcode_boundary_candidate_not_yet_promoted_by_source_pair_catalog"
        )
        phase_hint, phase_status = PHASE[sub]
        evidence = [
            f"canonical family 0x4E direct reader root C8:A717 subindex 0x{sub:02X}",
            f"canonical_rom_sha256={sha}",
        ]
        if use:
            evidence.append("data/dialogue/source_pair_usage_catalog.csv")
            if use.get("details"):
                evidence.append(use["details"])
        else:
            evidence.append(f"A4 {sub:02X} opcode bytes present at {callsite}; full compact-VM boundary promotion pending")
        if sub == 0x02:
            evidence.append("display text independently clean-decoded through family 0x4F:0x00 alias")
        location_strong = sub in DEFAULT_TABIDACHI
        rows.append({
            "location_context_id": "tabidachi_village",
            "location_label": "旅立ちの村",
            "map_config_id": "cfg_t04_l008_v2",
            "runtime_map_pack_hex": "0x50",
            "dialogue_family_hex": "0x4E",
            "subindex_hex": f"0x{sub:02X}",
            "text_pointer": f"C8:{before['src']-0x080000:04X}",
            "script_callsite": callsite,
            "source_selection_status": selection_status,
            "phase_hint": phase_hint,
            "phase_status": phase_status,
            "flag_binding_status": "exact_story_flag_unresolved",
            "viewer_default": "1" if location_strong else "0",
            "decoded_text": text,
            "decoder_unknown_tokens": ";".join(sorted(set(unknown))),
            "decode_status": "confirmed_static_direct_decode" if not unknown else "confirmed_static_direct_decode_with_parameter_control",
            "location_binding_status": (
                "strong_tabidachi_context_actor_binding_unresolved"
                if location_strong else
                "same_family_location_unresolved"
            ),
            "confidence": "strong" if location_strong else "candidate",
            "raw_token_sha256": hashlib.sha256(bytes(rec)).hexdigest(),
            "evidence": "; ".join(evidence),
        })

    fields = list(rows[0])
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    print(f"wrote {OUT.relative_to(ROOT)} rows={len(rows)} unknown_rows={sum(bool(r['decoder_unknown_tokens']) for r in rows)}")

if __name__ == "__main__":
    main()