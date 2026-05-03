#!/usr/bin/env python3
from pathlib import Path
import csv, argparse

def lorom_pc(bank:int, addr:int)->int:
    return (bank-0x80)*0x8000 + (addr-0x8000)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('rom', type=Path)
    ap.add_argument('--out', type=Path, default=Path('bank87_0759_0799_xrefs.csv'))
    args=ap.parse_args()
    rom=args.rom.read_bytes()
    bank=0x87
    start=lorom_pc(bank,0x8000); data=rom[start:start+0x8000]
    patterns={
        'STA_0759_X': bytes.fromhex('9d 59 07'),
        'STA_0799_X': bytes.fromhex('9d 99 07'),
        'LDA_0759_X': bytes.fromhex('bd 59 07'),
        'LDA_0799_X': bytes.fromhex('bd 99 07'),
        'DEC_0799_X': bytes.fromhex('de 99 07'),
        'INC_0799_X': bytes.fromhex('fe 99 07'),
        'STZ_0799_X': bytes.fromhex('9e 99 07'),
    }
    rows=[]
    for name,pat in patterns.items():
        i=0
        while True:
            j=data.find(pat,i)
            if j<0: break
            off=start+j; addr=0x8000+j
            rows.append({
                'kind':name,
                'snes':f'$87:{addr:04X}',
                'file_pc':f'0x{off:06X}',
                'context_hex':rom[max(0,off-16):off+32].hex(' ')
            })
            i=j+1
    rows.sort(key=lambda r:(r['file_pc'],r['kind']))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['kind','snes','file_pc','context_hex'])
        w.writeheader(); w.writerows(rows)
if __name__=='__main__': main()
