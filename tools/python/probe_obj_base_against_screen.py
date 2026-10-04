import json
from pathlib import Path
from PIL import Image
cap=Path(r'C:\Users\zin\AppData\Local\shinmomo-lab\captures')
repo=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
def load(name): return json.load(open(cap/name))
o=bytes(load('mem_1790685049129-6ef7516c.json')['bytes'])
cg=bytes(load('mem_1790685056056-c2803d44.json')['bytes'])
files=['mem_1790685076915-ac0d34f9.json']
# select VRAM captures by newest file for each numeric start
import glob,os
v=bytearray(65536)
for f in glob.glob(str(cap/'mem_*.json')):
 try:
  j=json.load(open(f))
  if j.get('domain')=='VRAM' and isinstance(j.get('start'),int) and j['length']==4096:
   s=j['start']
   if 0<=s<65536:
    # newest wins
    if os.path.getmtime(f)>=globals().get('mt'+str(s),0): v[s:s+4096]=bytes(j['bytes']);globals()['mt'+str(s)]=os.path.getmtime(f)
 except:pass
def rgb(i):
 w=cg[2*i]|cg[2*i+1]<<8
 return ((w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31,255)
def dec(addr):
 a=v[addr:addr+32]; z=[[0]*8 for _ in range(8)]
 for y in range(8):
  for x in range(8):
   b=7-x;z[y][x]=((a[y*2]>>b)&1)|(((a[y*2+1]>>b)&1)<<1)|(((a[y*2+16]>>b)&1)<<2)|(((a[y*2+17]>>b)&1)<<3)
 return z
# test all plausible OBSEL base unit interpretations and name selection conventions; render exact 3 mirror entries as 8x8 pieces
for base in [0x3000,0x6000,0xC000]:
 im=Image.new('RGBA',(32,32),(0,0,0,0))
 for i in range(3):
  x,y,t,a=o[i*4:i*4+4]; pal=(a>>1)&7; px=dec(base+t*32)
  for yy in range(8):
   for xx in range(8):
    ci=px[yy][xx]
    if ci: im.putpixel((x-104+xx,y-100+yy),rgb(128+pal*16+ci))
 im.resize((256,256),Image.Resampling.NEAREST).save(repo/f'graphics/runtime_sprite_dynamic/base_probe_{base:04X}.png')
 print(hex(base),[rgb(128+16+c) for c in range(1,16)])
