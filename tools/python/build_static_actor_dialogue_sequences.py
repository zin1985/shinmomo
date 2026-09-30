#!/usr/bin/env python3
from pathlib import Path
import argparse
import collections
import csv
import json
import re

ROOT = Path(__file__).resolve().parents[2]
BINDING = ROOT / "data/npc_display/static_actor_event_dialogue_binding_20260930.csv"
HIST = ROOT / "data/dialogue/historical_decode_crosswalk.csv"
DECODE = ROOT / "data/csv/shinmomo_v33_test_C8_A7DD.csv"
EVENT_SOURCE = ROOT / "data/events/event_source_crosslink.csv"
OUT_JSON = ROOT / "data/npc_display/static_actor_dialogue_sequences_20260930.json"
OUT_PAGES = ROOT / "data/npc_display/static_actor_dialogue_sequence_pages_20260930.csv"

PAGE_COLS = [
    "config_id","record_id","selector_hex","sequence_id","variant_order",
    "controller_pointer","event_record","dialogue_command_addr","text_record_id","text_pointer",
    "condition","speaker_actor_record","speaker_status","page_index","display_order","line_count",
    "line_1","line_2","line_3","page_text","page_boundary_status","advance_status",
    "termination_after_page","choice_status","branch_target_status","confidence",
    "raw_token_start_index","raw_token_end_index","evidence","provenance"
]

def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def ptr_num(p):
    if not p or ":" not in p:
        return 0
    b, a = p.split(":")
    return int(b, 16) * 0x10000 + int(a, 16)

def parse_events(s):
    out = []
    for item in (s or "").split(" | "):
        m = re.match(r"^(\d+):([^:]+):(.*)$", item, re.S)
        if m:
            out.append({"idx": int(m.group(1)), "token": m.group(2), "decoded": m.group(3)})
    return out

def build(source_head=None):
    binding = rows(BINDING)
    hist = rows(HIST)
    decode = rows(DECODE)
    event_source = rows(EVENT_SOURCE)

    hist_by_ptr = {}
    for h in hist:
        if h.get("historical_file") == "data/csv/shinmomo_v33_test_C8_A7DD.csv":
            hist_by_ptr.setdefault(h.get("selected_source_cpu", ""), h)

    decode_by_key = {
        f'{d.get("seg","")}|{d.get("start_bank","")}:{d.get("start_addr","")}': d
        for d in decode
    }
    source_count = collections.Counter(r.get("record_id", "") for r in event_source)

    selected = [b for b in binding if b.get("decoded_text") or b.get("record_id") == "F50-L001"]
    selected.sort(key=lambda b: (
        b.get("config_id",""),
        b.get("record_id",""),
        ptr_num(b.get("dialogue_command_addr",""))
    ))

    actors = collections.OrderedDict()
    decoded_sequences = 0

    for b in selected:
        key = (b.get("config_id",""), b.get("record_id",""))
        actors.setdefault(key, {
            "config_id": b.get("config_id",""),
            "record_id": b.get("record_id",""),
            "selector_hex": b.get("selector_hex",""),
            "controller_pointer": b.get("controller_pointer",""),
            "event_refs": [{
                "event_record": b.get("event_record",""),
                "controller_pointer": b.get("controller_pointer","")
            }],
            "dialogue_sequences": []
        })

        h = hist_by_ptr.get(b.get("text_pointer",""))
        d = decode_by_key.get(
            f'{h.get("historical_seg","")}|{h.get("selected_source_cpu","")}'
        ) if h else None

        raw_text = ((d or {}).get("text") or b.get("decoded_text") or "").replace("<00>", "")
        blocks = [m.group(0) for m in re.finditer(r"「[\s\S]*?」", raw_text)]
        if not blocks and raw_text.strip():
            blocks = [raw_text]

        events = parse_events((d or {}).get("events",""))
        starts = [e["idx"] for e in events if e["token"] == "7D"]
        ends = [e["idx"] for e in events if e["token"] == "7E"]

        seq_id = (
            f'{b.get("config_id")}:{b.get("record_id")}:'
            f'{b.get("text_record_id") or "no_text_id"}'
        )
        pages = []
        for i, block in enumerate(blocks):
            lines = block.split("\n")
            start = starts[i] if i < len(starts) else None
            end = ends[i] if i < len(ends) else None
            page_events = [
                e for e in events
                if start is not None and end is not None and start <= e["idx"] <= end
            ]
            pages.append({
                "page_index": i + 1,
                "display_order": i + 1,
                "page_text": block,
                "lines": [
                    {
                        "line_index": j + 1,
                        "text": text,
                        "line_break_after": j < len(lines) - 1,
                        "line_break_token": "0x01" if j < len(lines) - 1 else None
                    }
                    for j, text in enumerate(lines)
                ],
                "line_count": len(lines),
                "source_token_span": {"start_index": start, "end_index": end},
                "source_events": page_events,
                "page_boundary": {
                    "basis": "quote_delimited_7D_7E_block",
                    "status": "strong_candidate",
                    "evidence": (
                        "recovered F50 quote blocks align to <=3 explicit display lines; "
                        "0x7D/0x7E themselves are literal quote glyphs"
                    )
                },
                "advance": {
                    "required_between_pages": "candidate" if i < len(blocks) - 1 else "no_next_page",
                    "input": None,
                    "status": "unresolved_static" if i < len(blocks) - 1 else "not_applicable"
                }
            })

        if d:
            decoded_sequences += 1

        actors[key]["dialogue_sequences"].append({
            "sequence_id": seq_id,
            "variant_order": 0,
            "sequence_kind": (
                "conditional_variant"
                if source_count[b.get("record_id","")] > 1
                else "single_source_path"
            ),
            "event": {
                "record_id": b.get("event_record",""),
                "controller_pointer": b.get("controller_pointer",""),
                "dialogue_command_addr": b.get("dialogue_command_addr","")
            },
            "source": {
                "text_record_id": b.get("text_record_id",""),
                "text_pointer": b.get("text_pointer",""),
                "decode_status": b.get("decode_status",""),
                "decoder_score": int(d["score"]) if d and d.get("score") else None,
                "decoder_unknown_tokens": int(d["unknown"]) if d and d.get("unknown") else None,
                "raw_tokens": (d or {}).get("raw_tokens") or None,
                "record_terminator": "0x00"
            },
            "speaker": {
                "actor_record_id": b.get("record_id",""),
                "name": None,
                "status": "actor_bound_speaker_identity_unresolved"
            },
            "condition": {
                "description": b.get("condition",""),
                "status": (
                    "predicate_unresolved_static"
                    if source_count[b.get("record_id","")] > 1
                    else "no_alternative_source_detected_in_record"
                ),
                "source_variant_count": source_count[b.get("record_id","")],
                "guarded_selector_subform": (
                    "0x07" if b.get("record_id") == "F50-L005"
                    else "0x0C" if b.get("record_id") == "F50-L007"
                    else None
                )
            },
            "pages": pages,
            "choices": [],
            "choice_status": "no_choice_control_identified_static",
            "branch_target": {"status": "event_continuation_unresolved", "target": None},
            "termination": {
                "text_record_end": "0x00",
                "text_record_end_status": "confirmed_static" if d else "source_known_decode_unavailable",
                "event_end_status": "unresolved_static"
            },
            "confidence": b.get("confidence",""),
            "evidence": b.get("evidence",""),
            "provenance": b.get("provenance","")
        })

    page_rows = []
    for actor in actors.values():
        actor["dialogue_sequences"].sort(
            key=lambda s: ptr_num(s["event"]["dialogue_command_addr"])
        )
        for variant_order, seq in enumerate(actor["dialogue_sequences"], 1):
            seq["variant_order"] = variant_order
            for page in seq["pages"]:
                lines = [x["text"] for x in page["lines"]]
                page_rows.append({
                    "config_id": actor["config_id"],
                    "record_id": actor["record_id"],
                    "selector_hex": actor["selector_hex"],
                    "sequence_id": seq["sequence_id"],
                    "variant_order": variant_order,
                    "controller_pointer": actor["controller_pointer"],
                    "event_record": seq["event"]["record_id"],
                    "dialogue_command_addr": seq["event"]["dialogue_command_addr"],
                    "text_record_id": seq["source"]["text_record_id"],
                    "text_pointer": seq["source"]["text_pointer"],
                    "condition": seq["condition"]["description"],
                    "speaker_actor_record": actor["record_id"],
                    "speaker_status": seq["speaker"]["status"],
                    "page_index": page["page_index"],
                    "display_order": page["display_order"],
                    "line_count": page["line_count"],
                    "line_1": lines[0] if len(lines) > 0 else "",
                    "line_2": lines[1] if len(lines) > 1 else "",
                    "line_3": lines[2] if len(lines) > 2 else "",
                    "page_text": page["page_text"],
                    "page_boundary_status": page["page_boundary"]["status"],
                    "advance_status": page["advance"]["status"],
                    "termination_after_page": (
                        "logical_record_0x00"
                        if page["page_index"] == len(seq["pages"])
                        else "continue_same_source_record"
                    ),
                    "choice_status": seq["choice_status"],
                    "branch_target_status": seq["branch_target"]["status"],
                    "confidence": seq["confidence"],
                    "raw_token_start_index": page["source_token_span"]["start_index"],
                    "raw_token_end_index": page["source_token_span"]["end_index"],
                    "evidence": seq["evidence"],
                    "provenance": seq["provenance"]
                })

    actor_list = list(actors.values())
    f50 = [a for a in actor_list if a.get("config_id") == "cfg_t04_l008_v2"]
    all_pages = [
        page
        for actor in actor_list
        for seq in actor["dialogue_sequences"]
        for page in seq["pages"]
    ]
    coverage = {
        "selected_actor_bindings": len(selected),
        "decoded_sequences": decoded_sequences,
        "page_rows": len(all_pages),
        "max_lines_per_recovered_page": max(
            [p["line_count"] for p in all_pages], default=0
        ),
        "pages_over_3_lines": sum(1 for p in all_pages if p["line_count"] > 3),
        "f50_actors": len(f50),
        "f50_sequence_variants": sum(len(a["dialogue_sequences"]) for a in f50),
        "f50_decoded_sequence_variants": sum(
            1 for a in f50 for s in a["dialogue_sequences"] if s["pages"]
        ),
        "f50_pages": sum(
            len(s["pages"]) for a in f50 for s in a["dialogue_sequences"]
        )
    }

    obj = {
        "schema_version": "2026-09-30-dialogue-sequence-v1",
        "source_main_head": source_head,
        "purpose": (
            "HTML actor click -> event -> conditional dialogue sequence "
            "-> display page playback"
        ),
        "rom_text_control_facts": {
            "0x00": {
                "role": "logical text record terminator",
                "status": "confirmed_static"
            },
            "0x01": {
                "role": "explicit in-record line break",
                "status": "confirmed_static"
            },
            "0x7D": {
                "role": "literal opening Japanese quote glyph 「",
                "status": "confirmed_static"
            },
            "0x7E": {
                "role": "literal closing Japanese quote glyph 」",
                "status": "confirmed_static"
            },
            "page_boundary": {
                "role": (
                    "quote-delimited 0x7D..0x7E block used as "
                    "display-page candidate"
                ),
                "status": "strong_candidate",
                "evidence": (
                    "all recovered F50 quote blocks have <=3 explicit lines; "
                    "long records split into multiple quote-delimited blocks"
                )
            },
            "button_advance": {
                "role": "advance between display pages",
                "status": "unresolved_static",
                "input": None
            },
            "choice_control": {
                "role": "choice/menu control within dialogue source",
                "status": "not_identified_static"
            }
        },
        "coverage": coverage,
        "actors": actor_list
    }

    OUT_JSON.write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    with OUT_PAGES.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PAGE_COLS)
        w.writeheader()
        w.writerows(page_rows)

    print(json.dumps(coverage, ensure_ascii=False))
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_PAGES}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--source-head",
        default=None,
        help="main HEAD used to build the checked-in artifacts"
    )
    args = ap.parse_args()
    build(args.source_head)

if __name__ == "__main__":
    main()
