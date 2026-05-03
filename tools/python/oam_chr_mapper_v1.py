#!/usr/bin/env python3
"""Map OAM tile indices to tentative VRAM CHR byte addresses.

Input CSV should contain at least: frame,slot,x,y,tile,attr
Optional columns: obj_base,name_select,size,object_id

This is intentionally conservative: OBSEL/name_select handling is exposed as
columns/arguments so that future runtime logs can make the mapping exact.
"""
import argparse, csv, sys

REGIONS = [
    (0x0000, 0x8000, 'battle_chr_0000_7fff'),
    (0x8000, 0xB000, 'battle_ui_glyph_8000_afff'),
    (0xB000, 0xC000, 'empty_b000_bfff'),
    (0xC000, 0xE000, 'battle_object_ui_c000_dfff'),
    (0xE000, 0xF000, 'empty_e000_efff'),
    (0xF000, 0x10000, 'special_f000_ffff'),
]

def i(x, default=0):
    if x is None or x == '': return default
    s = str(x).strip()
    try:
        return int(s, 0)
    except ValueError:
        return int(s, 16)

def region(addr):
    a = addr & 0xFFFF
    for lo, hi, name in REGIONS:
        if lo <= a < hi:
            return name
    return 'unknown'

def decode_attr(attr):
    a = i(attr)
    return {
        'palette': (a >> 1) & 0x07,
        'priority': (a >> 4) & 0x03,
        'hflip': (a >> 6) & 0x01,
        'vflip': (a >> 7) & 0x01,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--obj-base', type=lambda x:int(x,0), default=0, help='OBJ base unit, used as obj_base << 14')
    ap.add_argument('--name-select', type=lambda x:int(x,0), default=0, help='Name select unit, used as name_select << 13')
    args = ap.parse_args()

    r = csv.DictReader(sys.stdin)
    out_cols = ['frame','slot','tile','attr','palette','priority','hflip','vflip','size','obj_base','name_select','chr_addr_hex','region_label','object_id','notes']
    w = csv.DictWriter(sys.stdout, fieldnames=out_cols)
    w.writeheader()
    for row in r:
        tile = i(row.get('tile'))
        attr = row.get('attr','0')
        obj_base = i(row.get('obj_base'), args.obj_base)
        name_select = i(row.get('name_select'), args.name_select)
        # SNES OBJ CHR address approximation. Confirm with $2101 OBSEL.
        addr = ((obj_base << 14) + (name_select << 13) + (tile << 5)) & 0xFFFF
        d = decode_attr(attr)
        w.writerow({
            'frame': row.get('frame',''), 'slot': row.get('slot',''), 'tile': tile,
            'attr': attr, 'palette': d['palette'], 'priority': d['priority'],
            'hflip': d['hflip'], 'vflip': d['vflip'],
            'size': row.get('size','unknown'), 'obj_base': obj_base,
            'name_select': name_select, 'chr_addr_hex': f'{addr:04X}',
            'region_label': region(addr), 'object_id': row.get('object_id',''),
            'notes': ''
        })

if __name__ == '__main__':
    main()
