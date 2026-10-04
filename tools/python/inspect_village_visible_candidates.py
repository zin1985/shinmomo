import json,glob,os
def s12(v): return v-4096 if v>=2048 else v
fs=sorted(glob.glob(r'C:\Users\zin\AppData\Local\shinmomo-lab\captures\atomic_17906886*.json'))[-6:]
for f in fs:
 j=json.load(open(f));s=j['snapshots'][-1];b=s['bytes'];st=j['start'];r=lambda a:b[a-st]
 vals=[]
 for sl in range(2,27):
  fr=r(0x0AE5+sl)
  if not fr: continue
  gr=r(0x0B25+sl)&15
  to=((r(0x0DE5+sl)<<8)|r(0x0DA5+sl))
  if to&0x8000: to-=0x10000
  to//=16
  x=s12(r(0x0BA5+sl)|(r(0x0BE5+sl)<<8));y=s12(r(0x0C65+sl)|(r(0x0CA5+sl)<<8))
  if -64<=x<320 and -64<=y<288: vals.append((sl,gr,fr,to,x,y))
 print(os.path.basename(f),s['frame'],vals)
