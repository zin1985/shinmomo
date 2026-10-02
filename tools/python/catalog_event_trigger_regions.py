#!/usr/bin/env python3
import csv, json
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'data/maps/transitions/source_transition_hotspots.csv'
OUT = ROOT / 'data/events/event_trigger_regions.csv'
SUMMARY = ROOT / 'data/events/event_trigger_regions_summary.json'
FIELDS = ['region_id','source_config_id','x_min','x_max','y_min','y_max','region_shape','predicate_layer','predicate_semantics','predicate_addr','transition_id','destination_config_id','destination_x','destination_y','confidence','source_hotspot_id','evidence','provenance']

def normalize(row):
    x = int(row['source_grid_x']); y = int(row['source_grid_y'])
    w = int(row['source_width']); h = int(row['source_height']); ht = row['hotspot_type']
    if ht == 'vm_opcode_0x69_exact_point':
        shape, layer, sem, addr = 'point', 'vm', 'coordinate_equal', 'C4:9320'
    elif ht == 'vm_opcode_0x5D_inclusive_rect':
        shape, layer, sem, addr = 'rectangle', 'vm', 'inclusive_rectangle', 'C4:908D'
    elif ht == 'native_boundary_saved_return_candidate_corridor':
        shape, layer, sem, addr = 'corridor', 'native_boundary', 'out_of_bounds_saved_state_restore', row['trigger_addr']
    elif ht == 'native_boundary_saved_return_exit':
        shape, layer, sem, addr = 'point', 'native_boundary', 'out_of_bounds_saved_state_restore', row['trigger_addr']
    else:
        shape, layer, sem, addr = 'unknown', 'unknown', row['trigger_type'], row['trigger_addr']
    return {'region_id':'region_'+row['hotspot_id'],'source_config_id':row['source_config_id'],'x_min':x,'x_max':x+w-1,'y_min':y,'y_max':y+h-1,'region_shape':shape,'predicate_layer':layer,'predicate_semantics':sem,'predicate_addr':addr,'transition_id':row['transition_id'],'destination_config_id':row['destination_config_id'],'destination_x':row['destination_x'],'destination_y':row['destination_y'],'confidence':row['confidence'],'source_hotspot_id':row['hotspot_id'],'evidence':row['evidence'],'provenance':row['provenance']}
with SRC.open(encoding='utf-8-sig', newline='') as f:
    rows = [normalize(r) for r in csv.DictReader(f)]
OUT.parent.mkdir(parents=True, exist_ok=True)
with OUT.open('w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator='\n'); w.writeheader(); w.writerows(rows)
shapes = Counter(r['region_shape'] for r in rows); layers = Counter(r['predicate_layer'] for r in rows)
summary = {
    'schema_version':1,'source':str(SRC.relative_to(ROOT)).replace('\\','/'),'region_count':len(rows),
    'shape_counts':dict(sorted(shapes.items())),'predicate_layer_counts':dict(sorted(layers.items())),
    'destination_config_resolved':sum(bool(r['destination_config_id']) for r in rows),
    'arrival_xy_resolved':sum(bool(r['destination_x']) and bool(r['destination_y']) for r in rows),
    'semantics':{'point':'VM exact coordinate or confirmed native exit point','rectangle':'VM opcode 0x5D inclusive coordinate rectangle','corridor':'native boundary candidate corridor; not terrain passability'}
}
SUMMARY.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
