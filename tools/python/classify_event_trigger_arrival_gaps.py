#!/usr/bin/env python3
import csv, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
trans=list(csv.DictReader((ROOT/'data/maps/transitions/map_transition_candidates.csv').open(encoding='utf-8-sig')))
gaps=list(csv.DictReader((ROOT/'data/events/event_trigger_crosslink_gaps.csv').open(encoding='utf-8-sig')))
rows=[]
for g in gaps:
    if g['gap_class']!='arrival_xy_only': continue
    addr=g['transition_id'].replace('transition_','').replace('_',':')
    t=next((r for r in trans if r.get('trigger_addr')==addr),{})
    pair=(t.get('destination_pack',''),t.get('destination_entry_id',''))
    same=[r for r in trans if (r.get('destination_pack'),r.get('destination_entry_id'))==pair and r.get('destination_x') and r.get('destination_y')]
    rows.append({'transition_id':g['transition_id'],'trigger_addr':addr,'destination_pack':pair[0],'destination_entry_id':pair[1],'destination_config_id':g['destination_config_id'],'same_pair_known_arrival_count':len(same),'classification':'needs_new_coordinate_evidence' if not same else 'same_pair_crosslink_available','next_evidence':'recover aligned opcode 0x58 / saved-state arrival / independent route-table coordinate evidence' if not same else 'crosslink same destination pack+entry'})
out=ROOT/'data/events/event_trigger_arrival_gap_provenance.csv'
with out.open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
summary={'arrival_xy_only_count':len(rows),'same_pair_crosslink_available':sum(r['same_pair_known_arrival_count']>0 for r in rows),'needs_new_coordinate_evidence':sum(r['same_pair_known_arrival_count']==0 for r in rows),'source':'committed map_transition_candidates.csv + event_trigger_crosslink_gaps.csv'}
(ROOT/'data/events/event_trigger_arrival_gap_provenance_summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary))