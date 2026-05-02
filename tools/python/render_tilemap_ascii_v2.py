#!/usr/bin/env python3
"""Render tilemap CSV as aligned ASCII tile ids."""
import sys, csv
path = sys.argv[1] if len(sys.argv)>1 else None
f = open(path, newline='', encoding='utf-8-sig') if path else sys.stdin
try:
    for line in f:
        line=line.strip()
        if not line or line.startswith('#'): continue
        vals=[]
        for tok in line.replace('\t',',').split(','):
            tok=tok.strip()
            if tok:
                vals.append(int(tok,0))
        if vals:
            print(' '.join(f'{v:03X}' for v in vals))
finally:
    if path: f.close()
