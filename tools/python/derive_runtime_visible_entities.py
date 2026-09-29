#!/usr/bin/env python3
"""Derive active visible-object observations from a local-only WRAM capture."""
import argparse,json
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument("--wram",type=Path,required=True);p.add_argument("--config-id",required=True);p.add_argument("--out",type=Path,required=True);a=p.parse_args()
 m=json.loads(a.wram.read_text(encoding="utf8")); start=int(m["start"]); b=m["bytes"]
 def r(x): return b[x-start]
 chain=[]; seen=set(); s=r(0x0A61)
 while s not in (0,255) and s not in seen and len(chain)<64:
  seen.add(s); chain.append(s); s=r(0x0A61+s)
 obs=[]
 for slot in chain:
  group=r(0x0B27+slot); frame=r(0x0AE5+slot); x=r(0x0BA5+slot)|(r(0x0BE5+slot)<<8); y=r(0x0C65+slot)|(r(0x0CA5+slot)<<8)
  obs.append({"slot":slot,"sprite_group_raw":group,"sprite_group_index":group&15,"sprite_group_flags":group&240,"frame_state":frame,"x":x,"y":y,"sort_key":r(0x0AA3+slot),"renderable_frame_nonzero":frame!=0})
 doc={"schema_version":1,"kind":"runtime_visible_object_observation","frame":m["frame"],"config_id":a.config_id,"active_count_wram_0AE5":r(0x0AE5),"active_chain":chain,"active_chain_end":s,"objects":obs,"coordinate_space":"runtime object/screen coordinate; map-world transform not yet proven","confidence":"confirmed_runtime_object_state","raw_capture_committed":False}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n",encoding="utf8");print(json.dumps(doc,ensure_ascii=False))
if __name__=="__main__":main()
