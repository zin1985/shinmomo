import csv,re
p=r'C:\Users\zin\Documents\GitHub\shinmomo\data\npc_display\shinmomo_B2C1_animation_state_scripts_20260425.csv'
rows=list(csv.DictReader(open(p,encoding='utf-8-sig')))
targets=set(range(1,9))|set(range(31,36))
for r in rows:
 if int(r['group'])!=2: continue
 seq=[int(x) for x in re.findall(r'\d+',r['frame_sequence_dec'] or '')]
 hit=targets.intersection(seq)
 if hit: print('state',r['state_no_1_based'],'frames',r['frame_sequence_dec'],'dur',r['duration_sequence_dec'],'hit',sorted(hit),'ptr',r['script_pointer'])
