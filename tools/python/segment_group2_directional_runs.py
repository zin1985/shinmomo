import csv
p=r'C:\Users\zin\Documents\GitHub\shinmomo\data\npc_display\shinmomo_B2C1_animation_state_scripts_20260425.csv'
rows=[r for r in csv.DictReader(open(p,encoding='utf-8-sig')) if int(r['group'])==2]
st=[]
for r in rows:
 seq=[int(x) for x in (r['frame_sequence_dec'] or '').split(',') if x.strip().isdigit()]
 dur=[int(x) for x in (r['duration_sequence_dec'] or '').split(',') if x.strip().isdigit()]
 st.append((int(r['state_no_1_based']),seq,dur))
runs=[];cur=[]
for x in st:
 ok=len(x[1])==2 and len(x[2])==2 and x[2][0]==x[2][1]
 if ok:
  if cur and x[0]!=cur[-1][0]+1:
   if len(cur)>=4:runs.append(cur)
   cur=[]
  cur.append(x)
 else:
  if len(cur)>=4:runs.append(cur)
  cur=[]
if len(cur)>=4:runs.append(cur)
print('runs',len(runs))
for run in runs:
 print('RUN',run[0][0],run[-1][0],'len',len(run),'dur',run[0][2])
 for i in range(0,len(run),4):
  q=run[i:i+4]
  print(' chunk',q[0][0],'-',q[-1][0],['/'.join(map(str,x[1])) for x in q])
