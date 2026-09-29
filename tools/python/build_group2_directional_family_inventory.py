import csv,json
from pathlib import Path
ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
states=[r for r in csv.DictReader(open(ROOT/'data/npc_display/shinmomo_B2C1_animation_state_scripts_20260425.csv',encoding='utf-8-sig')) if int(r['group'])==2]
frames={int(r['frame']):r for r in csv.DictReader(open(ROOT/'data/npc_display/group2_frame_catalog_20260929.csv',encoding='utf8')) if r['valid']=='True'}
families=[
(1,4,[[1,2],[3,4],[5,6],[7,8]],32,'momotaro_normal_walk'),
(5,8,[[9,10],[11,12],[13,14],[15,16]],32,'alternate_pose_family'),
(14,17,[[31,32],[22,33],[6,5],[34,35]],32,'ginji_normal_walk_template'),
(18,21,[[36,37],[38,39],[14,13],[40,41]],32,'shared_directional_family_b'),
(70,73,[[78,79],[80,81],[82,83],[84,85]],32,'candidate_family_78_85'),
(74,77,[[86,87],[88,89],[90,91],[92,93]],32,'candidate_family_86_93'),
(88,91,[[94,95],[96,97],[98,99],[100,101]],32,'candidate_family_94_101'),
(92,95,[[102,103],[104,105],[106,107],[108,109]],32,'candidate_family_102_109'),
(97,100,[[110,111],[112,113],[114,115],[116,117]],32,'candidate_family_110_117'),
(101,104,[[118,119],[120,121],[122,123],[124,125]],32,'candidate_family_118_125'),
(118,121,[[132,133],[134,135],[136,137],[138,139]],48,'candidate_family_132_139'),
(122,125,[[140,141],[142,143],[144,145],[146,147]],48,'candidate_family_140_147'),
(207,210,[[221,222],[223,224],[225,226],[227,228]],32,'candidate_family_221_228'),
(211,214,[[229,230],[231,232],[233,234],[235,236]],32,'candidate_family_229_236'),
(216,219,[[237,238],[239,240],[241,242],[243,244]],64,'village_npc_walk_runtime_bound_237_244')
]
rows=[]
for ss,se,pairs,dur,label in families:
 flat=[x for p in pairs for x in p]
 pcs=[frames.get(x,{}).get('piece_count','?') for x in flat]
 bbox=[frames.get(x,{}).get('bbox','') for x in flat]
 rows.append({'state_start':ss,'state_end':se,'label':label,'duration_each':dur,'direction_pairs':' | '.join('/'.join(map(str,p)) for p in pairs),'piece_counts':','.join(pcs),'bboxes':' | '.join(bbox)})
out=ROOT/'data/npc_display/group2_directional_family_inventory_20260929.csv'
with out.open('w',newline='',encoding='utf8') as f:
 w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
print('\n'.join(str(r) for r in rows))
