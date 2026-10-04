import json,os
p=r'C:\Users\zin\AppData\Local\shinmomo-lab\captures\mem_1790689683798-b4acf4a1.json'
j=json.load(open(p));b=j['bytes'];st=j['start'];r=lambda a:b[a-st]
def s12(v): return v-4096 if v>=2048 else v
chain=[];seen=set();x=r(0x0A61)
while x not in (0,255) and x not in seen and len(chain)<64:
 seen.add(x);chain.append(x);x=r(0x0A61+x)
print('frame',j['frame'],'chain',chain)
for sl in chain:
 fr=r(0x0AE5+sl)
 if not fr: continue
 gr=r(0x0B25+sl);raw=(r(0x0DE5+sl)<<8)|r(0x0DA5+sl);raw=raw-65536 if raw&0x8000 else raw;off=raw//16
 xx=s12(r(0x0BA5+sl)|(r(0x0BE5+sl)<<8));yy=s12(r(0x0C65+sl)|(r(0x0CA5+sl)<<8))
 if -32<=xx<288 and -32<=yy<256:
  print('slot',sl,'group',gr&15,'raw',hex(gr),'frame',fr,'off',off,'xy',xx,yy,'pal',r(0x0D25+sl))
