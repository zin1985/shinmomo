import json,glob,os
from pathlib import Path
from PIL import Image
ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
CAP=Path(r'C:\Users\zin\AppData\Local\shinmomo-lab\captures')
ROM=Path(r'C:\Users\zin\Downloads\Shin Momotarou Densetsu (J)\Shin Momotarou Densetsu (J)_original.smc').read_bytes()
OBJ=json.load(open(CAP/'mem_1790688923128-c4427367.json'))
CG=json.load(open(CAP/'mem_1790688739943-d9706a30.json'))
b=OBJ['bytes'];st=OBJ['start'];r=lambda a:b[a-st];cg=bytes(CG['bytes'])
v=bytearray(65536); mt={}
for f in CAP.glob('mem_*.json'):
 try:
  j=json.load(open(f))
  if j.get('domain')=='VRAM' and isinstance(j.get('start'),int) and j.get('length')==4096:
   s=j['start'];m=f.stat().st_mtime
   if 0<=s<65536 and m>mt.get(s,0):v[s:s+4096]=bytes(j['bytes']);mt[s]=m
 except:pass
def rgb(i):
 w=cg[i*2]|cg[i*2+1]<<8
 return ((w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31,255)
def dec(addr):
 a=v[addr:addr+32];z=[[0]*8 for _ in range(8)]
 for y in range(8):
  for x in range(8):
   q=7-x;z[y][x]=((a[y*2]>>q)&1)|(((a[y*2+1]>>q)&1)<<1)|(((a[y*2+16]>>q)&1)<<2)|(((a[y*2+17]>>q)&1)<<3)
 return z
bases=[0x5183A,0x5374F,0x10000,0x119D3,0x12BD3,0x13E68,0x162CB,0x5462C,0x250B1,0x25EF7,0x20000,0x21C10,0x30C01,0x33830,0x5086F,0x51A08]
def pieces(g,fr):
 base=bases[g];t=base+(fr-1)*2;ptr=int.from_bytes(ROM[t:t+2],'little');off=(base&~0xffff)+ptr;n=ROM[off]
 return ptr,[tuple(ROM[off+1+i*4:off+5+i*4]) for i in range(n)]
def signed16(v):return v-65536 if v&0x8000 else v
def render_slot(sl):
 gr=r(0x0B25+sl);g=gr&15;fr=r(0x0AE5+sl);x=r(0x0BA5+sl)|(r(0x0BE5+sl)<<8);y=r(0x0C65+sl)|(r(0x0CA5+sl)<<8)
 if x>=2048:x-=4096
 if y>=2048:y-=4096
 raw=(r(0x0DE5+sl)<<8)|r(0x0DA5+sl);off=signed16(raw)//16;palbase=r(0x0D25+sl);ypiv=r(0x0CE5+sl)
 ptr,ps=pieces(g,fr); out=[]
 for fl,xb,yb,tile in ps:
  sx=xb-256 if fl&0x10 else xb; sy=yb-256 if fl&0x20 else yb
  xx=x+sx;yy=y-ypiv+sy-1;ti=(tile+off)&0x1ff
  pal=(((fl&6)>>1)+palbase)&7
  attr=(fl&0xC1)|(pal<<1)|(gr&0x30);big=1 if fl&8 else 0
  out.append((xx,yy,ti,attr,big,pal,fl))
 if not out:return None
 x0=min(a[0] for a in out);y0=min(a[1] for a in out);x1=max(a[0]+(16 if a[4] else 8) for a in out);y1=max(a[1]+(16 if a[4] else 8) for a in out)
 im=Image.new('RGBA',(x1-x0,y1-y0),(0,0,0,0))
 for xx,yy,ti,attr,big,pal,fl in out:
  sz=16 if big else 8
  for ty in range(sz//8):
   for tx in range(sz//8):
    t=(ti+tx+ty*16)&0xff; addr=0xC000+t*32+(0x2000 if attr&1 else 0);z=dec(addr)
    for py in range(8):
     for px in range(8):
      ci=z[py][px]
      if not ci:continue
      dx=tx*8+px;dy=ty*8+py
      if attr&0x40:dx=sz-1-dx
      if attr&0x80:dy=sz-1-dy
      im.putpixel((xx-x0+dx,yy-y0+dy),rgb(128+pal*16+ci))
 return dict(slot=sl,group=g,group_raw=gr,frame=fr,tile_offset=off,palette_base=palbase,x=x,y=y,ptr=f'{(bases[g]>>16)&255:02X}:{ptr:04X}',pieces=out,image=im)
for sl in [13,22,23,15,17,18]:
 o=render_slot(sl)
 if not o:continue
 print({k:v for k,v in o.items() if k!='image' and k!='pieces'},'pieces',o['pieces'])
 p=ROOT/'graphics/runtime_sprite_dynamic'/f'village_slot{sl}_g{o["group"]}_f{o["frame"]:03d}_off{o["tile_offset"]:+d}.png'
 o['image'].resize((o['image'].width*10,o['image'].height*10),Image.Resampling.NEAREST).save(p)
 print(p)
