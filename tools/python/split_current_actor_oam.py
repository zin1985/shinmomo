from PIL import Image
from pathlib import Path
p=Path(r'C:\Users\zin\Documents\GitHub\shinmomo\graphics\runtime_sprite_dynamic')
# current corrected OAM piece renders, 4x scaled. reduce to native then composite
specs={
 'slot2_actual_oam_split.png':[(p/'oam_000_x113_y112_t08_a12.png',113,112),(p/'oam_001_x112_y110_t06_a52.png',112,110)],
 'slot3_actual_oam_split.png':[(p/'oam_002_x112_y110_t26_a52.png',112,110)]
}
for name,items in specs.items():
 ims=[]
 for f,x,y in items:
  im=Image.open(f).convert('RGBA'); im=im.resize((im.width//4,im.height//4),Image.Resampling.NEAREST);ims.append((im,x,y))
 x0=min(x for im,x,y in ims);y0=min(y for im,x,y in ims);x1=max(x+im.width for im,x,y in ims);y1=max(y+im.height for im,x,y in ims)
 out=Image.new('RGBA',(x1-x0,y1-y0),(0,0,0,0))
 for im,x,y in ims: out.alpha_composite(im,(x-x0,y-y0))
 out.resize((out.width*10,out.height*10),Image.Resampling.NEAREST).save(p/name)
 print(name,out.size)
