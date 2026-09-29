import json,glob
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
CAP=Path(r'C:\Users\zin\AppData\Local\shinmomo-lab\captures')
ROM=Path(r'C:\Users\zin\Downloads\Shin Momotarou Densetsu (J)\Shin Momotarou Densetsu (J)_original.smc').read_bytes()
CG=json.load(open(CAP/'mem_1790688739943-d9706a30.json'));cg=bytes(CG['bytes'])
v=bytearray(65536);mt={}
for f in CAP.glob('mem_*.json'):
 try:
  j=json.load(open(f))
  if j.get('domain')=='VRAM' and isinstance(j.get('start'),int) and j.get('length')==4096:
   s=j['start'];m=f.stat().st_mtime
   if 0<=s<65536 and m>mt.get(s,0):v[s:s+4096]=bytes(j['bytes']);mt[s]=m
 except:pass
bases=[0x5183A,0x5374F,0x10000,0x119D3,0x12BD3,0x13E68,0x162CB,0x5462C,0x250B1,0x25EF7,0x20000,0x21C10,0x30C01,0x33830,0x5086F,0x51A08]
def rgb(i):
 w=cg[i*2]|cg[i*2+1]<<8;return ((w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31,255)
def dec(addr):
 a=v[addr:addr+32];z=[[0]*8 for _ in range(8)]
 for y in range(8):
  for x in range(8):
   q=7-x;z[y][x]=((a[y*2]>>q)&1)|(((a[y*2+1]>>q)&1)<<1)|(((a[y*2+16]>>q)&1)<<2)|(((a[y*2+17]>>q)&1)<<3)
 return z
def pieces(g,fr):
 base=bases[g];ptr=int.from_bytes(ROM[base+(fr-1)*2:base+(fr-1)*2+2],'little');off=(base&~0xffff)+ptr;n=ROM[off]
 return [tuple(ROM[off+1+i*4:off+5+i*4]) for i in range(n)]
def render(g,fr,tileoff,palbase,group_raw):
 ps=pieces(g,fr); entries=[]
 for fl,xb,yb,tile in ps:
  sx=xb-256 if fl&0x10 else xb; sy=yb-256 if fl&0x20 else yb; ti=(tile+tileoff)&0x1ff
  pal=(((fl&6)>>1)+palbase)&7;attr=(fl&0xC1)|(pal<<1)|(group_raw&0x30);big=1 if fl&8 else 0
  entries.append((sx,sy,ti,attr,big,pal))
 x0=min(x for x,y,t,a,b,p in entries);y0=min(y for x,y,t,a,b,p in entries);x1=max(x+(16 if b else 8) for x,y,t,a,b,p in entries);y1=max(y+(16 if b else 8) for x,y,t,a,b,p in entries)
 im=Image.new('RGBA',(x1-x0,y1-y0),(0,0,0,0))
 for x,y,ti,attr,big,pal in entries:
  sz=16 if big else 8
  for ty in range(sz//8):
   for tx in range(sz//8):
    t=(ti+tx+ty*16)&255;z=dec(0xC000+t*32+(0x2000 if attr&1 else 0))
    for py in range(8):
     for px in range(8):
      ci=z[py][px]
      if not ci:continue
      dx=tx*8+px;dy=ty*8+py
      if attr&0x40:dx=sz-1-dx
      if attr&0x80:dy=sz-1-dy
      im.putpixel((x-x0+dx,y-y0+dy),rgb(128+pal*16+ci))
 return im
families=[
 ('village_group3_slot17_frames9_16',3,range(9,17),32,0,0x23),
 ('village_group3_slot15_frames33_40',3,range(33,41),8,0,0x23)
]
outdir=ROOT/'graphics/runtime_sprite_dynamic'
for name,g,frames,off,palbase,gr in families:
 M=Image.new('RGBA',(8*96,128),(0,0,0,255));dr=ImageDraw.Draw(M)
 for i,fr in enumerate(frames):
  im=render(g,fr,off,palbase,gr);im=im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST)
  M.alpha_composite(im,(i*96+(96-im.width)//2,20));dr.text((i*96+4,4),f'F{fr}',fill='white')
 p=outdir/(name+'.png');M.save(p);print(p)
