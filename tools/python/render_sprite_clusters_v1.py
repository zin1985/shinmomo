#!/usr/bin/env python3
"""Render clustered 4bpp SNES sprite pieces from VRAM dump.

Input: oam_chr_mapping CSV with x,y,tile,palette,hflip,vflip,chr_addr_hex,cluster_id optional.
If cluster_id is absent, all rows are rendered as one cluster.
"""
import argparse, csv, os
from pathlib import Path
from PIL import Image

def decode_4bpp_tile(data):
    pix = [[0]*8 for _ in range(8)]
    if len(data) < 32: return pix
    for y in range(8):
        p0=data[y*2]; p1=data[y*2+1]; p2=data[y*2+16]; p3=data[y*2+17]
        for x in range(8):
            b=7-x
            pix[y][x]=((p0>>b)&1)|(((p1>>b)&1)<<1)|(((p2>>b)&1)<<2)|(((p3>>b)&1)<<3)
    return pix

def default_palette():
    return [(0,0,0,0)] + [(i*16, i*16, i*16, 255) for i in range(1,16)]

def i(v,d=0):
    try: return int(str(v),0)
    except Exception: return d

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('vram')
    ap.add_argument('csv')
    ap.add_argument('out_dir')
    args=ap.parse_args()
    vram=Path(args.vram).read_bytes()
    out=Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    rows=list(csv.DictReader(open(args.csv, newline='', encoding='utf-8')))
    groups={}
    for r in rows:
        cid=r.get('cluster_id') or r.get('object_id') or 'cluster_all'
        groups.setdefault(cid,[]).append(r)
    pal=default_palette()
    for cid, rs in groups.items():
        xs=[i(r.get('x'),0) for r in rs]; ys=[i(r.get('y'),0) for r in rs]
        minx,miny=min(xs),min(ys); maxx,maxy=max(xs)+8,max(ys)+8
        img=Image.new('RGBA',(maxx-minx,maxy-miny),(0,0,0,0))
        # sort by priority then slot
        rs=sorted(rs,key=lambda r:(i(r.get('priority'),0), i(r.get('slot'),0)))
        for r in rs:
            addr=i('0x'+str(r.get('chr_addr_hex','0')).replace('0x',''),0)
            tile=decode_4bpp_tile(vram[addr:addr+32])
            hf=i(r.get('hflip'),0); vf=i(r.get('vflip'),0)
            ox=i(r.get('x'),0)-minx; oy=i(r.get('y'),0)-miny
            for y in range(8):
                for x in range(8):
                    sx=7-x if hf else x; sy=7-y if vf else y
                    ci=tile[sy][sx]
                    if ci==0: continue
                    img.putpixel((ox+x,oy+y),pal[ci])
        img.save(out/(cid+'.png'))

if __name__=='__main__':
    main()
