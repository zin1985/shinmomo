#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DIRECT = ROOT / "data/dialogue/family50_canonical_direct_decode_20260930.csv"
BINDING = ROOT / "data/npc_display/static_actor_event_dialogue_binding_20260930.csv"
SEQUENCES = ROOT / "data/npc_display/static_actor_dialogue_sequences_20260930.json"
PAGES = ROOT / "data/npc_display/static_actor_dialogue_sequence_pages_20260930.csv"
TOKEN_EVIDENCE = ROOT / "data/dialogue/family50_verified_token_semantics_20261002.csv"

VERIFIED_INLINE = {"5B": "?", "02C5": "ください", "02C9": "わたし"}
TABLE_SWITCH = {"04": 4, "03": 3}
TABLE_MARKER = {"04": "<TABLE4>", "03": "<TABLE3>"}
MARKER_RE = re.compile(r"\{(5B|02C5|02C9|03|04)\}")

OLD_EVIDENCE_SUFFIX = (
    "verified printable token 0x5B='?' from checked text-trace charset tables "
    "(data/text_trace/shinmomo_trace_text_jp_decode_snes9x_20260426.lua; "
    "tools/lua/shinmomo_trace_dialogue_v28_mode02_bd98_decoder_smallkana_checked_snes9x_20260427.lua)"
)
EVIDENCE_SUFFIX = (
    "verified family50 text-token semantics: 0x5B='?'; "
    "02C5 -> C7:0477 bytes 97 DA 9A 91 = 'ください'; "
    "02C9 -> C7:0489 bytes BB 9F 9B = 'わたし' through token02 family-type01 fallback "
    "and C4:9DBB logical-record skip; 0x04 switches text table 4 and 0x03 switches text table 3 "
    "(data/weapon_special/vol015_trace/shinmomo_vol015_dispatch_token_trace/"
    "shinmomo_vol015_dispatch_token_trace_report_20260430.md; "
    "docs/analysis/dialogue_source_family_catalog.md; "
    "data/text_trace/shinmomo_trace_text_jp_decode_snes9x_20260426.lua)"
)

TOKEN_EVIDENCE_ROWS = [
    {"token":"0x5B","kind":"printable_single_byte","selector_value":"","fallback_root":"","record_pointer":"","record_bytes":"5B","decoded":"?","status":"confirmed_static_checked_decoder","evidence":"data/text_trace/shinmomo_trace_text_jp_decode_snes9x_20260426.lua;tools/lua/shinmomo_trace_dialogue_v28_mode02_bd98_decoder_smallkana_checked_snes9x_20260427.lua"},
    {"token":"0x02C5","kind":"recursive_source_token","selector_value":"0x25","fallback_root":"C7:02EE","record_pointer":"C7:0477","record_bytes":"97 DA 9A 91 00","decoded":"ください","status":"confirmed_static_recursive_lookup","evidence":"token02 C5 trace: C5-A0=25; family type01 fallback C7:0000[0]=C7:02EE; C4:9DBB logical-record skip lands C7:0477"},
    {"token":"0x02C9","kind":"recursive_source_token","selector_value":"0x29","fallback_root":"C7:02EE","record_pointer":"C7:0489","record_bytes":"BB 9F 9B 00","decoded":"わたし","status":"confirmed_static_recursive_lookup","evidence":"same proven token02 family-type01 fallback and C4:9DBB logical-record skip as 02C5; value C9-A0=29 lands C7:0489"},
    {"token":"0x04","kind":"text_table_switch","selector_value":"","fallback_root":"","record_pointer":"","record_bytes":"04","decoded":"<TABLE4>","status":"confirmed_checked_text_decoder","evidence":"data/text_trace/shinmomo_trace_text_jp_decode_snes9x_20260426.lua sets tableId=4"},
    {"token":"0x03","kind":"text_table_switch","selector_value":"","fallback_root":"","record_pointer":"","record_bytes":"03","decoded":"<TABLE3>","status":"confirmed_checked_text_decoder","evidence":"data/text_trace/shinmomo_trace_text_jp_decode_snes9x_20260426.lua sets tableId=3"},
]

def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), list(reader.fieldnames or [])

def write_rows(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

def append_evidence(existing: str) -> str:
    if EVIDENCE_SUFFIX in existing:
        return existing
    return f"{existing}; {EVIDENCE_SUFFIX}" if existing else EVIDENCE_SUFFIX

def hira_to_kata(value: str) -> str:
    out = []
    for ch in value:
        cp = ord(ch)
        out.append(chr(cp + 0x60) if 0x3041 <= cp <= 0x3096 else ch)
    return "".join(out)

def resolve_display_markers(value: str) -> tuple[str, int]:
    if value == "{04}":
        return TABLE_MARKER["04"], 1
    if value == "{03}":
        return TABLE_MARKER["03"], 1
    matches = list(MARKER_RE.finditer(value))
    if not matches:
        return value, 0
    table_id = 3
    pos = 0
    out = []
    for m in matches:
        chunk = value[pos:m.start()]
        out.append(hira_to_kata(chunk) if table_id == 4 else chunk)
        token = m.group(1)
        if token in TABLE_SWITCH:
            table_id = TABLE_SWITCH[token]
        else:
            out.append(VERIFIED_INLINE[token])
        pos = m.end()
    tail = value[pos:]
    out.append(hira_to_kata(tail) if table_id == 4 else tail)
    return "".join(out), len(matches)

def resolve_event_stream(value: str) -> str:
    if not value:
        return value
    table_id = 3
    out = []
    for part in value.split(" | "):
        bits = part.split(":", 2)
        if len(bits) != 3:
            out.append(part)
            continue
        idx, token, decoded = bits
        if token in TABLE_SWITCH:
            table_id = TABLE_SWITCH[token]
            decoded = TABLE_MARKER[token]
        elif token in VERIFIED_INLINE:
            decoded = VERIFIED_INLINE[token]
        elif table_id == 4:
            decoded = hira_to_kata(decoded)
        out.append(f"{idx}:{token}:{decoded}")
    return " | ".join(out)

def resolve_source_events(events: list[dict[str, Any]]) -> int:
    table_id = 3
    changed = 0
    for ev in events:
        token = str(ev.get("token", ""))
        decoded = ev.get("decoded")
        if not isinstance(decoded, str):
            continue
        new = decoded
        if token in TABLE_SWITCH:
            table_id = TABLE_SWITCH[token]
            new = TABLE_MARKER[token]
        elif token in VERIFIED_INLINE:
            new = VERIFIED_INLINE[token]
        elif table_id == 4:
            new = hira_to_kata(decoded)
        if new != decoded:
            ev["decoded"] = new
            changed += 1
    return changed

def write_token_evidence() -> None:
    fields = ["token","kind","selector_value","fallback_root","record_pointer","record_bytes","decoded","status","evidence"]
    write_rows(TOKEN_EVIDENCE, TOKEN_EVIDENCE_ROWS, fields)

def main() -> None:
    direct, direct_fields = read_rows(DIRECT)
    changed_direct = 0
    resolved_unknowns = 0
    direct_by_text_id = {}

    for row in direct:
        decoded = row.get("decoded_text", "")
        old_unknown = int(row.get("unknown") or 0)
        markers = MARKER_RE.findall(decoded)
        if markers and len(markers) > old_unknown:
            raise ValueError(f"{row.get('subindex_hex')}: verified markers {len(markers)} exceed unknown={old_unknown}")
        if markers and len(markers) == old_unknown:
            new_decoded, replacements = resolve_display_markers(decoded)
            if replacements != old_unknown:
                raise ValueError(f"{row.get('subindex_hex')}: replacement count {replacements} != unknown={old_unknown}")
            row["decoded_text"] = new_decoded
            row["events"] = resolve_event_stream(row.get("events", ""))
            row["unknown"] = "0"
            row["decode_status"] = "confirmed_static_direct_decode"
            row["evidence"] = append_evidence(row.get("evidence", ""))
            changed_direct += 1
            resolved_unknowns += replacements
        direct_by_text_id[f"0x50:{row.get('subindex_hex', '')}"] = row

    write_rows(DIRECT, direct, direct_fields)
    write_token_evidence()

    eligible_text_ids = {
        text_id for text_id, row in direct_by_text_id.items()
        if int(row.get("unknown") or 0) == 0
        and row.get("decode_status") == "confirmed_static_direct_decode"
        and (EVIDENCE_SUFFIX in row.get("evidence", "") or OLD_EVIDENCE_SUFFIX in row.get("evidence", ""))
    }

    binding, binding_fields = read_rows(BINDING)
    changed_binding = 0
    direct_by_pointer = {row.get("text_pointer", ""): row for row in direct}
    for row in binding:
        if row.get("pack_id_hex") != "0x50":
            continue
        source = direct_by_pointer.get(row.get("text_pointer", ""))
        if not source:
            continue
        if row.get("decoded_text") != source.get("decoded_text") or row.get("decode_status") != source.get("decode_status"):
            row["decoded_text"] = source.get("decoded_text", "")
            row["decode_status"] = source.get("decode_status", "")
            row["evidence"] = append_evidence(row.get("evidence", ""))
            changed_binding += 1
    write_rows(BINDING, binding, binding_fields)

    sequence_obj = json.loads(SEQUENCES.read_text(encoding="utf-8"))
    changed_sequences = 0
    sequence_marker_replacements = 0
    source_event_updates = 0
    for actor in sequence_obj.get("actors", []):
        if actor.get("pack_id_hex") != "0x50":
            continue
        for sequence in actor.get("dialogue_sequences", []):
            source = sequence.get("source", {})
            direct_row = direct_by_text_id.get(source.get("text_record_id", ""))
            if not direct_row:
                continue
            before_status = source.get("decode_status")
            before_unknown = source.get("decoder_unknown_tokens")
            source["decode_status"] = direct_row.get("decode_status")
            source["decoder_unknown_tokens"] = int(direct_row.get("unknown") or 0)
            replacements = 0
            if source.get("text_record_id") in eligible_text_ids:
                for page in sequence.get("pages", []):
                    page_text, n = resolve_display_markers(page.get("page_text", ""))
                    if n:
                        page["page_text"] = page_text
                        replacements += n
                    for line in page.get("lines", []):
                        text_value, n = resolve_display_markers(line.get("text", ""))
                        if n:
                            line["text"] = text_value
                            replacements += n
                    source_event_updates += resolve_source_events(page.get("source_events", []))
            if replacements or before_status != source["decode_status"] or before_unknown != source["decoder_unknown_tokens"]:
                changed_sequences += 1
                sequence_marker_replacements += replacements

    SEQUENCES.write_text(json.dumps(sequence_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    page_rows, page_fields = read_rows(PAGES)
    changed_page_rows = 0
    page_marker_replacements = 0
    for row in page_rows:
        if row.get("text_record_id") not in eligible_text_ids:
            continue
        row_changed = False
        for key, value in list(row.items()):
            new_value, n = resolve_display_markers(value)
            if n:
                row[key] = new_value
                row_changed = True
                page_marker_replacements += n
        if row_changed:
            changed_page_rows += 1
    write_rows(PAGES, page_rows, page_fields)

    print(
        f"changed_direct_rows={changed_direct} "
        f"resolved_unknown_tokens={resolved_unknowns} "
        f"changed_binding_rows={changed_binding} "
        f"changed_sequences={changed_sequences} "
        f"sequence_marker_replacements={sequence_marker_replacements} "
        f"source_event_updates={source_event_updates} "
        f"changed_page_rows={changed_page_rows} "
        f"page_marker_replacements={page_marker_replacements}"
    )

if __name__ == "__main__":
    main()
