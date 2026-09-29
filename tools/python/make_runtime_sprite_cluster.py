from PIL import Image
from pathlib import Path
p=Path(r'C:\Users\zin\Documents\GitHub\shinmomo\graphics\runtime_sprite_dynamic')
items=[(p/'oam_000_x113_y112_t08_a12.png',113,112),(p/'oam_001_x112_y110_t06_a52.png',112,110)]
ims=[(Image.open(f).resize((Image.open(f).width//4,Image.open(f).height//4),Image.Resampling.NEAREST),x,y) for f,x,y in items]
x0=min(x for _,x,y in ims);y0=min(y for _,x,y in ims);x1=max(x+im.width for im,x,y in ims);y1=max(y+im.height for im,x,y in ims)
out=Image.new('RGBA',(x1-x0,y1-y0),(0,0,0,0))
for im,x,y in ims: out.alpha_composite(im,(x-x0,y-y0))
out.resize((out.width*8,out.height*8),Image.Resampling.NEAREST).save(p/'runtime_cluster_slots00_01.png')
print(out.size)