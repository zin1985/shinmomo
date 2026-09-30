#!/usr/bin/env python3
"""Catalog explicit native movement bounds attached to confirmed map selectors."""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
EXPECTED_SHA256="F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"
FIELDS=["config_id","pack_id_hex","record_index","entry_id_hex","primary_command_addr","primary_tileset_id","primary_layout_id","map_variant","bounds_opcode_addr","min_x","max_x","min_y","max_y","width_inclusive","height_inclusive","alignment_proof","confidence"]
def cpu_to_file(cpu):
    b,a=cpu.split(":",1);return ((int(b,16)-0xC0)<<16)|int(a,16)
def file_to_cpu(off):return f"{0xC0+(off>>16):02X}:{off&0xFFFF:04X}"
def walk_to_bounds(rom,command_off,stream_end):
    p=command_off+4;proof=[];stop=min(stream_end,command_off+20)
    while p<stop:
        op=rom[p]
        if op==0x52:
            if p+5>stream_end or rom[p+1]>=0xFE:return None
            vals=tuple(rom[p+1:p+5])
            if vals[0]>vals[1] or vals[2]>vals[3]:return None
            return p,vals,tuple(proof)
        if op==0x15:
            if p+3>stream_end:return None
            proof.append("0x15");p+=3;continue
        if op==0x51:
            if p+3>stream_end or not (1<=rom[p+1]<=60 and 1<=rom[p+2]<=203):return None
            proof.append("0x51_secondary_selector");p+=3;continue
        if op==0x64:
            if p+2>stream_end or rom[p+1] not in {0x00,0x24,0x70}:return None
            proof.append("0x64");p+=2;continue
        if op==0x96:
            if p+2>stream_end:return None
            proof.append("0x96");p+=2;continue
        return None
    return None
def main():
    ap=argparse.ArgumentParser();ap.add_argument("rom",type=Path)
    ap.add_argument("--selectors",type=Path,default=Path("data/maps/selectors/primary_map_selector_catalog.csv"))
    ap.add_argument("--out",type=Path,default=Path("data/maps/transitions/map_native_bounds_catalog.csv"))
    ap.add_argument("--summary",type=Path,default=Path("data/maps/transitions/map_native_bounds_summary.json"))
    args=ap.parse_args();root=Path(__file__).resolve().parents[2];rom=args.rom.read_bytes()
    got=hashlib.sha256(rom).hexdigest().upper()
    if got!=EXPECTED_SHA256:raise SystemExit(f"unexpected ROM SHA256: {got}")
    sp=args.selectors if args.selectors.is_absolute() else root/args.selectors
    rows=[];considered=0
    with sp.open(encoding="utf-8-sig",newline="") as f:
        for s in csv.DictReader(f):
            considered+=1;cmd=s["command_addr"];co=cpu_to_file(cmd);end=cpu_to_file(s["substream_end_exclusive"])
            ts=int(s["primary_tileset_id"]);lay=int(s["primary_layout_id"]);v=int(s["map_variant"])
            if rom[co:co+4]!=bytes([0x50,ts,lay,v]):raise SystemExit(f"selector bytes changed at {cmd}")
            hit=walk_to_bounds(rom,co,end)
            if hit is None:continue
            bo,vals,proof=hit;minx,maxx,miny,maxy=vals
            rows.append({"config_id":f"cfg_t{ts:02d}_l{lay:03d}_v{v}","pack_id_hex":s["pack_id_hex"],"record_index":int(s["record_index"]),"entry_id_hex":s["entry_id_hex"],"primary_command_addr":cmd,"primary_tileset_id":ts,"primary_layout_id":lay,"map_variant":v,"bounds_opcode_addr":file_to_cpu(bo),"min_x":minx,"max_x":maxx,"min_y":miny,"max_y":maxy,"width_inclusive":maxx-minx+1,"height_inclusive":maxy-miny+1,"alignment_proof":("immediate_after_primary_selector" if not proof else "after_"+"_then_".join(proof)),"confidence":"confirmed_static_opcode52_bounds"})
    rows.sort(key=lambda r:(int(r["pack_id_hex"],16),r["record_index"],int(r["entry_id_hex"],16),r["primary_command_addr"]))
    anchors={r["primary_command_addr"]:r for r in rows}
    for cmd,addr,vals in [("CC:1C3F","CC:1C46",(9,70,8,55)),("CB:DE70","CB:DE74",(0,19,0,12))]:
        r=anchors.get(cmd);got=(r["min_x"],r["max_x"],r["min_y"],r["max_y"]) if r else None
        if not r or r["bounds_opcode_addr"]!=addr or got!=vals:raise SystemExit(f"priority bounds anchor changed {cmd}")
    if len(rows)!=155:raise SystemExit(f"unexpected bounds count: {len(rows)}")
    out=args.out if args.out.is_absolute() else root/args.out;out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",encoding="utf-8-sig",newline="") as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
    by=defaultdict(set)
    for r in rows:by[r["config_id"]].add((r["min_x"],r["max_x"],r["min_y"],r["max_y"]))
    summary={"schema_version":1,"kind":"map_native_bounds_occurrence_catalog_summary","canonical_rom_sha256":EXPECTED_SHA256,"primary_selector_rows_considered":considered,"bounds_occurrence_count":len(rows),"unique_config_count":len(by),"pack_count":len({r["pack_id_hex"] for r in rows}),"configs_with_multiple_distinct_bounds":sum(len(v)>1 for v in by.values()),"alignment_proof_counts":dict(sorted(Counter(r["alignment_proof"] for r in rows).items())),"handler":{"opcode":"0x52","address":"C4:8B16","normal_form":"operand1 < 0xFE","writes":"operands 1..4 -> $15CA,$15CB,$15CC,$15CD","meaning":"inclusive native movement bounds consumed by 81:81DD via C1:8943"},"priority_examples":{"cfg_t04_l008_v2_pack_0x50":{"primary_command_addr":"CC:1C3F","bounds_opcode_addr":"CC:1C46","bounds":{"min_x":9,"max_x":70,"min_y":8,"max_y":55}},"cfg_t07_l015_v2_pack_0x2E":{"primary_command_addr":"CB:DE70","bounds_opcode_addr":"CB:DE74","bounds":{"min_x":0,"max_x":19,"min_y":0,"max_y":12}}}}
    so=args.summary if args.summary.is_absolute() else root/args.summary;so.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__":main()
