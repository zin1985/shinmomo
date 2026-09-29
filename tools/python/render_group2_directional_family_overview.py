from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
src=(ROOT/'tools/python/render_group2_walk_frames.py').read_text(encoding='utf8')
prefix=src.split("out=ROOT/")[0]; ns={}; exec(prefix,ns); render=ns['render']
families=[
('Momotaro S1-4',[1,2,3,4,5,6,7,8]),
('Alt S5-8',[9,10,11,12,13,14,15,16]),
('F78-85',[78,79,80,81,82,83,84,85]),
('F86-93',[86,87,88,89,90,91,92,93]),
('F94-101',[94,95,96,97,98,99,100,101]),
('F102-109',[102,103,104,105,106,107,108,109]),
('F110-117',[110,111,112,113,114,115,116,117]),
('F118-125',[118,119,120,121,122,123,124,125]),
('F132-139',[132,133,134,135,136,137,138,139]),
('F140-147',[140,141,142,143,144,145,146,147]),
('F221-228',[221,222,223,224,225,226,227,228]),
('F229-236',[229,230,231,232,233,234,235,236]),
('F237-244 slow NPC',[237,238,239,240,241,242,243,244])
]
cellw,cellh=96,110;labelw=150
M=Image.new('RGBA',(labelw+8*cellw,len(families)*cellh),(0,0,0,255));dr=ImageDraw.Draw(M)
for row,(label,frames) in enumerate(families):
 y=row*cellh;dr.text((4,y+4),label,fill='white')
 for col,fr in enumerate(frames):
  try: im=render(fr)
  except Exception: continue
  im=im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST)
  x=labelw+col*cellw
  M.alpha_composite(im,(x+(cellw-im.width)//2,y+18))
  dr.text((x+3,y+3),f'F{fr}',fill='white')
out=ROOT/'graphics/runtime_sprite_dynamic/group2_directional_family_overview.png';M.save(out);print(out)
