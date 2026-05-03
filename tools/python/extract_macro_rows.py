#!/usr/bin/env python3
from pathlib import Path
import csv, argparse

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('rom', type=Path)
    ap.add_argument('--start', type=lambda x:int(x,0), default=0x39850)
    ap.add_argument('--count', type=int, default=32)
    ap.add_argument('--out', type=Path, default=Path('macro_rows.csv'))
    args=ap.parse_args()
    rom=args.rom.read_bytes()
    rows=[]
    for i in range(args.count):
        off=args.start+i*9
        b=rom[off:off+9]
        if len(b)<9: break
        word=b[7] | (b[8]<<8)
        rows.append({
            'row_index':i,
            'file_pc':f'0x{off:06X}',
            'bytes':b.hex(' '),
            'slot3_word_le':f'{word:04X}',
            'lorom_label_if_bank87':f'$87:{word:04X}' if 0x8000 <= word <= 0xFFFF else ''
        })
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['row_index','file_pc','bytes','slot3_word_le','lorom_label_if_bank87'])
        w.writeheader(); w.writerows(rows)
if __name__=='__main__': main()
