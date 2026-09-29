import json,glob,os
from pathlib import Path
from PIL import Image
cap=Path(r'C:\Users\zin\AppData\Local\shinmomo-lab\captures')
repo=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
def latest(domain,start=None):
 fs=[]
 for f in cap.glob('mem_*.json'):
  try:
   j=json.load(open(f))
   if j.get('domain')==domain and (start is None or j.get('start')==start): fs.append((f.stat().st_mtime,j))
  except: pass
 return max(fs,key=lambda x:x[0])[1]
oam=bytes(latest('WRAM',0x0EE9)['bytes']); cg=bytes(latest('WRAM',0x21C2)['bytes'])
v=bytearray(65536)
for s in range(0,65536,4096):
 j=latest('VRAM',s);v[s:s+4096]=bytes(j['bytes'])
obsel=latest('WRAM',934)['bytes'][0]
base=(obsel&7)*0x2000
name=((obsel>>3)&3)*0x1000+0x1000
sizepair=[((8,8),(16,16)),((8,8),(32,32)),((8,8),(64,64)),((16,16),(32,32)),((16,16),(64,64)),((32,32),(64,64)),((16,32),(32,64)),((16,32),(32,32))][(obsel>>5)&7]
print('OBSEL',hex(obsel),'base',hex(base),'nameoff',hex(name),'sizes',sizepair)
def rgb(i):
 w=cg[2*i]|cg[2*i+1]<<8;return ((w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31,255)
def tile(addr):
 a=v[addr:addr+32];out=[[0]*8 for _ in range(8)]
 for y in range(8):
  for x in range(8):
   b=7-x;out[y][x]=((a[y*2]>>b)&1)|(((a[y*2+1]>>b)&1)<<1)|(((a[y*2+16]>>b)&1)<<2)|(((a[y*2+17]>>b)&1)<<3)
 return out
sprites=[]
for i in range(128):
 x,y,t,a=oam[i*4:i*4+4];hi=(oam[512+i//4]>>((i%4)*2))&3;x|=(hi&1)<<8;big=(hi>>1)&1
 if y>=224 or x>=256:continue
 pal=(a>>1)&7; h=(a>>6)&1;vf=(a>>7)&1; nb=(a&1)
 addr=base+(name if nb else 0)+t*32
 sprites.append((i,x,y,t,a,big,pal,addr,h,vf))
print('visible',sprites[:40])
out=repo/'graphics/runtime_sprite_dynamic';out.mkdir(parents=True,exist_ok=True)
# render each visible OAM 8x8/16x16 according to size
for i,x,y,t,a,big,pal,addr,hf,vf in sprites:
 w,h=sizepair[1] if big else sizepair[0]; im=Image.new('RGBA',(w,h),(0,0,0,0))
 for ty in range(h//8):
  for tx in range(w//8):
   # SNES OBJ 16-wide tile row addressing
   ti=(t+tx+ty*16)&255; ad=base+(name if (a&1) else 0)+ti*32;px=tile(ad)
   for py in range(8):
    for px0 in range(8):
     ci=px[py][px0]
     if ci: im.putpixel((tx*8+px0,ty*8+py),rgb(128+pal*16+ci))
 if hf: im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
 if vf: im=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
 im.resize((w*4,h*4),Image.Resampling.NEAREST).save(out/f'oam_{i:03d}_x{x}_y{y}_t{t:02X}_a{a:02X}.png')
print(out)
