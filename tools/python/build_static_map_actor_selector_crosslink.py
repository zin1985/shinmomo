#!/usr/bin/env python3
from pathlib import Path
import csv,json,collections

ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
ROM=Path(r'C:\Users\zin\Downloads\Shin Momotarou Densetsu (J)\Shin Momotarou Densetsu (J)_original.smc').read_bytes()

def parse_addr(s):
    bank,addr=s.split(':')
    bank=int(bank,16); addr=int(addr,16)
    return ((bank & 0x3F)<<16) | addr

selector_rows={}
with (ROOT/'data/npc_display/static_character_selector_catalog_20260930.csv').open(encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        selector_rows[int(r['selector'])]=r

with (ROOT/'data/maps/context/map_dialogue_pack_crosslink.csv').open(encoding='utf-8-sig') as f:
    map_rows=list(csv.DictReader(f))
maps_by_family=collections.defaultdict(list)
for r in map_rows:
    maps_by_family[r['source_family_hex'].upper()].append(r)

with (ROOT/'data/events/event_record_frame_catalog.csv').open(encoding='utf-8-sig') as f:
    event_rows=list(csv.DictReader(f))

out=[]
unmapped=[]
for er in event_rows:
    body_start=er['body_start']
    body_size=int(er['body_size'])
    if not body_start or body_size < 6:
        continue
    off=parse_addr(body_start)
    body=ROM[off:off+body_size]

    # Proven exact cases:
    # 1) body itself begins with opcode 0x59.
    # 2) body has an arbitrary validated prefix but its final six bytes are
    #    exactly one complete 0x59 actor/controller placement command.
    # The tail case is fail-closed at the framed record boundary and is kept
    # in a separate evidence class from the direct head case.
    command_offset=None
    evidence=None
    if body[0] == 0x59:
        command_offset=0
        evidence='static_event_head_opcode59_actor_controller'
    elif body[-6] == 0x59:
        command_offset=len(body)-6
        evidence='static_event_tail_opcode59_actor_controller'
    else:
        continue

    cmd=body[command_offset:command_offset+6]
    sel=cmd[1]
    sr=selector_rows.get(sel)
    if sr is None:
        unmapped.append({
            'record_id':er['record_id'],
            'reason':'opcode59_selector_missing_static_catalog',
            'selector_hex':f'0x{sel:02X}',
            'command_offset':command_offset,
            'body_hex':body.hex(' ')
        })
        continue

    fam=er['family_hex'].upper()
    configs=maps_by_family.get(fam,[]) or [None]
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
            'actor_command_offset':command_offset,
            'selector_hex':f'0x{sel:02X}',
            'selector_dec':sel,
            'field_0659_seed':cmd[2],
            'field_0699_seed':cmd[3],
            'field_06D9_seed':cmd[4],
            'field_0719_seed':cmd[5],
            'actor_command_hex':cmd.hex(' '),
            'body_hex':body.hex(' '),
            'chr_resource':sr['chr_resource'],
            'chr_window_index':sr['chr_window_index'],
            'animation_base_state':sr['base_state'],
            'sprite_group':sr['sprite_group'],
            'palette_resource':sr['palette_resource'],
            'graphics_context':sr['graphics_context'],
            'selector_catalog_status':sr['status'],
            'binding_evidence':evidence,
            'map_binding_scope':'pack_family_context'
        }
        out.append(row)

fields=list(out[0].keys()) if out else []
csv_path=ROOT/'data/npc_display/static_map_actor_selector_crosslink_20260930.csv'
with csv_path.open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(out)

agg=collections.defaultdict(lambda:{'selectors':set(),'records':[],'pack_id_hex':'','map_label':''})
for r in out:
    key=r['config_id'] or ('family_'+r['family_hex'])
    a=agg[key]
    a['pack_id_hex']=r['pack_id_hex'];a['map_label']=r['map_label']
    a['selectors'].add(r['selector_hex'])
    a['records'].append({
        'record_id':r['record_id'],'selector_hex':r['selector_hex'],
        'actor_command_offset':r['actor_command_offset'],
        'field_0659_seed':r['field_0659_seed'],'field_0699_seed':r['field_0699_seed'],
        'field_06D9_seed':r['field_06D9_seed'],'field_0719_seed':r['field_0719_seed'],
        'controller_pointer':r['controller_pointer'],
        'binding_evidence':r['binding_evidence']
    })
by_map={k:{'pack_id_hex':v['pack_id_hex'],'map_label':v['map_label'],
           'selectors':sorted(v['selectors']),'records':v['records']} for k,v in sorted(agg.items())}
(ROOT/'data/npc_display/static_map_actor_selector_by_map_20260930.json').write_text(
    json.dumps(by_map,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

record_keys={(r['family_hex'],r['record_id']) for r in out}
evidence_counts=collections.Counter(r['binding_evidence'] for r in out)
summary={
    'event_records_scanned':len(event_rows),
    'opcode59_actor_records':len(record_keys),
    'head_opcode59_records':len({(r['family_hex'],r['record_id']) for r in out if r['binding_evidence'].startswith('static_event_head')}),
    'tail_opcode59_records':len({(r['family_hex'],r['record_id']) for r in out if r['binding_evidence'].startswith('static_event_tail')}),
    'crosslink_rows_with_map_context':len(out),
    'unique_selectors':len({r['selector_hex'] for r in out}),
    'unique_families':len({r['family_hex'] for r in out}),
    'unique_map_configs':len({r['config_id'] for r in out if r['config_id']}),
    'binding_evidence_row_counts':dict(evidence_counts),
    'selectors_missing_static_catalog':sorted({x['selector_hex'] for x in unmapped if 'selector_hex' in x}),
    'unmapped':unmapped
}
(ROOT/'data/npc_display/static_map_actor_selector_crosslink_summary_20260930.json').write_text(
    json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
