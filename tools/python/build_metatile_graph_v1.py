#!/usr/bin/env python3
"""Build metatile adjacency graph from a reconstructed or observed metatile grid CSV.

Input CSV columns required: scene,x,y,metatile_id
Output CSV: scene,from_metatile_id,to_metatile_id,direction,frequency,confidence,notes
"""
import csv, argparse
from collections import Counter, defaultdict

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input_csv')
    ap.add_argument('output_csv')
    args = ap.parse_args()
    grids = defaultdict(dict)
    with open(args.input_csv, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            scene = row.get('scene','unknown')
            x, y = int(row['x']), int(row['y'])
            grids[scene][(x,y)] = row['metatile_id']
    counts = Counter()
    for scene, grid in grids.items():
        for (x,y), mt in grid.items():
            for dx,dy,d in [(1,0,'right'),(0,1,'down'),(-1,0,'left'),(0,-1,'up')]:
                nb = grid.get((x+dx,y+dy))
                if nb is not None:
                    counts[(scene,mt,nb,d)] += 1
    with open(args.output_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['scene','from_metatile_id','to_metatile_id','direction','frequency','confidence','notes'])
        for (scene,a,b,d), n in sorted(counts.items()):
            w.writerow([scene,a,b,d,n,1.0,''])
if __name__ == '__main__':
    main()
