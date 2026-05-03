#!/usr/bin/env python3
"""Cluster OAM pieces into likely sprite/object units.

Priority:
1. object_id if present
2. frame + palette + region + spatial proximity buckets
"""
import argparse, csv, sys, math
from collections import defaultdict

OUT = ['cluster_id','frame','object_id','slots','tile_indices','x_min','x_max','y_min','y_max','palette','region_label','object_type','confidence','notes']

def i(v, d=0):
    try: return int(str(v), 0)
    except Exception: return d

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bucket', type=int, default=24)
    args = ap.parse_args()
    r = csv.DictReader(sys.stdin)
    groups = defaultdict(list)
    for row in r:
        frame = row.get('frame','0')
        oid = row.get('object_id','')
        pal = row.get('palette','')
        reg = row.get('region_label','unknown')
        x = i(row.get('x'), 0); y = i(row.get('y'), 0)
        if oid:
            key = (frame, 'obj', oid)
        else:
            key = (frame, 'bucket', pal, reg, x//args.bucket, y//args.bucket)
        row['_x'] = x; row['_y'] = y
        groups[key].append(row)
    w = csv.DictWriter(sys.stdout, fieldnames=OUT)
    w.writeheader()
    n = 0
    for key, rows in sorted(groups.items(), key=lambda kv: str(kv[0])):
        n += 1
        xs = [r['_x'] for r in rows]; ys = [r['_y'] for r in rows]
        tiles = [str(r.get('tile','')) for r in rows]
        slots = [str(r.get('slot','')) for r in rows]
        pals = [r.get('palette','') for r in rows if r.get('palette','')!='']
        regs = [r.get('region_label','unknown') for r in rows]
        oid = rows[0].get('object_id','')
        pal = max(set(pals), key=pals.count) if pals else ''
        reg = max(set(regs), key=regs.count) if regs else 'unknown'
        object_type = 'unknown'
        if 'ui' in reg or (ys and max(ys) > 180): object_type = 'ui_or_glyph'
        if 'object' in reg and ys and max(ys) < 180: object_type = 'actor_or_effect'
        conf = 0.85 if oid else 0.55
        w.writerow({
            'cluster_id': f'cl_{n:04d}', 'frame': rows[0].get('frame',''), 'object_id': oid,
            'slots': ';'.join(slots), 'tile_indices': ';'.join(tiles),
            'x_min': min(xs), 'x_max': max(xs)+8, 'y_min': min(ys), 'y_max': max(ys)+8,
            'palette': pal, 'region_label': reg, 'object_type': object_type,
            'confidence': f'{conf:.2f}', 'notes': ''
        })

if __name__ == '__main__':
    main()
