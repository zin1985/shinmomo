#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render VRAM/CGRAM dump files made by shinmomo_vram_cgram_tilemap_dump_v1_snes9x.lua."""
from __future__ import annotations
import argparse, csv, math
from pathlib import Path
from PIL import Image, ImageDraw


def cgram_to_rgb(cgram: bytes):
    pal=[]
    for i in range(0, min(len(cgram),512), 2):
        raw = cgram[i] | (cgram[i+1]<<8)
        r = (raw & 0x1F) * 255 // 31
        g = ((raw >> 5) & 0x1F) * 255 // 31
        b = ((raw >> 10) & 0x1F) * 255 // 31
        pal.append((r,g,b))
    while len(pal)<256: pal.append((0,0,0))
    return pal


def gray_palette(n):
    return [(i*255//max(1,n-1),)*3 for i in range(n)] + [(0,0,0)]*(256-n)


def decode_tile(data: bytes, tile_index: int, bpp: int, base: int=0):
    ts = {2:16,4:32,8:64}[bpp]
    off = base + tile_index * ts
    tile = data[off:off+ts]
    px=[[0]*8 for _ in range(8)]
    if len(tile)<ts: return px
    if bpp==2:
        for y in range(8):
            p0=tile[y*2]; p1=tile[y*2+1]
            for x in range(8):
                bit=7-x
                px[y][x]=((p0>>bit)&1)|(((p1>>bit)&1)<<1)
    elif bpp==4:
        for y in range(8):
            p0=tile[y*2]; p1=tile[y*2+1]; p2=tile[16+y*2]; p3=tile[16+y*2+1]
            for x in range(8):
                bit=7-x
                px[y][x]=((p0>>bit)&1)|(((p1>>bit)&1)<<1)|(((p2>>bit)&1)<<2)|(((p3>>bit)&1)<<3)
    else:
        # SNES 8bpp: 4bpp first 32 + high planes next 32
        for y in range(8):
            planes=[tile[y*2],tile[y*2+1],tile[16+y*2],tile[16+y*2+1],tile[32+y*2],tile[32+y*2+1],tile[48+y*2],tile[48+y*2+1]]
            for x in range(8):
                bit=7-x; v=0
                for p in range(8): v |= ((planes[p]>>bit)&1)<<p
                px[y][x]=v
    return px


def render_tilesheet(vram: bytes, pal, bpp: int, base: int, count: int, cols=32, scale=2):
    rows=math.ceil(count/cols)
    im=Image.new('RGB',(cols*8,rows*8),(0,0,0))
    for t in range(count):
        px=decode_tile(vram,t,bpp,base)
        ox=(t%cols)*8; oy=(t//cols)*8
        for y in range(8):
            for x in range(8):
                im.putpixel((ox+x,oy+y),pal[px[y][x] % len(pal)])
    if scale!=1: im=im.resize((im.width*scale,im.height*scale), Image.Resampling.NEAREST)
    return im


def render_tilemap(vram: bytes, pal, page_base: int, tile_base: int, bpp: int, scale=2):
    im=Image.new('RGB',(256,256),(0,0,0))
    colors_per_pal={2:4,4:16,8:256}[bpp]
    for i in range(1024):
        off=page_base+i*2
        if off+1>=len(vram): continue
        raw=vram[off]|(vram[off+1]<<8)
        tile=raw&0x3FF; palidx=(raw>>10)&7; hf=(raw>>14)&1; vf=(raw>>15)&1
        px=decode_tile(vram,tile,bpp,tile_base)
        ox=(i%32)*8; oy=(i//32)*8
        for y in range(8):
            sy=7-y if vf else y
            for x in range(8):
                sx=7-x if hf else x
                ci=px[sy][sx]
                if ci==0: col=(0,0,0)
                else: col=pal[(palidx*colors_per_pal + ci) % len(pal)]
                im.putpixel((ox+x,oy+y),col)
    if scale!=1: im=im.resize((im.width*scale,im.height*scale), Image.Resampling.NEAREST)
    return im


def annotate(im, text):
    out=Image.new('RGB',(im.width, im.height+18),(255,255,255)); out.paste(im,(0,18))
    ImageDraw.Draw(out).text((2,2),text,fill=(0,0,0)); return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('dump_dir', type=Path)
    ap.add_argument('--frame', default='latest')
    ap.add_argument('--bpp', type=int, default=4, choices=[2,4,8])
    ap.add_argument('--tile-base', default='0x0000')
    ap.add_argument('--out', type=Path, default=None)
    args=ap.parse_args()
    d=args.dump_dir
    vrams=sorted(d.glob('vram_frame*.bin'))
    if not vrams: raise SystemExit('no vram_frame*.bin')
    vram_path=vrams[-1] if args.frame=='latest' else d/f'vram_frame{int(args.frame):06d}.bin'
    tag=vram_path.stem.replace('vram_','')
    cgram_path=d/f'cgram_{tag}.bin'
    vram=vram_path.read_bytes()
    pal=cgram_to_rgb(cgram_path.read_bytes()) if cgram_path.exists() else gray_palette(256)
    out=args.out or d/'rendered'
    out.mkdir(parents=True, exist_ok=True)
    tile_base=int(args.tile_base,0)
    ts={2:16,4:32,8:64}[args.bpp]
    max_count=max(0,(len(vram)-tile_base)//ts)
    count=min(max_count,1024)
    annotate(render_tilesheet(vram,pal,args.bpp,tile_base,count), f'{tag} VRAM tile sheet bpp={args.bpp} tile_base=0x{tile_base:04X} count={count}').save(out/f'{tag}_tilesheet_{args.bpp}bpp_base{tile_base:04X}.png')
    for page in range(0,0x10000,0x800):
        im=render_tilemap(vram,pal,page,tile_base,args.bpp)
        annotate(im, f'{tag} tilemap page=0x{page:04X} bpp={args.bpp} tile_base=0x{tile_base:04X}').save(out/f'{tag}_tilemap_page{page:04X}_{args.bpp}bpp_base{tile_base:04X}.png')
    print(out)
if __name__=='__main__': main()
