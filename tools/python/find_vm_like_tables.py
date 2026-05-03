#!/usr/bin/env python3
"""Heuristic search for VM-like dispatch tables.

This does not prove a command table. It flags candidate dense byte maps and 16-bit pointer tables.
"""
from pathlib import Path
import argparse, csv, statistics

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('rom', type=Path)
    ap.add_argument('--bank', type=lambda x:int(x,0), default=0x87)
    ap.add_argument('--out', type=Path, default=Path('vm_like_tables.csv'))
    args=ap.parse_args()
    rom=args.rom.read_bytes()
    start=(args.bank-0x80)*0x8000
    data=rom[start:start+0x8000]
    rows=[]
    # dense low-value byte windows
    for i in range(0,len(data)-64):
        win=data[i:i+64]
        low=sum(1 for b in win if b <= 0x40)
        uniq=len(set(win))
        if low >= 56 and 4 <= uniq <= 40:
            rows.append({'type':'dense_low_byte_window','snes':f'${args.bank:02X}:{0x8000+i:04X}','file_pc':f'0x{start+i:06X}','score':low,'detail':win.hex(' ')})
    # pointer-ish tables to bank87/bank80 style high bytes not included; 16-bit target >=8000 every 2 bytes
    for i in range(0,len(data)-32,2):
        vals=[data[i+j] | (data[i+j+1]<<8) for j in range(0,32,2)]
        inbank=sum(1 for v in vals if 0x8000 <= v <= 0xFFFF)
        if inbank >= 12:
            rows.append({'type':'word_pointerish_window','snes':f'${args.bank:02X}:{0x8000+i:04X}','file_pc':f'0x{start+i:06X}','score':inbank,'detail':' '.join(f'{v:04X}' for v in vals)})
    rows.sort(key=lambda r:(r['type'],-int(r['score']),r['file_pc']))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['type','snes','file_pc','score','detail'])
        w.writeheader(); w.writerows(rows)
if __name__=='__main__': main()
