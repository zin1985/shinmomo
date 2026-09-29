import csv,collections
p=r'C:\Users\zin\Documents\GitHub\shinmomo\data\npc_display\shinmomo_B2C1_animation_state_scripts_20260425.csv'
rows=[r for r in csv.DictReader(open(p,encoding='utf-8-sig')) if int(r['group'])==2]
seqs=collections.defaultdict(list)
for r in rows: seqs[(r['frame_sequence_dec'],r['duration_sequence_dec'])].append(int(r['state_no_1_based']))
print('states',len(rows),'unique_sequences',len(seqs))
for r in rows[:60]:
 print(r['state_no_1_based'],r['frame_sequence_dec'],'dur',r['duration_sequence_dec'])
print('--- longest unique ---')
u=sorted(seqs.items(),key=lambda kv:len(kv[0][0].split(',')),reverse=True)
for (seq,dur),states in u[:25]: print('states',states,'frames',seq,'dur',dur)
