#!/usr/bin/env python3
"""Build 2x2 metatile frequency from BG tilemap CSV.
Input columns expected: tx,ty,entry_hex or tile/palette/priority/hflip/vflip.
"""
import csv, sys
from collections import Counter

def key_for(row):
    if 'entry_hex' in row and row['entry_hex']:
        return row['entry_hex']
    return '|'.join(row.get(k,'') for k in ['tile','palette','priority','hflip','vflip'])

def main():
    rows=list(csv.DictReader(sys.stdin))
    grid={}
    for r in rows:
        try: grid[(int(r['tx']),int(r['ty']))]=key_for(r)
        except Exception: pass
    c=Counter()
    for (x,y),v in grid.items():
        if (x+1,y) in grid and (x,y+1) in grid and (x+1,y+1) in grid:
            mt=(v,grid[(x+1,y)],grid[(x,y+1)],grid[(x+1,y+1)])
            c[mt]+=1
    print('metatile_id,count,entry00_hex,entry01_hex,entry10_hex,entry11_hex,notes')
    for idx,(mt,count) in enumerate(c.most_common(),1):
        print(f'mt_{idx:04d},{count},{mt[0]},{mt[1]},{mt[2]},{mt[3]},')

if __name__=='__main__': main()
