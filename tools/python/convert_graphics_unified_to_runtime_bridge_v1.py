#!/usr/bin/env python3
"""Convert graphics unified polling CSV to normalized runtime bridge CSV."""
import csv, sys

IN_COLS = ["frame","bg_hash0","bg_hash1","bg_hash2","cgram_hash","oam_hash","obj_head","obj_count","obj_chain_hash","oam_visible_count"]
OUT_COLS = ["frame","scene_tag","bg_hash","cgram_hash","oam_hash","obj_head","obj_count","obj_chain_hash","oam_visible_count","scene_change_flag","object_change_flag","graphics_state_tag","notes"]

def main():
    r = csv.DictReader(sys.stdin)
    w = csv.DictWriter(sys.stdout, fieldnames=OUT_COLS)
    w.writeheader()
    prev_bg = prev_oam = prev_obj = None
    for row in r:
        bg = f"{row.get('bg_hash0','')}:{row.get('bg_hash1','')}:{row.get('bg_hash2','')}"
        oam = row.get('oam_hash','')
        obj = row.get('obj_chain_hash','')
        scene_changed = (prev_bg is not None and bg != prev_bg)
        object_changed = (prev_oam is not None and (oam != prev_oam or obj != prev_obj))
        if scene_changed and object_changed:
            tag = 'full_transition'
        elif scene_changed:
            tag = 'bg_transition'
        elif object_changed:
            tag = 'stable_bg_object_motion'
        else:
            tag = 'stable_bg_stable_obj'
        w.writerow({
            'frame': row.get('frame',''),
            'scene_tag': 'unknown',
            'bg_hash': bg,
            'cgram_hash': row.get('cgram_hash',''),
            'oam_hash': oam,
            'obj_head': row.get('obj_head',''),
            'obj_count': row.get('obj_count',''),
            'obj_chain_hash': obj,
            'oam_visible_count': row.get('oam_visible_count',''),
            'scene_change_flag': int(scene_changed),
            'object_change_flag': int(object_changed),
            'graphics_state_tag': tag,
            'notes': ''
        })
        prev_bg, prev_oam, prev_obj = bg, oam, obj

if __name__ == '__main__':
    main()
