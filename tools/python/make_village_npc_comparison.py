from PIL import Image,ImageDraw
from pathlib import Path
ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
screen=Image.open(r'C:\Users\zin\AppData\Local\shinmomo-lab\screens\game_1790688720923-74e5154a.png').convert('RGBA')
items=[
('slot13 g2 f240 off-32',ROOT/'graphics/runtime_sprite_dynamic/village_slot13_g2_f240_off-32.png',(40,0,64,24)),
('slot22 g7 f15 off+136',ROOT/'graphics/runtime_sprite_dynamic/village_slot22_g7_f015_off+136.png',(56,66,80,98)),
('slot15 g3 f35 off+8',ROOT/'graphics/runtime_sprite_dynamic/village_slot15_g3_f035_off+8.png',(56,130,80,162)),
('slot17 g3 f11 off+32',ROOT/'graphics/runtime_sprite_dynamic/village_slot17_g3_f011_off+32.png',(232,178,256,210))
]
cellw=360;cellh=180
M=Image.new('RGBA',(cellw,len(items)*cellh),(0,0,0,255));dr=ImageDraw.Draw(M)
for i,(label,p,cropbox) in enumerate(items):
 y=i*cellh;dr.text((4,y+4),label,fill='white')
 ref=screen.crop(cropbox).resize((128,128),Image.Resampling.NEAREST)
 rec=Image.open(p).convert('RGBA')
 # shrink 10x render to native, then upscale cleanly
 rec=rec.resize((max(1,rec.width//10),max(1,rec.height//10)),Image.Resampling.NEAREST).resize((128,128),Image.Resampling.NEAREST)
 M.alpha_composite(ref,(10,y+35));M.alpha_composite(rec,(190,y+35))
 dr.text((10,y+22),'screen crop',fill='white');dr.text((190,y+22),'runtime reconstruction',fill='white')
out=ROOT/'graphics/runtime_sprite_dynamic/village_runtime_npc_comparison.png';M.save(out);print(out)
