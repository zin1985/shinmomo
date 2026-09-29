import csv,json,hashlib
from pathlib import Path
ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
ROM=Path(r'C:\Users\zin\Downloads\Shin Momotarou Densetsu (J)\Shin Momotarou Densetsu (J)_original.smc').read_bytes()
group=2;base=0x10000;count=475
rows=[]
for fr in range(1,count+1):
    ptr=int.from_bytes(ROM[base+(fr-1)*2:base+(fr-1)*2+2],'little')
    off=base+ptr
    n=ROM[off]
    valid=(1<=n<=64 and off+1+n*4<=len(ROM))
    if not valid:
        rows.append(dict(frame=fr,ptr=f'C1:{ptr:04X}',piece_count=n,valid=False,bbox='',geometry_sig='',tiles=''))
        continue
    pieces=[]
    xs=[];ys=[]
    for i in range(n):
        fl,x,y,t=ROM[off+1+i*4:off+5+i*4]
        sx=x-256 if fl&0x10 else x
        sy=y-256 if fl&0x20 else y
        size=16 if fl&0x08 else 8
        xs += [sx,sx+size]; ys += [sy,sy+size]
        pieces.append((fl&0xF8,sx,sy,size))
    geom=';'.join(f'{a:02X}:{x}:{y}:{s}' for a,x,y,s in pieces)
    tiles=','.join(f'{ROM[off+4+i*4]:02X}' for i in range(n))
    rows.append(dict(frame=fr,ptr=f'C1:{ptr:04X}',piece_count=n,valid=True,bbox=f'{min(xs)},{min(ys)},{max(xs)},{max(ys)}',geometry_sig=hashlib.sha1(geom.encode()).hexdigest()[:12],tiles=tiles))
out=ROOT/'data/npc_display/group2_frame_catalog_20260929.csv'
with out.open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)

ap=ROOT/'data/npc_display/shinmomo_B2C1_animation_state_scripts_20260425.csv'
states=[r for r in csv.DictReader(open(ap,encoding='utf-8-sig')) if int(r['group'])==2]
parsed=[]
for r in states:
    seq=[int(x) for x in (r['frame_sequence_dec'] or '').split(',') if x.strip().isdigit()]
    dur=[int(x) for x in (r['duration_sequence_dec'] or '').split(',') if x.strip().isdigit()]
    parsed.append((int(r['state_no_1_based']),seq,dur,r['script_pointer']))
families=[]
for i in range(len(parsed)-3):
    q=parsed[i:i+4]
    if [x[0] for x in q] != list(range(q[0][0],q[0][0]+4)): continue
    if all(len(x[1])==2 for x in q) and len({tuple(x[2]) for x in q})==1:
        fam_frames=[x[1] for x in q]
        flat=[y for x in fam_frames for y in x]
        valid_frames=[rows[f-1] for f in flat if 1<=f<=len(rows)]
        families.append({
          'state_start':q[0][0],'state_end':q[-1][0],
          'frames':' | '.join(','.join(map(str,x[1])) for x in q),
          'durations':','.join(map(str,q[0][2])),
          'unique_frames':len(set(flat)),
          'piece_counts':' | '.join(','.join(str(rows[f-1]['piece_count']) for f in x[1] if 1<=f<=len(rows)) for x in q),
          'geometry_sigs':' | '.join(','.join(rows[f-1]['geometry_sig'] for f in x[1] if 1<=f<=len(rows)) for x in q)
        })
fout=ROOT/'data/npc_display/group2_four_direction_family_candidates_20260929.csv'
with fout.open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=families[0].keys());w.writeheader();w.writerows(families)
print('frame rows',len(rows),'valid',sum(r['valid'] for r in rows))
print('4-state/2-frame families',len(families))
for x in families[:40]: print(x['state_start'],x['frames'],x['durations'],x['piece_counts'])
