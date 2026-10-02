#!/usr/bin/env python3
import csv, json
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'data/events/event_trigger_regions.csv'
OUT = ROOT / 'data/events/event_trigger_crosslink_gaps.csv'
SUMMARY = ROOT / 'data/events/event_trigger_crosslink_gaps_summary.json'
FIELDS = ['region_id','transition_id','source_config_id','gap_class','destination_config_id','destination_x','destination_y','predicate_layer','region_shape','confidence','next_evidence_needed']
rows=[]
with SRC.open(encoding='utf-8-sig', newline='') as f:
    for r in csv.DictReader(f):
        missing_cfg = not bool(r['destination_config_id'])
        missing_xy = not (bool(r['destination_x']) and bool(r['destination_y']))
        if not (missing_cfg or missing_xy):
            continue
        if missing_cfg and not missing_xy:
            gap='destination_config_only'
            need='resolve destination pack/entry to canonical config; arrival XY already known'
        elif missing_xy and not missing_cfg:
            gap='arrival_xy_only'
            need='resolve destination entry coordinate setter or saved-state arrival; canonical config already known'
        else:
            gap='destination_config_and_arrival_xy'
            need='resolve destination pack/entry/config then arrival semantics'
        rows.append({k:r.get(k,'') for k in FIELDS} | {'gap_class':gap,'next_evidence_needed':need})
with OUT.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator='\n'); w.writeheader(); w.writerows(rows)
counts=Counter(r['gap_class'] for r in rows)
summary={'schema_version':1,'source':str(SRC.relative_to(ROOT)).replace('\\','/'),'gap_count':len(rows),'gap_class_counts':dict(sorted(counts.items())),'fully_crosslinked_region_count':57-len(rows),'note':'Gap manifest is provenance bookkeeping only; unresolved rows are not promoted by inference.'}
SUMMARY.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))