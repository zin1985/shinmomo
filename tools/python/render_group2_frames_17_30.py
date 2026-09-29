import json,glob,os
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo');CAP=Path(r'C:\Users\zin\AppData\Local\shinmomo-lab\captures')
ROM=Path(r'C:\Users\zin\Downloads\Shin Momotarou Densetsu (J)\Shin Momotarou Densetsu (J)_original.smc').read_bytes()
CG=json.load(open(CAP/'mem_1790685056056-c2803d44.json'));cg=bytes(CG['bytes'])
v=bytearray(65536);mt={}
for f in CAP.glob('mem_*.json'):
 try:
  j=json.load(open(f))
  if j.get('domain')=='VRAM' and isinstance(j.get('start'),int) and j.get('length')==4096:
   s=j['start'];m=f.stat().st_mtime
   if 0<=s<65536 and m>mt.get(s,0):v[s:s+4096]=bytes(j['bytes']);mt[s]=m
 except:pass
def rgb(i):
 w=cg[2*i]|cg[2*i+1]<<8;return ((w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31,255)
def dec(addr):
 a=v[addr:addr+32];z=[[0]*8 for _ in range(8)]
 for y in range(8):
  for x in range(8):
   q=7-x;z[y][x]=((a[y*2]>>q)&1)|(((a[y*2+1]>>q)&1)<<1)|(((a[y*2+16]>>q)&1)<<2)|(((a[y*2+17]>>q)&1)<<3)
 return z
def pieces(fr):
 t=0x10000+(fr-1)*2;ptr=int.from_bytes(ROM[t:t+2],'little');off=0x10000+ptr;n=ROM[off]
 return [tuple(ROM[off+1+i*4:off+5+i*4]) for i in range(n)]
def render(fr):
 ps=pieces(fr); coords=[]
 for fl,xb,yb,ti in ps:
  x=xb-256 if fl&0x10 else xb;y=yb-256 if fl&0x20 else yb;sz=16 if fl&8 else 8;coords.append((fl,x,y,ti,sz))
 x0=min(x for _,x,y,t,s in coords);y0=min(y for _,x,y,t,s in coords);x1=max(x+s for _,x,y,t,s in coords);y1=max(y+s for _,x,y,t,s in coords)
 im=Image.new('RGBA',(x1-x0,y1-y0),(0,0,0,0))
 for fl,x,y,ti,sz in coords:
  pal=(fl&6)>>1
  for ty in range(sz//8):
   for tx in range(sz//8):
    tile=(ti+tx+ty*16)&255; z=dec(0xC000+tile*32+(0x2000 if fl&1 else 0))
    for yy in range(8):
     for xx in range(8):
      ci=z[yy][xx]
      if not ci:continue
      dx=tx*8+xx;dy=ty*8+yy
      if fl&0x40:dx=sz-1-dx
      if fl&0x80:dy=sz-1-dy
      im.putpixel((x-x0+dx,y-y0+dy),rgb(128+pal*16+ci))
 return im
out=ROOT/'graphics/runtime_sprite_dynamic/group2_frames_17_30.png'
M=Image.new('RGBA',(7*96,2*128),(0,0,0,0));dr=ImageDraw.Draw(M)
for i,fr in enumerate(range(17,31)):
 im=render(fr);im=im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST);x=(i%7)*96; y=(i//7)*128; M.alpha_composite(im,(x+(96-im.width)//2,y+20));dr.text((x+4,y+4),f'F{fr}',fill='white')
M.save(out);print(out)
