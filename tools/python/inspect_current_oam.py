import json,glob,os
cap=r'C:\Users\zin\AppData\Local\shinmomo-lab\captures'
def by_start(start,domain='WRAM'):
 xs=[]
 for f in glob.glob(cap+r'\\mem_*.json'):
  try:
   j=json.load(open(f)); v=j.get('start')
   v=v if isinstance(v,int) else int(str(v).replace('0x',''),16)
   if j.get('domain')==domain and v==start: xs.append((os.path.getmtime(f),j))
  except: pass
 return max(xs)[1]
o=bytes(by_start(0xEE9)['bytes']); ob=by_start(0x3A6)['bytes'][0]; print('OBSEL',hex(ob))
for i in range(128):
 x,y,t,a=o[i*4:i*4+4]
 if y<224: print(i,x,y,hex(t),hex(a),'pal',(a>>1)&7,'pri',(a>>4)&3,'flip',a>>6)
