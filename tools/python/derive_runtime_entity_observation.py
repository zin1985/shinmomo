#!/usr/bin/env python3
"""Derive a small, committable entity observation from local-only runtime captures."""
import argparse,json
from pathlib import Path

def read(mem, addr, n):
    start=int(mem["start"])
    if not(start <= addr and addr+n <= start+len(mem["bytes"])):
        raise ValueError(f"capture does not cover {addr:04X}+{n}")
    i=addr-start
    return mem["bytes"][i:i+n]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--wram",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    man=json.loads(a.manifest.read_text(encoding="utf8"))
    mem=json.loads(a.wram.read_text(encoding="utf8"))
    s=man["map_state"]
    ids=[]
    for value in read(mem,0x1569,10):
        if value and value not in ids: ids.append(value)
    doc={
      "schema_version":1,
      "kind":"runtime_logical_entity_observation",
      "engine_layer":"script_event_logical_actor",
      "not_a_visible_object_inventory":True,
      "frame":man["frame"],
      "map_selector":{
        "pack_id":s["current_pack_0305"],
        "variant":s["map_variant_139b"],
        "tileset_id":s["primary_tileset_139c"],
        "layout_id":s["primary_layout_139e"],
      },
      "config_id":f"cfg_t{s['primary_tileset_139c']:02d}_l{s['primary_layout_139e']:03d}_v{s['map_variant_139b']}",
      "logical_object_ids":ids,
      "logical_object_list_wram":"$1569[0..9]",
      "semantic_classification":None,
      "coordinates":None,
      "sprite_binding":None,
      "confidence":"confirmed_runtime_presence",
      "raw_capture_committed":False,
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps(doc,ensure_ascii=False))
if __name__=="__main__":main()
