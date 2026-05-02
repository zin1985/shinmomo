#!/usr/bin/env python3
"""Infer a rough tilemap from adjacency counts.

This is a heuristic debug helper. Runtime BG tilemap CSV is authoritative when available.
Input: src,dst,dir,count from build_tile_adjacency_v2.py
Output: CSV grid of tile ids.
"""
import csv, sys
from collections import defaultdict, Counter

WIDTH = int(sys.argv[2]) if len(sys.argv) > 2 else 32
HEIGHT = int(sys.argv[3]) if len(sys.argv) > 3 else 32
path = sys.argv[1] if len(sys.argv) > 1 else None

right = defaultdict(Counter)
down = defaultdict(Counter)
all_counts = Counter()

f = open(path, newline='', encoding='utf-8-sig') if path else sys.stdin
try:
    rdr = csv.DictReader(f)
    for r in rdr:
        try:
            s = int(r['src'],0); d = int(r['dst'],0); cnt = int(r.get('count','1'),0)
            direc = r.get('dir','R').strip().upper()
        except Exception:
            continue
        all_counts[s] += cnt
        all_counts[d] += cnt
        if direc.startswith('R'):
            right[s][d] += cnt
        elif direc.startswith('D'):
            down[s][d] += cnt
finally:
    if path: f.close()

if not all_counts:
    sys.exit('no adjacency rows')

# Choose likely upper-left as a frequent tile with many outgoing edges.
start = max(all_counts, key=lambda t: (sum(right[t].values()) + sum(down[t].values()), all_counts[t]))
layout=[]
row_start=start
for y in range(HEIGHT):
    row=[]
    cur=row_start
    for x in range(WIDTH):
        row.append(cur)
        if right[cur]:
            cur=right[cur].most_common(1)[0][0]
    layout.append(row)
    if down[row_start]:
        row_start=down[row_start].most_common(1)[0][0]

for row in layout:
    print(','.join(str(x) for x in row))
