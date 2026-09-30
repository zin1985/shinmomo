#!/usr/bin/env python3
from pathlib import Path
import csv, json, sys
from PIL import Image, ImageDraw

ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
sys.path.insert(0,str(ROOT/'tools/python'))
from render_normal_map_family_from_setup import file_off, u16_cpu, graphics_descriptor, decode_graphics_resource

ROM_PATH=Path(r'C:\Users\zin\Downloads\Shin Momotarou Densetsu (J)\Shin Momotarou Densetsu (J)_original.smc')
rom=ROM_PATH.read_bytes()
CTX=5

def ptr24_table(addr,index):
    off=file_off(0xC0,addr+index*3)
    return rom[off+2], rom[off] | (rom[off+1]<<8)

def b294_group(g):
    return ptr24_table(0xB294,g)

def frame_pieces(g,fr):
    bank,base=b294_group(g)
    poff=file_off(bank,(base+(fr-1)*2)&0xffff)
    ptr=rom[poff] | (rom[poff+1]<<8)
    off=file_off(bank,ptr)
    n=rom[off]
    return [tuple(rom[off+1+i*4:off+5+i*4]) for i in range(n)]

def chr_window(g,index):
    bank,base=ptr24_table(0xB2EE,g)
    off=file_off(bank,(base+(index-1)*2)&0xffff)
    return rom[off],rom[off+1]

def palette_payload(resource_id):
    table=u16_cpu(rom,0xC0,0xB516+CTX*2)
    entry=u16_cpu(rom,0xC0,table+(resource_id-1)*2)
    off=file_off(0xC0,entry)
    destination=rom[off] | (rom[off+1]<<8)
    count=rom[off+2] | (rom[off+3]<<8)
    colors=[(0,0,0,0)]*256
    for i in range(count):
        w=rom[off+4+i*2] | (rom[off+5+i*2]<<8)
        idx=destination+i
        if idx < 256:
            colors[idx]=((w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31,255)
    return colors,{'table':f'C0:{table:04X}','entry':f'C0:{entry:04X}','destination':destination,'count':count}

def decode_tile(chunk):
    if len(chunk)<32:return None
    z=[[0]*8 for _ in range(8)]
    for y in range(8):
        for x in range(8):
            q=7-x
            z[y][x]=((chunk[y*2]>>q)&1)|(((chunk[y*2+1]>>q)&1)<<1)|(((chunk[y*2+16]>>q)&1)<<2)|(((chunk[y*2+17]>>q)&1)<<3)
    return z

def selector_record(sel):
    raw=rom[sel*5:sel*5+5]
    return {
        'selector':sel,
        'chr_resource':raw[0],
        'chr_window_index':raw[1],
        'base_state':raw[2],
        'sprite_group_raw':raw[3],
        'sprite_group':raw[3]&15,
        'palette_resource':raw[4],
        'raw':raw.hex(' ')
    }

states={}
with open(ROOT/'data/npc_display/shinmomo_B2C1_animation_state_scripts_20260425.csv',encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        seq=[int(x) for x in r['frame_sequence_dec'].split(',') if x.strip().isdigit()]
        states[(int(r['group']),int(r['state_no_1_based']))]=seq

def render_frame(rec,fr):
    desc=graphics_descriptor(rom,rec['chr_resource'],CTX)
    data=decode_graphics_resource(rom,desc,rec['chr_resource'])
    source_tile_start,tile_count=chr_window(rec['sprite_group'],rec['chr_window_index'])
    obj_base_tile=(source_tile_start&0xE0)|((source_tile_start&0x1F)>>1)

    # B893 OBJ packing: sequential decoded tiles are written as
    # local tile 0,16,1,17,2,18,... inside the allocated OBJ region.
    packed={}
    for j in range(tile_count):
        src=source_tile_start+j
        chunk=data[src*32:(src+1)*32]
        if len(chunk)==32:
            packed[(j//2)+(16 if (j&1) else 0)]=chunk

    palette,pmeta=palette_payload(rec['palette_resource'])
    ps=frame_pieces(rec['sprite_group'],fr)
    entries=[]
    for fl,xb,yb,tile in ps:
        x=xb-256 if fl&0x10 else xb
        y=yb-256 if fl&0x20 else yb
        entries.append((fl,x,y,tile,16 if fl&8 else 8,(fl>>1)&3))

    x0=min(x for _,x,y,t,s,p in entries); y0=min(y for _,x,y,t,s,p in entries)
    x1=max(x+s for _,x,y,t,s,p in entries); y1=max(y+s for _,x,y,t,s,p in entries)
    im=Image.new('RGBA',(x1-x0,y1-y0),(0,0,0,0))

    for fl,x,y,tile,sz,pal in entries:
        for ty in range(sz//8):
            for tx in range(sz//8):
                raw_tile=(tile+tx+ty*16)&0x1ff
                local=raw_tile-obj_base_tile
                chunk=packed.get(local)
                if chunk is None:
                    continue
                z=decode_tile(chunk)
                for py in range(8):
                    for px in range(8):
                        ci=z[py][px]
                        if not ci:continue
                        dx=tx*8+px; dy=ty*8+py
                        if fl&0x40: dx=sz-1-dx
                        if fl&0x80: dy=sz-1-dy
                        idx=128+pal*16+ci
                        col=palette[idx] if idx<len(palette) and palette[idx][3] else (255,0,255,255)
                        im.putpixel((x-x0+dx,y-y0+dy),col)
    return im,desc,{
        'source_tile_start':source_tile_start,
        'tile_count':tile_count,
        'obj_base_tile':obj_base_tile,
        'palette':pmeta,
        'decoded_size':len(data)
    }

outdir=ROOT/'graphics/static_character_reconstruction';outdir.mkdir(exist_ok=True)
TABLE_END=0xAB
rows=[]; rejected=[]; seen={}; atlas_entries=[]
for sel in range(1,TABLE_END):
 rec=selector_record(sel); g=rec['sprite_group']; state=rec['base_state']
 if (g,state) not in states: rejected.append((sel,'animation_state_not_catalogued')); continue
 try:
  desc=graphics_descriptor(rom,rec['chr_resource'],CTX); data=decode_graphics_resource(rom,desc,rec['chr_resource'])
  st,cnt=chr_window(g,rec['chr_window_index'])
  if not cnt or (st+cnt)*32>len(data): raise ValueError(f'CHR window {st}+{cnt}>{len(data)//32}')
  sig=(rec['chr_resource'],rec['chr_window_index'],state,g,rec['palette_resource']); dup=seen.get(sig)
  if dup is None: seen[sig]=sel
  frames=[]
  for ss in range(state,min(state+4,256)): frames.extend(states.get((g,ss),[]))
  frames=frames[:8]
  if not frames: raise ValueError('no animation frames')
  im,_,_=render_frame(rec,frames[0]); thumb=Image.new('RGBA',(64,64),(0,0,0,255))
  zoom=max(1,min(4,48//max(im.width,im.height))); z=im.resize((im.width*zoom,im.height*zoom),Image.Resampling.NEAREST)
  thumb.alpha_composite(z,((64-z.width)//2,(64-z.height)//2))
  if dup is None:
   p=outdir/f'catalog_selector_{sel:02X}.png';thumb.save(p);atlas_entries.append((sel,thumb,rec))
  rows.append({**rec,'source_tile_start':st,'tile_count':cnt,'decoded_size':len(data),'first_frame':frames[0],'frames_sample':','.join(map(str,frames)),'duplicate_of':'' if dup is None else f'0x{dup:02X}','status':'static_rom_reconstructable'})
 except Exception as e: rejected.append((sel,str(e)))
csv_path=ROOT/'data/npc_display/static_character_selector_catalog_20260930.csv'
fields=['selector','chr_resource','chr_window_index','base_state','sprite_group_raw','sprite_group','palette_resource','raw','source_tile_start','tile_count','decoded_size','first_frame','frames_sample','duplicate_of','status']
with csv_path.open('w',newline='',encoding='utf-8') as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
cols=8;cw=96;ch=88
atlas=Image.new('RGBA',(cols*cw,((len(atlas_entries)+cols-1)//cols)*ch),(0,0,0,255));dr=ImageDraw.Draw(atlas)
for i,(sel,thumb,rec) in enumerate(atlas_entries):
 x=(i%cols)*cw;y=(i//cols)*ch;atlas.alpha_composite(thumb,(x+16,y+16))
 dr.text((x+3,y+2),f'{sel:02X} G{rec["sprite_group"]} S{rec["base_state"]}',fill='white')
 dr.text((x+3,y+72),f'R{rec["chr_resource"]} W{rec["chr_window_index"]}',fill=(190,190,190,255))
atlas_path=outdir/'static_character_catalog_atlas_20260930.png';atlas.save(atlas_path)
summary={'selector_table_start':0,'selector_table_end_exclusive':TABLE_END,'total_records':TABLE_END,'reserved_selector_00':True,'static_rom_reconstructable':len(rows),'unique_graphics_signatures':len(atlas_entries),'rejected_count':len(rejected),'rejected':[{'selector':f'0x{s:02X}','reason':e} for s,e in rejected],'atlas':str(atlas_path.relative_to(ROOT)),'catalog_csv':str(csv_path.relative_to(ROOT))}
(ROOT/'data/npc_display/static_character_selector_catalog_summary_20260930.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
