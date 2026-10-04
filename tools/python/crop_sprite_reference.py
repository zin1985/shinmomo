from PIL import Image
from pathlib import Path
im=Image.open(r'C:\Users\zin\AppData\Local\shinmomo-lab\screens\game_1790685032054-00f5181a.png').convert('RGB')
# exact region around OAM coords; upscale
crop=im.crop((104,100,144,140))
crop.resize((320,320),Image.Resampling.NEAREST).save(r'C:\Users\zin\Documents\GitHub\shinmomo\graphics\runtime_sprite_dynamic\reference_screen_oam_region.png')
print(sorted(crop.getcolors(crop.width*crop.height),reverse=True)[:20])
