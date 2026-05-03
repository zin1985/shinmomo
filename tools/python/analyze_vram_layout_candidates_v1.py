#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from collections import Counter, defaultdict
import csv, math, argparse
from PIL import Image, ImageDraw

GREY4 = [(i*17, i*17, i*17) for i in range(16)]
PSEUDO4 = [
    (0,0,0),(34,34,34),(68,68,68),(102,102,102),
    (136,136,136),(170,170,170),(204,204,204),(238,238,238),
    (60,30,90),(90,60,30),(30,90,60),(120,80,40),
    (40,80,120),(120,40,80),(80,120,40),(255,255,255),
]

def decode_4bpp(tile: bytes):
    px = [[0]*8 for _ in range(8)]
    if len(tile) < 32:
        return px
    for y in range(8):
        p0 = tile[y*2]
        p1 = tile[y*2+1]
        p2 = tile[y*2+16]
        p3 = tile[y*2+17]
        for x in range(8):
            bit = 7-x
            px[y][x] = ((p0>>bit)&1) | (((p1>>bit)&1)<<1) | (((p2>>bit)&1)<<2) | (((p3>>bit)&1)<<3)
    return px

def decode_2bpp(tile: bytes):
    px = [[0]*8 for _ in range(8)]
    if len(tile) < 16:
        return px
    for y in range(8):
        p0 = tile[y*2]
        p1 = tile[y*2+1]
        for x in range(8):
            bit = 7-x
            px[y][x] = ((p0>>bit)&1) | (((p1>>bit)&1)<<1)
    return px

def render_tile(img, px, ox, oy, pal=PSEUDO4, scale=1):
    for y in range(8):
        for x in range(8):
            c = pal[px[y][x] % len(pal)]
            if scale == 1:
                img.putpixel((ox+x, oy+y), c)
            else:
                for yy in range(scale):
                    for xx in range(scale):
                        img.putpixel((ox+x*scale+xx, oy+y*scale+yy), c)

def render_4bpp_atlas(vram: bytes, base: int, size: int, out: Path, cols=32, scale=2, title=''):
    data = vram[base:base+size]
    tiles = [data[i:i+32] for i in range(0, len(data), 32) if len(data[i:i+32]) == 32]
    rows = math.ceil(len(tiles)/cols)
    header = 18 if title else 0
    img = Image.new('RGB', (cols*8*scale, rows*8*scale+header), (18,18,18))
    d = ImageDraw.Draw(img)
    if title:
        d.text((4,3), title, fill=(255,255,255))
    for i,t in enumerate(tiles):
        x = (i % cols)*8*scale
        y = header + (i//cols)*8*scale
        render_tile(img, decode_4bpp(t), x, y, PSEUDO4, scale)
    img.save(out)

def render_range_contact(vram: bytes, out: Path):
    # 0x1000ごとの小atlasを縦積み。battle/field判定用。
    panels=[]
    for base in range(0, 0x10000, 0x1000):
        data=vram[base:base+0x1000]
        tiles=[data[i:i+32] for i in range(0,len(data),32)]
        cols=16; scale=1; rows=math.ceil(len(tiles)/cols); header=12
        img=Image.new('RGB',(cols*8*scale, rows*8*scale+header),(20,20,20))
        d=ImageDraw.Draw(img); d.text((2,1), f'{base:04X}-{base+0x0FFF:04X}', fill=(255,255,255))
        for i,t in enumerate(tiles):
            render_tile(img, decode_4bpp(t), (i%cols)*8*scale, header+(i//cols)*8*scale, PSEUDO4, scale)
        panels.append(img)
    w=max(p.width for p in panels); h=sum(p.height for p in panels)
    canvas=Image.new('RGB',(w,h),(0,0,0)); y=0
    for p in panels:
        canvas.paste(p,(0,y)); y+=p.height
    canvas.save(out)

def region_summary(vram: bytes):
    rows=[]
    for base in range(0,0x10000,0x1000):
        b=vram[base:base+0x1000]
        nz=sum(1 for x in b if x)
        tiles4=[b[i:i+32] for i in range(0,len(b),32)]
        tiles2=[b[i:i+16] for i in range(0,len(b),16)]
        words=[b[i] | (b[i+1]<<8) for i in range(0,len(b)-1,2)]
        word_counts=Counter(words)
        rows.append({
            'base':f'{base:04X}', 'end':f'{base+0x0FFF:04X}',
            'nonzero_byte_ratio':f'{nz/len(b):.4f}',
            'byte_unique':len(set(b)),
            'word_unique':len(word_counts),
            'word_top_repeat_ratio':f'{(word_counts.most_common(1)[0][1]/len(words)) if words else 0:.4f}',
            'tiles_4bpp_nonblank':sum(any(t) for t in tiles4),
            'tiles_4bpp_unique':len(set(tiles4)),
            'tiles_2bpp_nonblank':sum(any(t) for t in tiles2),
            'tiles_2bpp_unique':len(set(tiles2)),
            'chr_likeness_4bpp':f'{(sum(any(t) for t in tiles4)/len(tiles4))* (len(set(tiles4))/len(tiles4)):.4f}',
        })
    return rows

def parse_entry(v):
    return {
        'tile': v & 0x03ff,
        'palette': (v >> 10) & 7,
        'priority': (v >> 13) & 1,
        'hflip': (v >> 14) & 1,
        'vflip': (v >> 15) & 1,
    }

def tile_nonblank(vram: bytes, char_base: int, tile_id: int, bpp: int):
    size = 32 if bpp==4 else 16
    off = char_base + tile_id*size
    if off < 0 or off+size > len(vram): return False
    return any(vram[off:off+size])

def candidate_scores(vram: bytes):
    rows=[]
    char_bases=[0x0000,0x2000,0x4000,0x6000,0x8000,0xA000,0xC000,0xE000]
    for map_base in range(0,0x10000-0x800+1,0x800):
        raw=vram[map_base:map_base+0x800]
        vals=[raw[i] | (raw[i+1]<<8) for i in range(0,0x800,2)]
        entries=[parse_entry(v) for v in vals]
        pal=Counter(e['palette'] for e in entries)
        tile=Counter(e['tile'] for e in entries)
        attr=Counter((e['palette'],e['priority'],e['hflip'],e['vflip']) for e in entries)
        top_pal_ratio=pal.most_common(1)[0][1]/len(entries)
        top_attr_ratio=attr.most_common(1)[0][1]/len(entries)
        tile_repeat_ratio=1-len(tile)/len(entries)
        flip_ratio=sum(e['hflip'] or e['vflip'] for e in entries)/len(entries)
        prio_ratio=sum(e['priority'] for e in entries)/len(entries)
        # horizontal pair repetition in 32x32
        pairs=[]
        for y in range(32):
            for x in range(31):
                a=entries[y*32+x]['tile']; b=entries[y*32+x+1]['tile']
                pairs.append((a,b))
        pair_counts=Counter(pairs)
        pair_repeat_ratio=1-len(pair_counts)/len(pairs)
        for char_base in char_bases:
            for bpp in (2,4):
                nb=sum(tile_nonblank(vram,char_base,e['tile'],bpp) for e in entries)
                nb_ratio=nb/len(entries)
                # real tilemap tends to have repeated entries, palette concentration, and references nonblank char tiles.
                # CHR-as-tilemap tends to have broad attrs/flip/prio and lower pair repetition.
                score = (top_pal_ratio*1.2 + top_attr_ratio*1.2 + tile_repeat_ratio*1.6 + pair_repeat_ratio*2.0 + nb_ratio*1.5) - (flip_ratio*0.6 + prio_ratio*0.4)
                rows.append({
                    'map_base':f'{map_base:04X}', 'char_base':f'{char_base:04X}', 'bpp':bpp,
                    'score':round(score,4), 'nonblank_ref_ratio':round(nb_ratio,4),
                    'top_palette_ratio':round(top_pal_ratio,4), 'top_attr_ratio':round(top_attr_ratio,4),
                    'tile_unique':len(tile), 'tile_repeat_ratio':round(tile_repeat_ratio,4),
                    'h_or_v_flip_ratio':round(flip_ratio,4), 'priority_ratio':round(prio_ratio,4),
                    'pair_repeat_ratio':round(pair_repeat_ratio,4),
                    'top_tiles':' '.join(f'{k:03X}:{v}' for k,v in tile.most_common(8)),
                    'top_attrs':' '.join(f'p{a[0]}r{a[1]}h{a[2]}v{a[3]}:{c}' for a,c in attr.most_common(4)),
                })
    rows.sort(key=lambda r: r['score'], reverse=True)
    return rows

def render_tilemap_candidate(vram: bytes, map_base: int, char_base: int, bpp: int, out: Path, scale=2):
    raw=vram[map_base:map_base+0x800]
    vals=[raw[i] | (raw[i+1]<<8) for i in range(0,0x800,2)]
    img=Image.new('RGB',(32*8*scale,32*8*scale),(0,0,0))
    size=32 if bpp==4 else 16
    for idx,v in enumerate(vals):
        e=parse_entry(v)
        off=char_base + e['tile']*size
        if off+size > len(vram):
            continue
        tile=vram[off:off+size]
        px=decode_4bpp(tile) if bpp==4 else decode_2bpp(tile)
        pal=[]
        # palette bank tinting: preserve color index but tint by palette number
        tint=e['palette']
        for i in range(16 if bpp==4 else 4):
            base=i*(255//(15 if bpp==4 else 3))
            pal.append(((base + tint*25)%256, (base + tint*55)%256, (base + tint*85)%256))
        x=(idx%32)*8*scale; y=(idx//32)*8*scale
        # flip while rendering
        for ty in range(8):
            for tx in range(8):
                sx=7-tx if e['hflip'] else tx
                sy=7-ty if e['vflip'] else ty
                c=pal[px[sy][sx] % len(pal)]
                for yy in range(scale):
                    for xx in range(scale): img.putpixel((x+tx*scale+xx,y+ty*scale+yy),c)
    img.save(out)

def write_csv(path: Path, rows):
    rows=list(rows)
    if not rows: return
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('vram')
    ap.add_argument('outdir')
    args=ap.parse_args()
    vram=Path(args.vram).read_bytes()
    out=Path(args.outdir); out.mkdir(parents=True,exist_ok=True)
    rs=region_summary(vram); write_csv(out/'current_vram_region_summary_20260502_run2.csv', rs)
    scores=candidate_scores(vram); write_csv(out/'current_vram_tilemap_candidate_scores_20260502_run2.csv', scores)
    render_range_contact(vram, out/'current_vram_4bpp_region_contact_sheet_20260502_run2.png')
    render_4bpp_atlas(vram,0x0000,0x8000,out/'current_vram_0000_7fff_4bpp_chr_atlas_20260502_run2.png',cols=32,scale=2,title='VRAM 0000-7FFF as 4bpp CHR')
    render_4bpp_atlas(vram,0x8000,0x8000,out/'current_vram_8000_ffff_4bpp_chr_atlas_20260502_run2.png',cols=32,scale=2,title='VRAM 8000-FFFF as 4bpp CHR')
    # render top 4 tilemap candidates
    for i,r in enumerate(scores[:4],1):
        render_tilemap_candidate(vram,int(r['map_base'],16),int(r['char_base'],16),int(r['bpp']),out/f'current_vram_tilemap_candidate_rank{i}_{r["map_base"]}_char{r["char_base"]}_{r["bpp"]}bpp.png')

if __name__ == '__main__':
    main()
