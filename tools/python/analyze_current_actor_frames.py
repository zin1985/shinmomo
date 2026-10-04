import json,glob,os
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
CAP=Path(r'C:\Users\zin\AppData\Local\shinmomo-lab\captures')
ROM=Path(r'C:\Users\zin\Downloads\Shin Momotarou Densetsu (J)\Shin Momotarou Densetsu (J)_original.smc').read_bytes()
OBJ=json.load(open(CAP/'mem_1790685308574-738b8d95.json'))
CG=json.load(open(CAP/'mem_1790685056056-c2803d44.json'))
b=OBJ['bytes']; st=OBJ['start']; r=lambda a:b[a-st]
cg=bytes(CG['bytes'])
# newest current-session VRAM chunk per start
v=bytearray(65536); mt={}
for f in CAP.glob('mem_*.json'):
 try:
  j=json.load(open(f))
  if j.get('domain')=='VRAM' and isinstance(j.get('start'),int) and j.get('length')==4096:
   s=j['start']; m=f.stat().st_mtime
   if 0<=s<65536 and m>mt.get(s,0): v[s:s+4096]=bytes(j['bytes']);mt[s]=m
 except: pass
def rgb(i):
 w=cg[i*2]|cg[i*2+1]<<8
 return ((w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31,255)
def dec(addr):
 a=v[addr:addr+32]; z=[[0]*8 for _ in range(8)]
 for y in range(8):
  for x in range(8):
   q=7-x;z[y][x]=((a[y*2]>>q)&1)|(((a[y*2+1]>>q)&1)<<1)|(((a[y*2+16]>>q)&1)<<2)|(((a[y*2+17]>>q)&1)<<3)
 return z
def group_base(g):
 table=[0x5183A,0x5374F,0x10000,0x119D3,0x12BD3,0x13E68,0x162CB,0x5462C,0x250B1,0x25EF7,0x20000,0x21C10,0x30C01,0x33830,0x5086F,0x51A08]
 return table[g]
def bankbase(g):
 return group_base(g)&~0xFFFF
def frame_pieces(g,frame):
 t=group_base(g)+(frame-1)*2
 ptr=int.from_bytes(ROM[t:t+2],'little'); off=bankbase(g)+ptr; n=ROM[off]
 return ptr,[tuple(ROM[off+1+i*4:off+5+i*4]) for i in range(n)]
def sx(v,neg): return v-256 if neg else v
def obj(slot):
 gr=r(0x0B25+slot);g=gr&15;fr=r(0x0AE5+slot);x=r(0x0BA5+slot)|(r(0x0BE5+slot)<<8);y=r(0x0C65+slot)|(r(0x0CA5+slot)<<8)
 da=r(0x0DA5+slot); palbase=r(0x0D25+slot); ybase=r(0x0CE5+slot)
 off16=((fr<<8)|da)>>4
 if off16&0x800: off16|=0xF000
 ptr,ps=frame_pieces(g,fr); out=[]
 for fl,xb,yb,tile in ps:
  xx=(x+sx(xb,bool(fl&0x10)))&0x1ff
  yy=(y-ybase+sx(yb,bool(fl&0x20)))&0xff
  ti=(tile+off16)&0x1ff
  pal=(((fl&6)>>1)+palbase)*2&0x0e
  attr=(fl&0xC1)|pal|(gr&0x30)
  out.append(dict(flags=fl,x=xx,y=(yy-1)&255,tile=ti&255,tile9=ti,pal=pal>>1,attr=attr,big=1 if fl&8 else 0))
 return dict(slot=slot,group=g,group_raw=gr,frame=fr,frame_ptr=ptr,tile_offset=off16&0xffff,pieces=out)
def render(o):
 ps=o['pieces']; x0=min(p['x'] for p in ps);y0=min(p['y'] for p in ps);x1=max(p['x']+(16 if p['big'] else 8) for p in ps);y1=max(p['y']+(16 if p['big'] else 8) for p in ps)
 im=Image.new('RGBA',(x1-x0,y1-y0),(0,0,0,0))
 for p in ps:
  sz=16 if p['big'] else 8
  for ty in range(sz//8):
   for tx in range(sz//8):
    ti=(p['tile9']+tx+ty*16)&0x1ff
    addr=0xC000+(ti&0xff)*32+(0x2000 if (p['attr']&1) else 0)
    z=dec(addr)
    for yy in range(8):
     for xx in range(8):
      ci=z[yy][xx]
      if not ci: continue
      dx=tx*8+xx;dy=ty*8+yy
      if p['attr']&0x40: dx=sz-1-dx
      if p['attr']&0x80: dy=sz-1-dy
      im.putpixel((p['x']-x0+dx,p['y']-y0+dy),rgb(128+p['pal']*16+ci))
 return im
out=ROOT/'graphics/runtime_sprite_dynamic';out.mkdir(exist_ok=True)
docs=[]
for s in (2,3):
 o=obj(s);docs.append(o);print(json.dumps(o,ensure_ascii=False))
 im=render(o); im.resize((im.width*10,im.height*10),Image.Resampling.NEAREST).save(out/f'current_slot{s}_g{o["group"]}_f{o["frame"]:03d}.png')
# compare exact produced OAM with mirror first entries
print('actual_oam',[(r(0x0EE9+i*4),r(0x0EEA+i*4),r(0x0EEB+i*4),r(0x0EEC+i*4)) for i in range(3)])
(ROOT/'data/entities/current_actor_oam_split_20260929.json').write_text(json.dumps(docs,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
