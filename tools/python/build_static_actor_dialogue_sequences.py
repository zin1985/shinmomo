#!/usr/bin/env python3
from pathlib import Path
import csv, json, re, collections

ROOT = Path(__file__).resolve().parents[2]
BINDING = ROOT / "data/npc_display/static_actor_event_dialogue_binding_20260930.csv"
HIST = ROOT / "data/dialogue/historical_decode_crosswalk.csv"
DECODE = ROOT / "data/csv/shinmomo_v33_test_C8_A7DD.csv"
EVENT_SOURCE = ROOT / "data/events/event_source_crosslink.csv"
OUT_JSON = ROOT / "data/npc_display/static_actor_dialogue_sequences_20260930.json"
OUT_PAGES = ROOT / "data/npc_display/static_actor_dialogue_sequence_pages_20260930.csv"

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

binding = rows(BINDING)
hist = rows(HIST)
decode = rows(DECODE)
event_source = rows(EVENT_SOURCE)

hist_by_ptr = {}
for h in hist:
    if h.get("historical_file") == "data/csv/shinmomo_v33_test_C8_A7DD.csv":
        hist_by_ptr.setdefault(h.get("selected_source_cpu", ""), h)

decode_by_key = {f'{d.get("seg","")}|{d.get("start_bank","")}:{d.get("start_addr","")}': d for d in decode}
source_count = collections.Counter(r.get("record_id", "") for r in event_source)

selected = [b for b in binding if b.get("decoded_text") or b.get("record_id") == "F50-L001"]
selected.sort(key=lambda b: (b.get("config_id",""), b.get("record_id",""), ptr_num(b.get("dialogue_command_addr",""))))

actors = collections.OrderedDict()
page_rows = []
for b in selected:
    key = (b.get("config_id",""), b.get("record_id",""))
    actors.setdefault(key, {
        "config_id": b.get("config_id",""), "record_id": b.get("record_id",""),
        "selector_hex": b.get("selector_hex",""), "controller_pointer": b.get("controller_pointer",""),
        "event_refs": [{"event_record": b.get("event_record",""), "controller_pointer": b.get("controller_pointer","")}],
        "dialogue_sequences": []
    })
    h = hist_by_ptr.get(b.get("text_pointer",""))
    d = decode_by_key.get(f'{h.get("historical_seg","")}|{h.get("selected_source_cpu","")}') if h else None
    raw_text = ((d or {}).get("text") or b.get("decoded_text") or "").replace("<00>", "")
    blocks = [m.group(0) for m in re.finditer(r"「[\s\S]*?」", raw_text)]
    if not blocks and raw_text.strip():
        blocks = [raw_text]
    events = parse_events((d or {}).get("events",""))
    starts = [e["idx"] for e in events if e["token"] == "7D"]
    ends = [e["idx"] for e in events if e["token"] == "7E"]
    seq_id = f'{b.get("config_id")}:{b.get("record_id")}:{b.get("text_record_id") or "no_text_id"}'
    pages = []
    for i, block in enumerate(blocks):
        lines = block.split("\n")
        start = starts[i] if i < len(starts) else None
        end = ends[i] if i < len(ends) else None
        pages.append({
            "page_index": i+1, "display_order": i+1, "page_text": block,
            "lines": [{"line_index": j+1, "text": t, "line_break_after": j < len(lines)-1,
                       "line_break_token": "0x01" if j < len(lines)-1 else None} for j,t in enumerate(lines)],
            "line_count": len(lines),
            "source_token_span": {"start_index": start, "end_index": end},
            "source_events": [e for e in events if start is not None and end is not None and start <= e["idx"] <= end],
            "page_boundary": {"basis": "quote_delimited_7D_7E_block", "status": "strong_candidate"},
            "advance": {"required_between_pages": "candidate" if i < len(blocks)-1 else "no_next_page",
                        "input": None, "status": "unresolved_static" if i < len(blocks)-1 else "not_applicable"}
        })
    seq = {
        "sequence_id": seq_id, "variant_order": 0,
        "sequence_kind": "conditional_variant" if source_count[b.get("record_id","")] > 1 else "single_source_path",
        "event": {"record_id": b.get("event_record",""), "controller_pointer": b.get("controller_pointer",""),
                  "dialogue_command_addr": b.get("dialogue_command_addr","")},
        "source": {"text_record_id": b.get("text_record_id",""), "text_pointer": b.get("text_pointer",""),
                   "decode_status": b.get("decode_status",""), "decoder_score": int(d["score"]) if d and d.get("score") else None,
                   "decoder_unknown_tokens": int(d["unknown"]) if d and d.get("unknown") else None,
                   "raw_tokens": (d or {}).get("raw_tokens") or None, "record_terminator": "0x00"},
        "speaker": {"actor_record_id": b.get("record_id",""), "name": None, "status": "actor_bound_speaker_identity_unresolved"},
        "condition": {"description": b.get("condition",""),
                      "status": "predicate_unresolved_static" if source_count[b.get("record_id","")] > 1 else "no_alternative_source_detected_in_record",
                      "source_variant_count": source_count[b.get("record_id","")],
                      "guarded_selector_subform": "0x07" if b.get("record_id") == "F50-L005" else "0x0C" if b.get("record_id") == "F50-L007" else None},
        "pages": pages, "choices": [], "choice_status": "no_choice_control_identified_static",
        "branch_target": {"status": "event_continuation_unresolved", "target": None},
        "termination": {"text_record_end": "0x00", "text_record_end_status": "confirmed_static" if d else "source_known_decode_unavailable",
                        "event_end_status": "unresolved_static"},
        "confidence": b.get("confidence",""), "evidence": b.get("evidence",""), "provenance": b.get("provenance","")
    }
    actors[key]["dialogue_sequences"].append(seq)

for actor in actors.values():
    actor["dialogue_sequences"].sort(key=lambda s: ptr_num(s["event"]["dialogue_command_addr"]))
    for i, seq in enumerate(actor["dialogue_sequences"], 1):
        seq["variant_order"] = i

obj = {
    "schema_version": "2026-09-30-dialogue-sequence-v1",
    "purpose": "HTML actor click -> event -> conditional dialogue sequence -> display page playback",
    "rom_text_control_facts": {
        "0x00": {"role": "logical text record terminator", "status": "confirmed_static"},
        "0x01": {"role": "explicit in-record line break", "status": "confirmed_static"},
        "0x7D": {"role": "literal opening Japanese quote glyph 「", "status": "confirmed_static"},
        "0x7E": {"role": "literal closing Japanese quote glyph 」", "status": "confirmed_static"},
        "page_boundary": {"role": "quote-delimited 0x7D..0x7E block used as display-page candidate", "status": "strong_candidate"},
        "button_advance": {"role": "advance between display pages", "status": "unresolved_static", "input": None},
        "choice_control": {"role": "choice/menu control within dialogue source", "status": "not_identified_static"}
    },
    "actors": list(actors.values())
}
OUT_JSON.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote {OUT_JSON}")
print("NOTE: page CSV is canonical generated output committed beside this script; regeneration should retain the same page-level fields.")
