from pathlib import Path
from PIL import Image,ImageDraw
import csv
root=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
cap=Path(r'C:\Users\zin\AppData\Local\shinmomo-lab\map_captures\1790661748186-410b0c3f_entity_probe')
vram=(cap/'vram.bin').read_bytes(); cg=(cap/'cgram.bin').read_bytes()
rows=list(csv.DictReader(open(root/'data/npc_display/shinmomo_B294_sprite_frame_piece_sample_20260425.csv',encoding='utf-8-sig')))
def tile(data):
 out=[[0]*8 for _ in range(8)]
 for y in range(8):
  p0,p1,p2,p3=data[y*2],data[y*2+1],data[y*2+16],data[y*2+17]
  for x in range(8):
   b=7-x;out[y][x]=((p0>>b)&1)|(((p1>>b)&1)<<1)|(((p2>>b)&1)<<2)|(((p3>>b)&1)<<3)
 return out
def col(i):
 w=cg[i*2]|(cg[i*2+1]<<8);return ((w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31,255)
out=root/'graphics/sprite_reconstruction_probe';out.mkdir(parents=True,exist_ok=True)
for frame in [1,4,5,6,7,8]:
 rs=[r for r in rows if r['group']=='0' and int(r['frame_index_1based'])==frame]
 if not rs:continue
 for base in [0,0x2000,0x4000,0x6000,0x8000,0xA000,0xC000]:
  xs=[int(r['x_offset_signed']) for r in rs];ys=[int(r['y_offset_signed']) for r in rs]
  minx,maxx=min(xs),max(xs)+8;miny,maxy=min(ys),max(ys)+8
  for pal in range(8):
   im=Image.new('RGBA',(maxx-minx,maxy-miny),(0,0,0,0))
   for r in rs:
    ti=int(r['tile_hex'],16); addr=(base+ti*32)&0xffff
    if addr+32>len(vram):continue
    px=tile(vram[addr:addr+32]); ox=int(r['x_offset_signed'])-minx;oy=int(r['y_offset_signed'])-miny
    for y in range(8):
     for x in range(8):
      ci=px[y][x]
      if ci: im.putpixel((ox+x,oy+y),col(128+pal*16+ci))
   im.resize((im.width*4,im.height*4),resample=Image.Resampling.NEAREST).save(out/f'g00_f{frame:02d}_b{base:04X}_p{pal}.png')
# montage selected all base/pal frame5
imgs=[];labels=[]
for base in [0,0x2000,0x4000,0x6000,0x8000,0xA000,0xC000]:
 for pal in range(8):
  p=out/f'g00_f05_b{base:04X}_p{pal}.png'; im=Image.open(p); imgs.append(im);labels.append(f'{base:04X} p{pal}')
w=160;h=160;M=Image.new('RGB',(8*w,7*h),'white');dr=ImageDraw.Draw(M)
for i,im in enumerate(imgs):
 x=(i%8)*w;y=(i//8)*h;M.paste(im,(x+8,y+20),im);dr.text((x+5,y+3),labels[i],fill='black')
M.save(out/'montage_group0_frame5.png')
print(out/'montage_group0_frame5.png')