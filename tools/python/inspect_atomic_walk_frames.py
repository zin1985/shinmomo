import json,glob,os
files=sorted(glob.glob(r'C:\Users\zin\AppData\Local\shinmomo-lab\captures\atomic_1790686*.json'))[-20:]
for f in files:
 j=json.load(open(f));
 if j.get('buttons')!='Right' or j.get('start')!=0x0A00: continue
 s=j['snapshots'][-1]; b=s['bytes']; st=j['start']
 r=lambda a:b[a-st]
 print(os.path.basename(f),s['frame'],'slot2',{'g':r(0x0B25+2)&15,'fr':r(0x0AE5+2),'x':r(0x0BA5+2),'y':r(0x0C65+2)},'slot3',{'g':r(0x0B25+3)&15,'fr':r(0x0AE5+3),'x':r(0x0BA5+3),'y':r(0x0C65+3)})
