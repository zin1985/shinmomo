import csv,collections
p=r'C:\Users\zin\Documents\GitHub\shinmomo\data\npc_display\group2_four_direction_family_candidates_20260929.csv'
rows=list(csv.DictReader(open(p,encoding='utf8')))
by=collections.defaultdict(list)
for r in rows:
    key=(r['frames'],r['durations'])
    by[key].append(int(r['state_start']))
items=sorted(by.items(),key=lambda kv:(-len(kv[1]),kv[1][0]))
print('raw windows',len(rows),'unique frame quartets',len(items))
for i,((frames,dur),starts) in enumerate(items[:40],1):
    print(i,'occ',len(starts),'starts',starts,'frames',frames,'dur',dur)
