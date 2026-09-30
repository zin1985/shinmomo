#!/usr/bin/env python3
from pathlib import Path
import csv,json,collections

ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
dialogue=list(csv.DictReader(open(
    ROOT/'data/npc_display/static_map_actor_dialogue_crosslink_20260930.csv',
    encoding='utf-8-sig'
)))
visual={r['selector_hex']:r for r in csv.DictReader(open(
    ROOT/'data/npc_display/static_map_bound_selector_visual_form_20260930.csv',
    encoding='utf-8-sig'
))}

out=[]
for r in dialogue:
    v=visual.get(r['selector_hex'],{})
    form=v.get('visual_form','unknown')
    decoded=int(r.get('decoded_dialogue_source_count') or 0)
    source=int(r.get('dialogue_source_count') or 0)
    if form=='humanoid_like' and decoded>0:
        role='dialogue_npc_candidate'
        confidence='high_candidate'
    elif form=='animal_like':
        role='animal_actor_candidate'
        confidence='high_visual'
    elif form in ('monster_like','small_creature_like'):
        role='monster_or_enemy_actor_candidate'
        confidence='visual_only'
    elif form=='object_like':
        role='object_or_prop_actor'
        confidence='high_visual'
    elif form=='plant_or_effect_like':
        role='plant_or_effect_actor'
        confidence='high_visual'
    elif form=='humanoid_like':
        role='humanoid_map_actor_candidate'
        confidence='visual_plus_static_map_binding'
    else:
        role='unclassified_actor'
        confidence='low'
    x=dict(r)
    x.update({
        'visual_form':form,
        'visual_detail':v.get('visual_detail',''),
        'visual_confidence':v.get('visual_confidence',''),
        'role_candidate':role,
        'role_candidate_confidence':confidence,
        'role_evidence_note':(
            'humanoid sprite plus decoded dialogue' if role=='dialogue_npc_candidate' else
            'visual form only; enemy allegiance not yet proven' if role=='monster_or_enemy_actor_candidate' else
            'visual form plus static opcode59 map binding'
        )
    })
    out.append(x)

csv_path=ROOT/'data/npc_display/static_map_actor_semantic_candidates_20260930.csv'
with csv_path.open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0].keys()));w.writeheader();w.writerows(out)

# Aggregate per selector without erasing map/record-level differences.
agg=collections.defaultdict(lambda:{
    'rows':0,'maps':set(),'records':set(),'role_counts':collections.Counter(),
    'visual_forms':set(),'decoded_dialogue_rows':0,'examples':[]
})
for r in out:
    a=agg[r['selector_hex']]
    a['rows']+=1
    if r['config_id']:a['maps'].add(r['config_id'])
    a['records'].add(r['record_id'])
    a['role_counts'][r['role_candidate']]+=1
    a['visual_forms'].add(r['visual_form'])
    if int(r['decoded_dialogue_source_count'] or 0):
        a['decoded_dialogue_rows']+=1
        if r['dialogue_excerpt'] and len(a['examples'])<3:
            a['examples'].append(r['dialogue_excerpt'])

summary={}
for s,a in sorted(agg.items()):
    summary[s]={
        'map_config_count':len(a['maps']),
        'event_record_count':len(a['records']),
        'crosslink_rows':a['rows'],
        'visual_forms':sorted(a['visual_forms']),
        'role_candidate_counts':dict(a['role_counts']),
        'decoded_dialogue_rows':a['decoded_dialogue_rows'],
        'dialogue_examples':a['examples']
    }

sum_path=ROOT/'data/npc_display/static_map_actor_semantic_candidates_summary_20260930.json'
sum_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

role_counts=collections.Counter(r['role_candidate'] for r in out)
selector_roles=collections.defaultdict(set)
for r in out: selector_roles[r['selector_hex']].add(r['role_candidate'])
print('row role counts',dict(role_counts))
print('selector candidates')
for role in sorted(set(role_counts)):
    sels=sorted(s for s,roles in selector_roles.items() if role in roles)
    print(role,len(sels),sels)
