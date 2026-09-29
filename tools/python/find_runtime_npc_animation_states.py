import csv,re
from collections import defaultdict
p=r'C:\Users\zin\Documents\GitHub\shinmomo\data\npc_display\shinmomo_B2C1_animation_state_scripts_20260425.csv'
obs={3:[35,11],7:[15]}
for g,targets in obs.items():
 rows=[r for r in csv.DictReader(open(p,encoding='utf-8-sig')) if int(r['group'])==g]
 print('GROUP',g,'states',len(rows))
 for t in targets:
  print(' target frame',t)
  for r in rows:
   seq=[int(x) for x in re.findall(r'\d+',r['frame_sequence_dec'] or '')]
   if t in seq:
    print('  state',r['state_no_1_based'],'seq',r['frame_sequence_dec'],'dur',r['duration_sequence_dec'],'ptr',r['script_pointer'])
