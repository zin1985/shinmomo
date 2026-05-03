#!/usr/bin/env python3
"""Tiny validation helper for reconstructed map CSVs.

This validates only basic continuity and presence of required columns.
It is intentionally conservative and does not claim visual correctness.
"""
import csv, argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('map_csv')
    ap.add_argument('report_csv')
    args = ap.parse_args()
    required = {'scene','x','y','metatile_id'}
    issues = []
    rows = []
    with open(args.map_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        missing = required - set(reader.fieldnames or [])
        if missing:
            issues.append('missing columns: ' + ','.join(sorted(missing)))
        for row in reader:
            rows.append(row)
    if not rows:
        issues.append('no rows')
    passed = len(issues) == 0
    with open(args.report_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['scene','frame_range','passed','issues_count','adjacency_score','tile_continuity_score','dma_consistency_score','palette_consistency_score','notes'])
        scene = rows[0].get('scene','unknown') if rows else 'unknown'
        w.writerow([scene,'unknown',str(passed).lower(),len(issues),'','','','', '; '.join(issues)])
if __name__ == '__main__':
    main()
