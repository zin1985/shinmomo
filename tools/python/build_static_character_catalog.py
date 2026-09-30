#!/usr/bin/env python3
from pathlib import Path
import csv, json, importlib.util
from PIL import Image, ImageDraw

ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
spec=importlib.util.spec_from_file_location('static_chars',ROOT/'tools/python/render_static_character_selectors.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

TABLE_END=0xAB
outdir=ROOT/'graphics/static_character_reconstruction'
outdir.mkdir(exist_ok=True)
rows=[]
rejected=[]
seen={}
atlas_entries=[]

for sel in range(1,TABLE_END):
    rec=m.selector_record(sel)
    g=rec['sprite_group']
    base=rec['base_state']
    if (g,base) not in m.states:
        rejected.append((sel,'animation_state_not_catalogued'))
        continue
    frames=[]
    for st in range(base,min(base+4,256)):
        frames.extend(m.states.get((g,st),[]))
    frames=frames[:8]
    if not frames:
        rejected.append((sel,'no_animation_frames'))
        continue
    try:
        # Viewer/catalog representative art should face the camera when the
        # selector starts a four-direction humanoid family. The engine's
        # established ordering is right, down(front), left, up(back).
        display_frame=frames[0]
        display_orientation='base_state_first_frame'
        if g in {2,3} and all(m.states.get((g,base+i)) for i in range(4)):
            display_frame=m.states[(g,base+1)][0]
            display_orientation='front_preferred_state_plus_1'
        im,desc,info=m.render_frame(rec,display_frame)
        sig=(rec['chr_resource'],rec['chr_window_index'],base,g,rec['palette_resource'])
        duplicate_of=seen.get(sig)
        if duplicate_of is None:
            seen[sig]=sel
            thumb=Image.new('RGBA',(64,64),(0,0,0,255))
            zoom=max(1,min(4,48//max(1,im.width,im.height)))
            z=im.resize((im.width*zoom,im.height*zoom),Image.Resampling.NEAREST)
            thumb.alpha_composite(z,((64-z.width)//2,(64-z.height)//2))
            p=outdir/f'catalog_selector_{sel:02X}.png'
            thumb.save(p)
            atlas_entries.append((sel,thumb,rec,info))
        rows.append({
            **rec,
            'graphics_context':info['graphics_context'],
            'source_tile_start':info['source_tile_start'],
            'tile_count':info['tile_count'],
            'decoded_size':info['decoded_size'],
            'first_frame':frames[0],
            'display_frame':display_frame,
            'display_orientation':display_orientation,
            'frames_sample':','.join(map(str,frames)),
            'duplicate_of':'' if duplicate_of is None else f'0x{duplicate_of:02X}',
            'status':'static_rom_reconstructable'
        })
    except Exception as e:
        rejected.append((sel,str(e)))

csv_path=ROOT/'data/npc_display/static_character_selector_catalog_20260930.csv'
fields=[
    'selector','chr_resource','chr_window_index','base_state','sprite_group_raw','sprite_group',
    'palette_resource','raw','graphics_context','source_tile_start','tile_count','decoded_size',
    'first_frame','display_frame','display_orientation','frames_sample','duplicate_of','status'
]
with csv_path.open('w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

cols=8; cw=96; ch=88
atlas=Image.new('RGBA',(cols*cw,((len(atlas_entries)+cols-1)//cols)*ch),(0,0,0,255))
dr=ImageDraw.Draw(atlas)
for i,(sel,thumb,rec,info) in enumerate(atlas_entries):
    x=(i%cols)*cw; y=(i//cols)*ch
    atlas.alpha_composite(thumb,(x+16,y+16))
    dr.text((x+3,y+2),f'{sel:02X} G{rec["sprite_group"]} S{rec["base_state"]}',fill='white')
    dr.text((x+3,y+72),f'C{info["graphics_context"]} R{rec["chr_resource"]} W{rec["chr_window_index"]}',fill=(190,190,190,255))

atlas_path=outdir/'static_character_catalog_atlas_20260930.png'
atlas.save(atlas_path)
summary={
    'selector_table_start':0,
    'selector_table_end_exclusive':TABLE_END,
    'total_records':TABLE_END,
    'reserved_selector_00':True,
    'static_rom_reconstructable':len(rows),
    'unique_graphics_signatures':len(atlas_entries),
    'rejected_count':len(rejected),
    'rejected':[{'selector':f'0x{s:02X}','reason':e} for s,e in rejected],
    'atlas':str(atlas_path.relative_to(ROOT)),
    'catalog_csv':str(csv_path.relative_to(ROOT))
}
(ROOT/'data/npc_display/static_character_selector_catalog_summary_20260930.json').write_text(
    json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
