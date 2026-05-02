#!/usr/bin/env python3
"""Render a tile-id CSV grid as a pseudocolor PNG for quick debugging.
No external palette/CGRAM is required.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

if len(sys.argv) < 3:
    print('usage: render_tilemap_png_pseudocolor_v1.py tilemap.csv out.png [cell=8]', file=sys.stderr)
    sys.exit(2)

inp, out = sys.argv[1], sys.argv[2]
cell = int(sys.argv[3]) if len(sys.argv)>3 else 8
rows=[]
for line in open(inp, encoding='utf-8-sig'):
    line=line.strip()
    if not line or line.startswith('#'): continue
    vals=[int(tok.strip(),0) for tok in line.replace('\t',',').split(',') if tok.strip()]
    if vals: rows.append(vals)
if not rows: sys.exit('empty tilemap')
w=max(len(r) for r in rows); h=len(rows)
img=Image.new('RGB',(w*cell,h*cell),'black')
d=ImageDraw.Draw(img)
for y,row in enumerate(rows):
    for x,t in enumerate(row):
        # deterministic pseudo-color
        col=((t*53)%256,(t*97)%256,(t*193)%256)
        d.rectangle([x*cell,y*cell,(x+1)*cell-1,(y+1)*cell-1], fill=col)
img.save(out)
