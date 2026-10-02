#!/usr/bin/env python3
import csv, json
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TRANS=ROOT/'data/maps/transitions/map_transition_candidates.csv'
BOUNDS=ROOT/'data/maps/transitions/map_native_bounds_catalog.csv'
OUT=ROOT/'data/maps/transitions/destination_config_bounds_resolution.csv'
SUMMARY=ROOT/'data/maps/transitions/destination_config_bounds_resolution_summary.json'
FIELDS=['transition_id','trigger_addr','destination_pack','destination_x','destination_y','resolved_config_id','candidate_count','evidence','provenance']
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
trs=read(TRANS); bs=read(BOUNDS); by_pack=defaultdict(list)
for b in bs: by_pack[b['pack_id_hex']].append(b)
out=[]
for r in trs:
    if r['destination_config_id'] or not r['trigger_addr'] or not r['destination_pack'] or r['destination_x']=='' or r['destination_y']=='': continue
    x,y=int(r['destination_x']),int(r['destination_y'])
    candidates=sorted({b['config_id'] for b in by_pack[r['destination_pack']] if int(b['min_x'])<=x<=int(b['max_x']) and int(b['min_y'])<=y<=int(b['max_y'])})
    if len(candidates)!=1: continue
    cfg=candidates[0]
    out.append({'transition_id':'transition_'+r['trigger_addr'].replace(':','_'),'trigger_addr':r['trigger_addr'],'destination_pack':r['destination_pack'],'destination_x':x,'destination_y':y,'resolved_config_id':cfg,'candidate_count':1,'evidence':f"arrival ({x},{y}) is inside {cfg} native opcode-0x52 bounds and outside every other committed native-bounds config for destination pack {r['destination_pack']}",'provenance':'data/maps/transitions/map_transition_candidates.csv;data/maps/transitions/map_native_bounds_catalog.csv'})
OUT.parent.mkdir(parents=True,exist_ok=True)
with OUT.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=FIELDS,lineterminator='\n');w.writeheader();w.writerows(out)
summary={'schema_version':1,'unresolved_transition_input_count':sum(not r['destination_config_id'] and bool(r['destination_pack']) for r in trs),'unique_bounds_resolution_count':len(out),'method':'destination pack + committed arrival XY filtered against committed native opcode-0x52 bounds; emit only exactly-one-config matches'}
SUMMARY.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
