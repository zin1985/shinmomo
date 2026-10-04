import csv
p=r'C:\Users\zin\Documents\GitHub\shinmomo\data\npc_display\shinmomo_B2C1_animation_state_scripts_20260425.csv'
for r in csv.DictReader(open(p,encoding='utf-8-sig')):
 if int(r['group'])==2 and 216<=int(r['state_no_1_based'])<=219:
  print(r)
