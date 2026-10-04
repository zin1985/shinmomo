from pathlib import Path
from PIL import Image,ImageDraw
import json
ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
src=(ROOT/'tools/python/render_group2_walk_frames.py').read_text(encoding='utf8')
# extract renderer prefix before output block
prefix=src.split("out=ROOT/")[0]
ranges=[('78_93',list(range(78,94))),('94_109',list(range(94,110))),('110_125',list(range(110,126))),('132_147',list(range(132,148))),('221_244',list(range(221,245)))]
ns={}
exec(prefix,ns)
render=ns['render']
outdir=ROOT/'graphics/runtime_sprite_dynamic'
for name,frames in ranges:
 cols=8; cellw=96; cellh=128; rows=(len(frames)+cols-1)//cols
 M=Image.new('RGBA',(cols*cellw,rows*cellh),(0,0,0,0));dr=ImageDraw.Draw(M)
 for i,fr in enumerate(frames):
  try: im=render(fr)
  except Exception: continue
  im=im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST)
  x=(i%cols)*cellw;y=(i//cols)*cellh
  M.alpha_composite(im,(x+(cellw-im.width)//2,y+20));dr.text((x+4,y+4),f'F{fr}',fill='white')
 p=outdir/f'group2_frames_{name}.png';M.save(p);print(p)
