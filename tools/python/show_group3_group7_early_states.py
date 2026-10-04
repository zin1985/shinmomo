import csv
p=r'C:\Users\zin\Documents\GitHub\shinmomo\data\npc_display\shinmomo_B2C1_animation_state_scripts_20260425.csv'
for g in (3,7):
 print('=== GROUP',g,'===')
 n=0
 for r in csv.DictReader(open(p,encoding='utf-8-sig')):
  if int(r['group'])!=g: continue
  st=int(r['state_no_1_based'])
  if st>32: break
  print(st,r['frame_sequence_dec'],'dur',r['duration_sequence_dec'])
