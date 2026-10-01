#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DIRECT = ROOT / "data/dialogue/family50_canonical_direct_decode_20260930.csv"
BINDING = ROOT / "data/npc_display/static_actor_event_dialogue_binding_20260930.csv"
SEQUENCES = ROOT / "data/npc_display/static_actor_dialogue_sequences_20260930.json"
PAGES = ROOT / "data/npc_display/static_actor_dialogue_sequence_pages_20260930.csv"

VERIFIED_SINGLE_BYTE = {
    "5B": "?",
}
EVIDENCE_SUFFIX = (
    "verified printable token 0x5B='?' from checked text-trace charset tables "
    "(data/text_trace/shinmomo_trace_text_jp_decode_snes9x_20260426.lua; "
    "tools/lua/shinmomo_trace_dialogue_v28_mode02_bd98_decoder_smallkana_checked_snes9x_20260427.lua)"
)


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader), list(reader.fieldnames or [])


def write_rows(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator=chr(10))
        writer.writeheader()
        writer.writerows(rows)


def append_evidence(existing: str) -> str:
    if EVIDENCE_SUFFIX in existing:
        return existing
    return f"{existing}; {EVIDENCE_SUFFIX}" if existing else EVIDENCE_SUFFIX


def replace_verified_markers(value: Any) -> tuple[Any, int]:
    if isinstance(value, str):
        count = 0
        for token, glyph in VERIFIED_SINGLE_BYTE.items():
            marker = "{" + token + "}"
            n = value.count(marker)
            if n:
                value = value.replace(marker, glyph)
                count += n
        return value, count
    if isinstance(value, list):
        out = []
        count = 0
        for item in value:
            new_item, n = replace_verified_markers(item)
            out.append(new_item)
            count += n
        return out, count
    if isinstance(value, dict):
        out = {}
        count = 0
        for key, item in value.items():
            new_item, n = replace_verified_markers(item)
            out[key] = new_item
            count += n
        return out, count
    return value, 0


def main() -> None:
    direct, direct_fields = read_rows(DIRECT)
    changed_direct = 0
    resolved_unknowns = 0
    direct_by_text_id: dict[str, dict[str, str]] = {}

    for row in direct:
        replacements = 0
        decoded = row.get("decoded_text", "")
        events = row.get("events", "")
        for token, glyph in VERIFIED_SINGLE_BYTE.items():
            marker = "{" + token + "}"
            count = decoded.count(marker)
            if count:
                decoded = decoded.replace(marker, glyph)
                events = events.replace(f":{token}:{marker}", f":{token}:{glyph}")
                replacements += count

        old_unknown = int(row.get("unknown") or 0)
        if replacements > old_unknown:
            raise ValueError(
                f"{row.get('subindex_hex')}: verified replacements {replacements} exceed unknown={old_unknown}"
            )
        # Promote only records whose entire unknown set is explained by verified glyphs.
        # Mixed-unknown records remain unresolved until all unknown tokens are proven.
        if replacements and replacements == old_unknown:
            row["decoded_text"] = decoded
            row["events"] = events
            row["unknown"] = "0"
            row["decode_status"] = "confirmed_static_direct_decode"
            row["evidence"] = append_evidence(row.get("evidence", ""))
            changed_direct += 1
            resolved_unknowns += replacements

        direct_by_text_id[f"0x50:{row.get('subindex_hex', '')}"] = row

    write_rows(DIRECT, direct, direct_fields)
    eligible_text_ids = {
        text_id for text_id, row in direct_by_text_id.items()
        if EVIDENCE_SUFFIX in row.get("evidence", "") and int(row.get("unknown") or 0) == 0
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
        if (
            row.get("decoded_text") != source.get("decoded_text")
            or row.get("decode_status") != source.get("decode_status")
        ):
            row["decoded_text"] = source.get("decoded_text", "")
            row["decode_status"] = source.get("decode_status", "")
            row["evidence"] = append_evidence(row.get("evidence", ""))
            changed_binding += 1

    write_rows(BINDING, binding, binding_fields)

    sequence_obj = json.loads(SEQUENCES.read_text(encoding="utf-8"))
    changed_sequences = 0
    sequence_marker_replacements = 0
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
            if source.get("text_record_id") in eligible_text_ids:
                new_pages, n = replace_verified_markers(sequence.get("pages", []))
                sequence["pages"] = new_pages
            else:
                n = 0
            if n or before_status != source["decode_status"] or before_unknown != source["decoder_unknown_tokens"]:
                changed_sequences += 1
                sequence_marker_replacements += n

    SEQUENCES.write_text(
        json.dumps(sequence_obj, ensure_ascii=False, indent=2) + chr(10),
        encoding="utf-8",
    )

    page_rows, page_fields = read_rows(PAGES)
    changed_page_rows = 0
    page_marker_replacements = 0
    for row in page_rows:
        if row.get("text_record_id") not in eligible_text_ids:
            continue
        row_changed = False
        for key, value in list(row.items()):
            new_value, n = replace_verified_markers(value)
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
        f"changed_page_rows={changed_page_rows} "
        f"page_marker_replacements={page_marker_replacements}"
    )


if __name__ == "__main__":
    main()
