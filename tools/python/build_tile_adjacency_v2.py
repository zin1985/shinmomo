#!/usr/bin/env python3
"""Build tile adjacency counts from a decoded SNES BG tilemap CSV or plain tile-id grid.

Input accepted:
  - CSV with columns x,y,tile_id or tile
  - CSV with one row per map row: 1,2,3,...

Output:
  src,dst,dir,count
  where dir is R or D.
"""
import csv, sys
from collections import Counter, defaultdict
from pathlib import Path


def read_grid(path: str | None):
    f = open(path, newline='', encoding='utf-8-sig') if path else sys.stdin
    try:
        sample = f.read(4096)
        f.seek(0)
        # Dict style CSV
        if any(k in sample.splitlines()[0].lower() for k in ['tile_id','tile','x','y']):
            rdr = csv.DictReader(f)
            rows = []
            for r in rdr:
                rows.append(r)
            if not rows:
                return []
            cols = {c.lower(): c for c in rows[0].keys()}
            tile_col = cols.get('tile_id') or cols.get('tile') or cols.get('tileid')
            x_col = cols.get('x') or cols.get('col') or cols.get('screen_x')
            y_col = cols.get('y') or cols.get('row') or cols.get('screen_y')
            if tile_col and x_col and y_col:
                pts = []
                for r in rows:
                    try:
                        x = int(str(r[x_col]), 0); y = int(str(r[y_col]), 0); t = int(str(r[tile_col]), 0)
                        pts.append((x,y,t))
                    except Exception:
                        continue
                if not pts: return []
                maxx = max(x for x,_,_ in pts); maxy = max(y for _,y,_ in pts)
                grid = [[None]*(maxx+1) for _ in range(maxy+1)]
                for x,y,t in pts:
                    grid[y][x] = t
                return grid
        # Plain grid
        f.seek(0)
        grid = []
        for line in f:
            line=line.strip()
            if not line or line.startswith('#'): continue
            row=[]
            for tok in line.replace('\t',',').split(','):
                tok=tok.strip()
                if tok:
                    row.append(int(tok,0))
            if row: grid.append(row)
        return grid
    finally:
        if path: f.close()


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    grid = read_grid(path)
    counts = Counter()
    for y,row in enumerate(grid):
        for x,t in enumerate(row):
            if t is None: continue
            if x+1 < len(row) and row[x+1] is not None:
                counts[(t,row[x+1],'R')] += 1
            if y+1 < len(grid) and x < len(grid[y+1]) and grid[y+1][x] is not None:
                counts[(t,grid[y+1][x],'D')] += 1
    print('src,dst,dir,count')
    for (src,dst,d),cnt in sorted(counts.items(), key=lambda kv:(kv[0][2],-kv[1],kv[0][0],kv[0][1])):
        print(f'{src},{dst},{d},{cnt}')

if __name__ == '__main__':
    main()
