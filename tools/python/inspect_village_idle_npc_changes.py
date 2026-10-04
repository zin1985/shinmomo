import json,glob,os
fs=sorted(glob.glob(r'C:\Users\zin\AppData\Local\shinmomo-lab\captures\mem_17906894*.json'))[-5:]
for f in fs:
 j=json.load(open(f));b=j['bytes'];st=j['start'];r=lambda a:b[a-st]
 print(os.path.basename(f),'frame',j['frame'])
 for sl in (22,15,17,13):
  fr=r(0x0AE5+sl);gr=r(0x0B25+sl);raw=(r(0x0DE5+sl)<<8)|r(0x0DA5+sl);raw=raw-65536 if raw&0x8000 else raw;off=raw//16
  x=r(0x0BA5+sl)|(r(0x0BE5+sl)<<8);y=r(0x0C65+sl)|(r(0x0CA5+sl)<<8)
  if x>=2048:x-=4096
  if y>=2048:y-=4096
  print(' ',sl,'g',gr&15,'gr',hex(gr),'f',fr,'off',off,'xy',x,y,'pal',r(0x0D25+sl))
