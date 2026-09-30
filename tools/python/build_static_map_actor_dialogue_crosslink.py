#!/usr/bin/env python3
from pathlib import Path
import csv,json,collections,re

ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')

actor_rows=list(csv.DictReader(open(
    ROOT/'data/npc_display/static_map_actor_selector_crosslink_20260930.csv',
    encoding='utf-8-sig'
)))
source_rows=list(csv.DictReader(open(
    ROOT/'data/events/event_source_crosslink.csv',
    encoding='utf-8-sig'
)))
hist_rows=list(csv.DictReader(open(
    ROOT/'data/dialogue/historical_decode_crosswalk.csv',
    encoding='utf-8-sig'
)))

sources_by_record=collections.defaultdict(list)
for r in source_rows:
    sources_by_record[r['record_id']].append(r)

hist_by_source=collections.defaultdict(list)
for r in hist_rows:
    hist_by_source[r['selected_source_cpu']].append(r)

# Load each canonical data/csv historical decode file once.
decode_file_cache={}
def load_decode_file(rel):
    if rel in decode_file_cache:
        return decode_file_cache[rel]
    p=ROOT/rel
    if not p.exists():
        decode_file_cache[rel]=[]
        return []
    try:
        rows=list(csv.DictReader(open(p,encoding='utf-8-sig')))
    except Exception:
        rows=[]
    decode_file_cache[rel]=rows
    return rows

def text_for_hist_row(hr):
    rel=hr.get('historical_file','')
    # Prefer canonical data/csv copies, not archived duplicates.
    if not rel.startswith('data/csv/'):
        return ''
    rows=load_decode_file(rel)
    seg=hr.get('historical_seg','')
    source=hr.get('selected_source_cpu','')
    bank,addr=(source.split(':')+[None,None])[:2] if ':' in source else ('','')
    for r in rows:
        if seg and r.get('seg')!=seg:
            continue
        if bank and r.get('start_bank','').upper()!=bank.upper():
            continue
        if addr and r.get('start_addr','').upper()!=addr.upper():
            continue
        return r.get('text','') or ''
    # fall back to documented line number if the older file lacks structured state columns
    try:
        line_no=int(hr.get('historical_row','0'))
        idx=line_no-2
        if 0 <= idx < len(rows):
            return rows[idx].get('text','') or ''
    except Exception:
        pass
    return ''

def clean_excerpt(text,limit=180):
    t=(text or '').replace('\r',' ').replace('\n',' ')
    t=re.sub(r'<00>','',t)
    t=re.sub(r'\s+',' ',t).strip()
    if len(t)>limit:
        t=t[:limit-1]+'…'
    return t

out=[]
for a in actor_rows:
    srcs=sources_by_record.get(a['record_id'],[])
    decoded=[]
    source_addrs=[]
    evidence=[]
    for s in srcs:
        cpu=s['selected_source_cpu']
        if cpu:
            source_addrs.append(cpu)
        hs=hist_by_source.get(cpu,[])
        best_text=''
        for hr in hs:
            t=text_for_hist_row(hr)
            if t:
                best_text=t
                evidence.append(hr.get('historical_evidence_class',''))
                break
        if best_text:
            decoded.append((cpu,best_text))
    has_source=bool(source_addrs)
    has_decoded=bool(decoded)
    if has_decoded:
        role='dialogue_actor_candidate'
    elif has_source:
        role='source_linked_no_decoded_text'
    else:
        role='no_source_link'
    row=dict(a)
    row.update({
        'dialogue_source_count':len(set(source_addrs)),
        'decoded_dialogue_source_count':len({cpu for cpu,_ in decoded}),
        'dialogue_sources':'|'.join(dict.fromkeys(source_addrs)),
        'dialogue_excerpt':' || '.join(clean_excerpt(t) for _,t in decoded[:2]),
        'dialogue_role_evidence':role,
        'dialogue_evidence_classes':'|'.join(sorted({e for e in evidence if e})),
    })
    out.append(row)

csv_path=ROOT/'data/npc_display/static_map_actor_dialogue_crosslink_20260930.csv'
with csv_path.open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=list(out[0].keys()))
    w.writeheader();w.writerows(out)

agg=collections.defaultdict(lambda:{
    'rows':0,'dialogue_rows':0,'source_rows':0,'maps':set(),'families':set(),
    'records':set(),'dialogue_examples':[]
})
for r in out:
    s=r['selector_hex'];x=agg[s]
    x['rows']+=1;x['records'].add(r['record_id']);x['families'].add(r['family_hex'])
    if r['config_id']:x['maps'].add(r['config_id'])
    if int(r['dialogue_source_count']):x['source_rows']+=1
    if int(r['decoded_dialogue_source_count']):
        x['dialogue_rows']+=1
        if r['dialogue_excerpt'] and len(x['dialogue_examples'])<3:
            x['dialogue_examples'].append(r['dialogue_excerpt'])

summary={}
for s,x in sorted(agg.items()):
    summary[s]={
        'map_config_count':len(x['maps']),
        'family_count':len(x['families']),
        'event_record_count':len(x['records']),
        'crosslink_rows':x['rows'],
        'source_linked_rows':x['source_rows'],
        'decoded_dialogue_rows':x['dialogue_rows'],
        'dialogue_ratio':round(x['dialogue_rows']/x['rows'],3) if x['rows'] else 0,
        'role_evidence':(
            'dialogue_actor_candidate' if x['dialogue_rows'] else
            'source_linked_no_decoded_text' if x['source_rows'] else
            'no_source_link'
        ),
        'dialogue_examples':x['dialogue_examples']
    }

sum_path=ROOT/'data/npc_display/static_map_actor_dialogue_summary_20260930.json'
sum_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

counts=collections.Counter(r['dialogue_role_evidence'] for r in out)
print('rows',len(out),'selectors',len(summary),'role_counts',dict(counts))
print('selectors with decoded dialogue',sum(1 for x in summary.values() if x['decoded_dialogue_rows']))
print('top dialogue selectors')
for s,x in sorted(summary.items(),key=lambda kv:(-kv[1]['decoded_dialogue_rows'],-kv[1]['event_record_count']))[:20]:
    if x['decoded_dialogue_rows']:
        print(s,x['decoded_dialogue_rows'],'/',x['crosslink_rows'],'maps',x['map_config_count'])
