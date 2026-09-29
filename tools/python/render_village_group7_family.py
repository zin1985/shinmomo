from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
src=(ROOT/'tools/python/render_village_group3_families.py').read_text(encoding='utf8')
prefix=src.split("families=[")[0];ns={};exec(prefix,ns);render=ns['render']
sets=[('village_group7_slot22_frames15_19',[15,16,17,18,19],136,0,0x27),('village_group7_frames51_58',[51,52,53,54,55,56,57,58],136,0,0x27)]
outdir=ROOT/'graphics/runtime_sprite_dynamic'
for name,frames,off,pal,gr in sets:
 M=Image.new('RGBA',(len(frames)*96,128),(0,0,0,255));dr=ImageDraw.Draw(M)
 for i,fr in enumerate(frames):
  im=render(7,fr,off,pal,gr);im=im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST)
  M.alpha_composite(im,(i*96+(96-im.width)//2,20));dr.text((i*96+4,4),f'F{fr}',fill='white')
 p=outdir/(name+'.png');M.save(p);print(p)
