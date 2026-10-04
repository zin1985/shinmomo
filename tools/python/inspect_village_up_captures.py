import json,glob,os
fs=sorted(glob.glob(r'C:\Users\zin\AppData\Local\shinmomo-lab\captures\atomic_17906885*.json'))[-6:]
for f in fs:
 j=json.load(open(f)); s=j['snapshots'][-1]; b=s['bytes']; st=j['start']; r=lambda a:b[a-st]
 chain=[];seen=set();x=r(0x0A61)
 while x not in (0,255) and x not in seen and len(chain)<64:
  seen.add(x);chain.append(x);x=r(0x0A61+x)
 obs=[]
 for sl in chain:
  fr=r(0x0AE5+sl); gr=r(0x0B25+sl); to=((r(0x0DE5+sl)<<8)|r(0x0DA5+sl))>>4
  xx=r(0x0BA5+sl)|(r(0x0BE5+sl)<<8); yy=r(0x0C65+sl)|(r(0x0CA5+sl)<<8)
  if fr: obs.append((sl,gr&15,fr,hex(to),xx,yy))
 print(os.path.basename(f),s['frame'],'chain',chain,'visible_nonzero',obs)
