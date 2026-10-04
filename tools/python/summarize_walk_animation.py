import json,glob,os,collections
xs=[]
for f in glob.glob(r'C:\Users\zin\AppData\Local\shinmomo-lab\captures\atomic_*.json'):
 try:
  j=json.load(open(f))
  if j.get('start')==0x0A00 and j.get('buttons') in ('Right','Left','Up','Down') and j.get('input_frames')==1:
   s=j['snapshots'][-1];b=s['bytes'];st=j['start'];r=lambda a:b[a-st]
   xs.append((os.path.getmtime(f),j['buttons'],s['frame'],r(0x0AE5+2),r(0x0AE5+3),r(0x0BA5+2),r(0x0C65+2),r(0x0BA5+3),r(0x0C65+3),os.path.basename(f)))
 except:pass
xs=sorted(xs)[-40:]
for d in ('Right','Left','Up','Down'):
 a=[x for x in xs if x[1]==d][-8:]
 print(d,'slot2_frames',[x[3] for x in a],'slot3_frames',[x[4] for x in a])
 print(' positions2',[(x[5],x[6]) for x in a])
 print(' positions3',[(x[7],x[8]) for x in a])
