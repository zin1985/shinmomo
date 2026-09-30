#!/usr/bin/env python3
from pathlib import Path
import csv, json, sys
from PIL import Image, ImageDraw

ROOT=Path(r'C:\Users\zin\Documents\GitHub\shinmomo')
sys.path.insert(0,str(ROOT/'tools/python'))
from render_normal_map_family_from_setup import file_off, u16_cpu, graphics_descriptor, decode_graphics_resource

ROM_PATH=Path(r'C:\Users\zin\Downloads\Shin Momotarou Densetsu (J)\Shin Momotarou Densetsu (J)_original.smc')
rom=ROM_PATH.read_bytes()
DEFAULT_CTX=5


def context_for_group(group):
    # Object/resource setup at physical ROM 0x1AE70 selects context 0 for
    # sprite groups 0/1 and context 5 for groups >=2.
    return 0 if group < 2 else DEFAULT_CTX

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

def palette_payload(resource_id, context):
    table=u16_cpu(rom,0xC0,0xB516+context*2)
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
    group=rec['sprite_group']
    context=context_for_group(group)
    desc=graphics_descriptor(rom,rec['chr_resource'],context)
    data=decode_graphics_resource(rom,desc,rec['chr_resource'])
    if group < 2 and rec['chr_window_index'] == 0:
        # Special group-0/1 path: object setup clears $1122/$1121 and skips
        # B25E when the selector's window byte is zero. The entire decoded
        # resource is therefore packed from source tile 0.
        source_tile_start=0
        tile_count=len(data)//32
    else:
        source_tile_start,tile_count=chr_window(group,rec['chr_window_index'])
    obj_base_tile=(source_tile_start&0xE0)|((source_tile_start&0x1F)>>1)

    # B893 OBJ packing: each 32-tile source block is swizzled as
    # 0,16,1,17,...,15,31, then the next block continues at +32.
    packed={}
    for j in range(tile_count):
        src=source_tile_start+j
        chunk=data[src*32:(src+1)*32]
        if len(chunk)==32:
            within=j & 0x1F
            local=(j & ~0x1F) + (within//2) + (16 if (within&1) else 0)
            packed[local]=chunk

    palette,pmeta=palette_payload(rec['palette_resource'],context)
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
        'decoded_size':len(data),
        'graphics_context':context
    }

sels=[0x01,0x0D,0x24,0x40,0x3F,0x7D]
outdir=ROOT/'graphics/static_character_reconstruction'
outdir.mkdir(exist_ok=True)
metas=[]
for sel in sels:
    rec=selector_record(sel)
    g=rec['sprite_group']; base=rec['base_state']
    frame_list=[]
    for st in range(base,base+4):
        frame_list.extend(states.get((g,st),[]))
    frame_list=frame_list[:8]
    M=Image.new('RGBA',(max(1,len(frame_list))*96,128),(0,0,0,255))
    dr=ImageDraw.Draw(M)
    info=None; desc=None
    for i,fr in enumerate(frame_list):
        im,desc,info=render_frame(rec,fr)
        im=im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST)
        M.alpha_composite(im,(i*96+(96-im.width)//2,20))
        dr.text((i*96+3,3),f'F{fr}',fill='white')
    p=outdir/f'selector_{sel:02X}_g{g}_s{base:03d}.png'
    M.save(p)
    metas.append({**rec,'frames':frame_list,'output':str(p.relative_to(ROOT)),**(info or {}),'descriptor':desc})
    print(f'{sel:02X}',rec,'frames',frame_list,'window',None if info is None else (info['source_tile_start'],info['tile_count'],info['obj_base_tile']),'->',p)

(ROOT/'data/npc_display/static_display_selector_probe_20260930.json').write_text(
    json.dumps(metas,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
