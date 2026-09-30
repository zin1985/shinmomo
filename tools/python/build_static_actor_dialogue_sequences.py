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
DIRECT = ROOT / "data/dialogue/family50_canonical_direct_decode_20260930.csv"
CONDITIONS = ROOT / "data/npc_display/static_actor_dialogue_conditions_20260930.csv"
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
    direct = rows(DIRECT)
    conditions = rows(CONDITIONS)
    event_source = rows(EVENT_SOURCE)

    hist_by_ptr = {}
    for h in hist:
        if h.get("historical_file") == "data/csv/shinmomo_v33_test_C8_A7DD.csv":
            hist_by_ptr.setdefault(h.get("selected_source_cpu", ""), h)
    decode_by_key = {
        f'{d.get("seg","")}|{d.get("start_bank","")}:{d.get("start_addr","")}': d
        for d in decode
    }
    direct_by_ptr = {r.get("text_pointer",""): r for r in direct}
    cond_by_key = {
        (r.get("config_id",""), r.get("record_id",""), r.get("subindex_hex","")): r
        for r in conditions
    }
    source_count = collections.Counter(r.get("record_id", "") for r in binding if r.get("text_pointer"))

    selected = [b for b in binding if b.get("decoded_text")]
    selected.sort(key=lambda b: (
        b.get("config_id",""), b.get("record_id",""), ptr_num(b.get("dialogue_command_addr",""))
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
            "event_refs": [{"event_record": b.get("event_record",""), "controller_pointer": b.get("controller_pointer","")}],
            "dialogue_sequences": []
        })

        d = direct_by_ptr.get(b.get("text_pointer",""))
        direct_used = d is not None
        if d is None:
            h = hist_by_ptr.get(b.get("text_pointer",""))
            d = decode_by_key.get(
                f'{h.get("historical_seg","")}|{h.get("selected_source_cpu","")}'
            ) if h else None

        raw_text = ((d or {}).get("decoded_text") or (d or {}).get("text") or b.get("decoded_text") or "").replace("<00>", "")
        blocks = [m.group(0) for m in re.finditer(r"「[\s\S]*?」", raw_text)]
        if not blocks and raw_text.strip():
            blocks = [raw_text]
        events = parse_events((d or {}).get("events",""))
        starts = [e["idx"] for e in events if e["token"] == "7D"]
        ends = [e["idx"] for e in events if e["token"] == "7E"]

        text_id = b.get("text_record_id","")
        subindex_hex = text_id.split(":")[-1] if ":" in text_id else ""
        c = cond_by_key.get((b.get("config_id",""), b.get("record_id",""), subindex_hex))
        seq_id = f'{b.get("config_id")}:{b.get("record_id")}:{text_id or "no_text_id"}'
        pages = []
        for i, block in enumerate(blocks):
            lines = block.split("\n")
            start = starts[i] if i < len(starts) else None
            end = ends[i] if i < len(ends) else None
            page_events = [e for e in events if start is not None and end is not None and start <= e["idx"] <= end]
            pages.append({
                "page_index": i + 1, "display_order": i + 1, "page_text": block,
                "lines": [
                    {"line_index": j + 1, "text": text, "line_break_after": j < len(lines) - 1,
                     "line_break_token": "0x01" if j < len(lines) - 1 else None}
                    for j, text in enumerate(lines)
                ],
                "line_count": len(lines),
                "source_token_span": {"start_index": start, "end_index": end},
                "source_events": page_events,
                "page_capacity_lines": 3 if b.get("record_id","").startswith("F50-") else None,
                "transition_padding_line_break_count": (
                    sum(1 for e in events if end is not None and i + 1 < len(starts)
                        and end < e["idx"] < starts[i+1] and e["token"] == "01")
                    if i + 1 < len(blocks) else None
                ),
                "line_advance_count_before_next_page": (
                    (len(lines)-1) + sum(1 for e in events if end is not None and i + 1 < len(starts)
                        and end < e["idx"] < starts[i+1] and e["token"] == "01")
                    if i + 1 < len(blocks) else None
                ),
                "page_boundary": {
                    "basis": "quote_block_aligned_with_three_line_0x01_cadence",
                    "status": (
                        "confirmed_static_family50" if b.get("record_id","").startswith("F50-") and i + 1 < len(blocks)
                        and ((len(lines)-1) + sum(1 for e in events if end is not None and end < e["idx"] < starts[i+1] and e["token"] == "01") == 3)
                        else "confirmed_static_family50_final_page_shape" if b.get("record_id","").startswith("F50-") and i + 1 == len(blocks)
                        else "strong_candidate"
                    ),
                    "evidence": "F50 canonical corpus: 17/17 inter-page transitions consume exactly three 0x01 line advances" if b.get("record_id","").startswith("F50-") else "quote-delimited page candidate"
                },
                "advance": (
                    {"required_between_pages":"strong_candidate","boundary_trigger":"three_line_0x01_cadence_exhausted",
                     "input":{"source":"normalized held-input DP $57","state_handler":"C4:A264","primary_mask":"0xFC","secondary_mask":"0xF4","gate":"$12C0","gate_init":"0xFF at C4:9FEB","normalized_button_layout":{"bit7":"A","bit6":"X","bit5":"L","bit4":"R","bit3":"B","bit2":"Y","bit1":"Select","bit0":"Start"},"primary_buttons":["A","X","L","R","B","Y"],"secondary_buttons":["A","X","L","R","Y"],"dpad_source":"DP $59","exact_button_names_status":"confirmed_mask_mapping","edge_semantics":"handler reads held $57; generic new-press edges are $5B/$5D"},
                     "status":"strong_candidate_static_display_state"}
                    if b.get("record_id","").startswith("F50-") and i < len(blocks)-1
                    else {"required_between_pages":"no_next_page","input":None,"status":"not_applicable"}
                )
            })

        if d:
            decoded_sequences += 1
        cond_obj = {
            "description": b.get("condition",""),
            "status": c.get("condition_status") if c else (
                "predicate_unresolved_static" if source_count[b.get("record_id","")] > 1
                else "no_alternative_source_detected_in_record"
            ),
            "source_variant_count": source_count[b.get("record_id","")],
            "expression": c.get("condition_expr") if c else None,
            "condition_id": c.get("condition_id") if c else None,
            "common_predicate": c.get("common_predicate") if c else None,
            "flag_tests": [],
            "relation_test": None,
            "branch_path": c.get("branch_path") if c else None,
        }
        if c and c.get("flag_0x65_wram"):
            cond_obj["flag_tests"].append({
                "spec": "0x65", "wram": c.get("flag_0x65_wram"), "bit": int(c.get("flag_0x65_bit") or 0)
            })
        if c and c.get("secondary_flag_wram"):
            cond_obj["flag_tests"].append({
                "spec": c.get("secondary_flag_spec"), "wram": c.get("secondary_flag_wram"),
                "bit": int(c.get("secondary_flag_bit") or 0)
            })
        if c and c.get("relation_key"):
            cond_obj["relation_test"] = {
                "key": c.get("relation_key"), "subkey": c.get("relation_subkey"),
                "resolver": "80:DA57", "semantic_identity": "unresolved_relation_key"
            }

        actors[key]["dialogue_sequences"].append({
            "sequence_id": seq_id, "variant_order": 0,
            "sequence_kind": "conditional_variant" if source_count[b.get("record_id","")] > 1 else "single_source_path",
            "event": {
                "record_id": b.get("event_record",""), "controller_pointer": b.get("controller_pointer",""),
                "dialogue_command_addr": b.get("dialogue_command_addr","")
            },
            "source": {
                "text_record_id": text_id, "text_pointer": b.get("text_pointer",""),
                "decode_status": b.get("decode_status",""),
                "decoder_score": int(d["score"]) if d and d.get("score") else None,
                "decoder_unknown_tokens": int(d["unknown"]) if d and d.get("unknown") else None,
                "raw_tokens": (d or {}).get("raw_tokens") or None,
                "record_terminator": "0x00",
                "decode_provenance": "canonical_direct_family50" if direct_used else "historical_exact_token_overlay"
            },
            "speaker": {"actor_record_id": b.get("record_id",""), "name": None, "status": "actor_bound_speaker_identity_unresolved"},
            "condition": cond_obj,
            "pages": pages, "choices": [], "choice_status": "no_choice_control_identified_static",
            "branch_target": {"status": "event_continuation_unresolved", "target": None},
            "termination": {
                "text_record_end": "0x00", "text_record_end_status": "confirmed_static" if d else "source_known_decode_unavailable",
                "event_end_status": "unresolved_static"
            },
            "confidence": b.get("confidence",""), "evidence": b.get("evidence",""), "provenance": b.get("provenance","")
        })

    page_rows = []
    for actor in actors.values():
        actor["dialogue_sequences"].sort(key=lambda s: ptr_num(s["event"]["dialogue_command_addr"]))
        for variant_order, seq in enumerate(actor["dialogue_sequences"], 1):
            seq["variant_order"] = variant_order
            for page in seq["pages"]:
                lines = [x["text"] for x in page["lines"]]
                page_rows.append({
                    "config_id": actor["config_id"], "record_id": actor["record_id"], "selector_hex": actor["selector_hex"],
                    "sequence_id": seq["sequence_id"], "variant_order": variant_order,
                    "controller_pointer": actor["controller_pointer"], "event_record": seq["event"]["record_id"],
                    "dialogue_command_addr": seq["event"]["dialogue_command_addr"],
                    "text_record_id": seq["source"]["text_record_id"], "text_pointer": seq["source"]["text_pointer"],
                    "condition": seq["condition"].get("expression") or seq["condition"].get("description") or "",
                    "speaker_actor_record": actor["record_id"], "speaker_status": seq["speaker"]["status"],
                    "page_index": page["page_index"], "display_order": page["display_order"], "line_count": page["line_count"],
                    "line_1": lines[0] if len(lines)>0 else "", "line_2": lines[1] if len(lines)>1 else "",
                    "line_3": lines[2] if len(lines)>2 else "", "page_text": page["page_text"],
                    "page_boundary_status": page["page_boundary"]["status"], "advance_status": page["advance"]["status"],
                    "termination_after_page": "logical_record_0x00" if page["page_index"] == len(seq["pages"]) else "continue_same_source_record",
                    "choice_status": seq["choice_status"], "branch_target_status": seq["branch_target"]["status"],
                    "confidence": seq["confidence"], "raw_token_start_index": page["source_token_span"]["start_index"],
                    "raw_token_end_index": page["source_token_span"]["end_index"],
                    "evidence": seq["evidence"], "provenance": seq["provenance"]
                })

    actor_list = list(actors.values())
    f50 = [a for a in actor_list if a.get("config_id") == "cfg_t04_l008_v2"]
    all_pages = [p for a in actor_list for s in a["dialogue_sequences"] for p in s["pages"]]
    coverage = {
        "selected_actor_bindings": len(selected),
        "decoded_sequences": decoded_sequences,
        "page_rows": len(all_pages),
        "max_lines_per_recovered_page": max([p["line_count"] for p in all_pages], default=0),
        "pages_over_3_lines": sum(1 for p in all_pages if p["line_count"] > 3),
        "f50_actors": len(f50),
        "f50_sequence_variants": sum(len(a["dialogue_sequences"]) for a in f50),
        "f50_decoded_sequence_variants": sum(1 for a in f50 for s in a["dialogue_sequences"] if s["pages"]),
        "f50_pages": sum(len(s["pages"]) for a in f50 for s in a["dialogue_sequences"]),
        "f50_exact_condition_actors": sum(1 for a in f50 if any(s["condition"].get("condition_status") == "confirmed_static_cfg" for s in a["dialogue_sequences"]))
    }

    obj = {
        "schema_version": "2026-09-30-dialogue-sequence-v3",
        "source_main_head": source_head,
        "purpose": "HTML actor click -> event -> conditional dialogue sequence -> display page playback",
        "rom_text_control_facts": {
            "0x00": {"role":"logical text record terminator","status":"confirmed_static"},
            "0x01": {"role":"explicit in-record line break","status":"confirmed_static"},
            "0x7D": {"role":"literal opening Japanese quote glyph 「","status":"confirmed_static"},
            "0x7E": {"role":"literal closing Japanese quote glyph 」","status":"confirmed_static"},
            "page_boundary": {
                "role":"family-0x50 page transition aligns to a three-line 0x01 cadence; quote glyphs remain literal presentation characters",
                "status":"confirmed_static_family50",
                "evidence":"17/17 canonical-direct F50 inter-page transitions satisfy internal line breaks + post-quote padding line breaks = 3"
            },
            "button_advance": {
                "role":"display-state input gate reached at page cadence boundary",
                "status":"strong_candidate",
                "input":{"source":"normalized held-input DP $57","display_state_handler":"C4:A264","primary_mask":"0xFC","secondary_mask":"0xF4","gate":"$12C0","gate_init":"0xFF at C4:9FEB","normalized_button_layout":{"bit7":"A","bit6":"X","bit5":"L","bit4":"R","bit3":"B","bit2":"Y","bit1":"Select","bit0":"Start"},"primary_buttons":["A","X","L","R","B","Y"],"secondary_buttons":["A","X","L","R","Y"],"dpad_source":"DP $59","exact_button_names_status":"confirmed_mask_mapping"},
                "evidence":"C4 display-state machine includes input-sensitive state A264; generic C0 joypad pipeline retains held state in $57/$59 and new-press edges in $5B/$5D",
                "caveat":"exact accepted button names and release/autorepeat semantics remain unresolved"
            },
            "choice_control": {"role":"choice/menu control within dialogue source","status":"not_identified_static"}
        },
        "condition_vm_facts": {
            "A3":{"role":"flag bit test; pushes boolean","status":"confirmed_static"},
            "B2":{"role":"unconditional signed rel8 branch","status":"confirmed_static"},
            "B3":{"role":"branch on zero, otherwise fall through","status":"confirmed_static"},
            "B4":{"role":"branch on nonzero, otherwise fall through","status":"confirmed_static"},
            "E1":{"role":"boolean zero-test over expression accumulator","status":"confirmed_static"},
            "E7":{"role":"boolean conjunction with previously stacked operand","status":"confirmed_static"},
            "f50_common_predicate":{
                "expression":"and(flag_test(spec=0x65,wram=$1252,bit=5),zero_test(relation_resolver_condition(key=0x90,subkey=0x00)))",
                "status":"confirmed_static_structure",
                "semantic_note":"relation key 0x90 identity remains unresolved; do not label it as a specific character without independent evidence"
            }
        },
        "coverage": coverage,
        "actors": actor_list
    }
    json_text = json.dumps(obj, ensure_ascii=False, indent=2) + "\n"
    OUT_JSON.write_text(json_text, encoding="utf-8")
    with OUT_PAGES.open("w", encoding="utf-8-sig", newline="") as f:
        w=csv.DictWriter(f,fieldnames=PAGE_COLS); w.writeheader(); w.writerows(page_rows)
    print(json.dumps(coverage, ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-head", default=None)
    args=ap.parse_args()
    build(args.source_head)

if __name__ == "__main__":
    main()
