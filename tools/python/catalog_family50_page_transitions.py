#!/usr/bin/env python3
from pathlib import Path
import csv, json, re
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/"data/dialogue/family50_canonical_direct_decode_20260930.csv"
OUT=ROOT/"data/dialogue/family50_page_transition_invariants_20260930.csv"
SUM=ROOT/"data/dialogue/family50_page_transition_summary_20260930.json"
def events(s):
    out=[]
    for item in (s or "").split(" | "):
        m=re.match(r"^(\\d+):([^:]+):(.*)$",item,re.S)
        if m: out.append({"idx":int(m.group(1)),"token":m.group(2)})
    return out
with SRC.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
out=[]
for r in rows:
    ev=events(r.get("events","")); starts=[e["idx"] for e in ev if e["token"]=="7D"]; ends=[e["idx"] for e in ev if e["token"]=="7E"]
    for i in range(min(len(starts),len(ends))-1):
        st,en,nx=starts[i],ends[i],starts[i+1]
        internal=sum(1 for e in ev if st<=e["idx"]<=en and e["token"]=="01")
        padding=sum(1 for e in ev if en<e["idx"]<nx and e["token"]=="01"); total=internal+padding
        out.append({"subindex_hex":r["subindex_hex"],"text_pointer":r["text_pointer"],"page_index":i+1,"line_count":internal+1,"internal_line_breaks":internal,"padding_line_breaks_to_next_page":padding,"total_line_breaks_before_next_page":total,"expected_total_line_breaks":3,"invariant_ok":1 if total==3 else 0,"page_end_token_index":en,"next_page_start_token_index":nx,"evidence_class":"confirmed_static_family50" if total==3 else "mismatch_requires_review"})
with OUT.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
s={"schema_version":1,"scope":"family 0x50 canonical direct dialogue corpus","transition_count":len(out),"invariant_match_count":sum(int(x["invariant_ok"]) for x in out),"invariant_mismatch_count":sum(1-int(x["invariant_ok"]) for x in out),"invariant":"internal 0x01 line breaks inside page + padding 0x01 line breaks before next page = 3","page_capacity_lines":3,"normalized_button_layout":{"bit7":"A","bit6":"X","bit5":"L","bit4":"R","bit3":"B","bit2":"Y","bit1":"Select","bit0":"Start"},"primary_mask":"0xFC","primary_buttons":["A","X","L","R","B","Y"],"secondary_mask":"0xF4","secondary_buttons":["A","X","L","R","Y"],"dpad_source":"DP $59"}
SUM.write_text(json.dumps(s,ensure_ascii=False,indent=2)+"\\n",encoding="utf-8")
print(json.dumps(s,ensure_ascii=False))
