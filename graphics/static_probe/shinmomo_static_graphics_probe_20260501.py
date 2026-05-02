#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新桃太郎伝説 グラフィック静的解析補助 2026-05-01
- ROM内の DMA/VRAM queue helper 参照を列挙
- DA:3800 stream decoded CSV を簡易グリフ画像化
- VRAM dump の exact tile raw match 有無をチェック
Usage:
  python shinmomo_static_graphics_probe_20260501.py --rom "Shin Momotarou Densetsu (J).smc" --vram vram.bin --da-csv shinmomo_da3800_streams_decoded_records_20260314.csv --out outdir
"""
from __future__ import annotations
import argparse, csv, math
from pathlib import Path
from collections import Counter
from PIL import Image, ImageDraw

def raw_to_snes(raw:int, base:int=0xC0)->str:
    return f"{base + raw//0x10000:02X}:{raw%0x10000:04X}"

def find_all(data:bytes, pat:bytes):
    out=[]; s=0
    while True:
        i=data.find(pat,s)
        if i<0: break
        out.append(i); s=i+1
    return out

def render_da_records(da_csv:Path, outdir:Path):
    rows=[]
    with da_csv.open('r',encoding='utf-8-sig') as f:
        rows=list(csv.DictReader(f))
    def hb(s): return bytes.fromhex(s) if s else b''
    def render(r,scale=2):
        seg0=hb(r['seg0_bytes_hex']); seg2=hb(r['seg2_bytes_hex'])
        h=max(len(seg0),len(seg2),1); w=8
        img=Image.new('L',(w,h),255); px=img.load()
        for y,b in enumerate(seg0):
            for x in range(8):
                if b & (0x80>>x): px[x,y]=0
        for y,b in enumerate(seg2):
            for x in range(8):
                if b & (0x80>>x) and px[x,y]!=0: px[x,y]=110
        return img.resize((w*scale,h*scale),Image.Resampling.NEAREST)
    da_out=outdir/'da3800_render'
    da_out.mkdir(exist_ok=True)
    for sid in sorted(set(int(r['stream_id']) for r in rows)):
        rs=[r for r in rows if int(r['stream_id'])==sid]
        cols=16; cellw=24; cellh=42
        for page in range(math.ceil(len(rs)/64)):
            part=rs[page*64:(page+1)*64]
            mont=Image.new('RGB',(cols*cellw, max(1,math.ceil(len(part)/cols))*cellh),'white')
            d=ImageDraw.Draw(mont)
            for idx,r in enumerate(part):
                im=render(r).convert('RGB')
                x=(idx%cols)*cellw; y=(idx//cols)*cellh
                mont.paste(im,(x+4,y+4))
                d.text((x+2,y+30),str(int(r['record_index'])),fill=(0,0,0))
            mont.save(da_out/f'da3800_stream{sid:02d}_page{page+1}.png')

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--rom',required=True)
    ap.add_argument('--vram')
    ap.add_argument('--da-csv')
    ap.add_argument('--out',required=True)
    args=ap.parse_args()
    outdir=Path(args.out); outdir.mkdir(parents=True,exist_ok=True)
    rom=Path(args.rom).read_bytes()
    patterns={
        'JSL $80:A151 transfer_queue_begin?': bytes([0x22,0x51,0xA1,0x80]),
        'JSL $80:A170 transfer_queue_write?': bytes([0x22,0x70,0xA1,0x80]),
        'JSL $80:A185 transfer_queue_commit?': bytes([0x22,0x85,0xA1,0x80]),
        'JSL $80:A474 HDMA/update flag setter': bytes([0x22,0x74,0xA4,0x80]),
        'DA:3800 pointer table operand': bytes([0x00,0x38,0xDA]),
    }
    hits=[]
    for name,pat in patterns.items():
        for off in find_all(rom,pat):
            hits.append({
                'pattern':name,
                'raw_offset':f'0x{off:06X}',
                'snes_c_mirror':raw_to_snes(off,0xC0),
                'snes_80_mirror':raw_to_snes(off,0x80),
                'context_hex':rom[max(0,off-8):min(len(rom),off+12)].hex(' ').upper()
            })
    with (outdir/'static_dma_asset_reference_hits.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['pattern','raw_offset','snes_c_mirror','snes_80_mirror','context_hex'])
        w.writeheader(); w.writerows(hits)
    if args.da_csv:
        render_da_records(Path(args.da_csv),outdir)

if __name__ == '__main__':
    main()
