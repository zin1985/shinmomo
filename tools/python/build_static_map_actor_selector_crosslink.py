#!/usr/bin/env python3
from pathlib import Path
import csv,json,collections,re

ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
ROM=Path(r'C:\Users\zin\Downloads\Shin Momotarou Densetsu (J)\Shin Momotarou Densetsu (J)_original.smc').read_bytes()

def parse_addr(s):
    bank,addr=s.split(':')
    bank=int(bank,16); addr=int(addr,16)
    # HiROM physical mapping for the C0-DF ROM banks used by event packs.
    return ((bank & 0x3F)<<16) | addr

selector_rows={}
with (ROOT/'data/npc_display/static_character_selector_catalog_20260930.csv').open(encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        selector_rows[int(r['selector'])]=r

map_rows=[]
with (ROOT/'data/maps/context/map_dialogue_pack_crosslink.csv').open(encoding='utf-8-sig') as f:
    map_rows=list(csv.DictReader(f))
maps_by_family=collections.defaultdict(list)
for r in map_rows:
    maps_by_family[r['source_family_hex'].upper()].append(r)

event_rows=[]
with (ROOT/'data/events/event_record_frame_catalog.csv').open(encoding='utf-8-sig') as f:
    event_rows=list(csv.DictReader(f))

out=[]
unmapped=[]
for er in event_rows:
    body_start=er['body_start']
    body_size=int(er['body_size'])
    if not body_start or body_size < 1:
        continue
    off=parse_addr(body_start)
    body=ROM[off:off+body_size]
    if not body or body[0] != 0x59:
        continue
    if len(body) < 6:
        unmapped.append({'record_id':er['record_id'],'reason':'opcode59_body_too_short','body_hex':body.hex(' ')})
        continue
    sel=body[1]
    sr=selector_rows.get(sel)
    fam=er['family_hex'].upper()
    configs=maps_by_family.get(fam,[])
    if not configs:
        configs=[None]
    for mr in configs:
        label=''
        if fam=='0X50':
            label='旅立ちの村'
        elif mr and mr.get('known_semantic_contexts'):
            label=mr['known_semantic_contexts']
        row={
            'config_id': mr['config_id'] if mr else '',
            'pack_id_hex': mr['pack_id_hex'] if mr else fam.lower(),
            'map_label': label,
            'family_hex':er['family_hex'],
            'record_id':er['record_id'],
            'record_seq':er['record_seq'],
            'record_start':er['record_start'],
            'controller_pointer':er['trailer_start'],
            'body_start':body_start,
            'selector_hex':f'0x{sel:02X}',
            'selector_dec':sel,
            'field_0659_seed':body[2],
            'field_0699_seed':body[3],
            'field_06D9_seed':body[4],
            'field_0719_seed':body[5],
            'body_hex':body.hex(' '),
            'chr_resource':sr['chr_resource'] if sr else '',
            'chr_window_index':sr['chr_window_index'] if sr else '',
            'animation_base_state':sr['base_state'] if sr else '',
            'sprite_group':sr['sprite_group'] if sr else '',
            'palette_resource':sr['palette_resource'] if sr else '',
            'graphics_context':sr['graphics_context'] if sr else '',
            'selector_catalog_status':sr['status'] if sr else 'missing_selector_catalog',
            'binding_evidence':'static_event_opcode59_actor_controller',
            'map_binding_scope':'pack_family_context'
        }
        out.append(row)

fields=list(out[0].keys()) if out else []
csv_path=ROOT/'data/npc_display/static_map_actor_selector_crosslink_20260930.csv'
with csv_path.open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)

# Aggregate by map/config.
agg=collections.defaultdict(lambda:{'selectors':set(),'records':[],'pack_id_hex':'','map_label':''})
for r in out:
    key=r['config_id'] or ('family_'+r['family_hex'])
    a=agg[key]
    a['pack_id_hex']=r['pack_id_hex'];a['map_label']=r['map_label']
    a['selectors'].add(r['selector_hex'])
    a['records'].append({
        'record_id':r['record_id'],'selector_hex':r['selector_hex'],
        'field_0659_seed':r['field_0659_seed'],'field_0699_seed':r['field_0699_seed'],
        'field_06D9_seed':r['field_06D9_seed'],'field_0719_seed':r['field_0719_seed'],
        'controller_pointer':r['controller_pointer']
    })
by_map={k:{'pack_id_hex':v['pack_id_hex'],'map_label':v['map_label'],
           'selectors':sorted(v['selectors']),'records':v['records']} for k,v in sorted(agg.items())}
json_path=ROOT/'data/npc_display/static_map_actor_selector_by_map_20260930.json'
json_path.write_text(json.dumps(by_map,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

summary={
    'event_records_scanned':len(event_rows),
    'opcode59_actor_records':len({(r['family_hex'],r['record_id']) for r in out}),
    'crosslink_rows_with_map_context':len(out),
    'unique_selectors':len({r['selector_hex'] for r in out}),
    'unique_families':len({r['family_hex'] for r in out}),
    'unique_map_configs':len({r['config_id'] for r in out if r['config_id']}),
    'selectors_missing_static_catalog':sorted({r['selector_hex'] for r in out if r['selector_catalog_status']=='missing_selector_catalog'}),
    'unmapped':unmapped
}
(ROOT/'data/npc_display/static_map_actor_selector_crosslink_summary_20260930.json').write_text(
    json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
print('pack50 rows:')
for r in out:
    if r['family_hex'].upper()=='0X50':
        print(r['config_id'],r['record_id'],r['selector_hex'],r['field_0659_seed'],r['field_0699_seed'],r['field_06D9_seed'],r['field_0719_seed'])
