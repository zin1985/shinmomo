#!/usr/bin/env python3
"""Partition validated A4 callsites outside the B0/trailer frame grammar."""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter
from pathlib import Path
EXPECTED_SIZE=2_097_152
EXPECTED_SHA256="F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"
def cpu_off(cpu):
    b,a=cpu.split(":"); return ((int(b,16)-0xC0)<<16)|int(a,16)
def read_rows(path):
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("rom",type=Path)
    ap.add_argument("--unmapped",type=Path,default=Path("data/events/event_source_unmapped_callsites.csv"))
    ap.add_argument("--keyed",type=Path,default=Path("data/events/keyed_dispatch_target_catalog.csv"))
    ap.add_argument("--out-dir",type=Path,default=Path("data/events")); a=ap.parse_args()
    rom=a.rom.read_bytes(); sha=hashlib.sha256(rom).hexdigest().upper()
    if len(rom)!=EXPECTED_SIZE or sha!=EXPECTED_SHA256: raise SystemExit("canonical ROM mismatch")
    unmapped=read_rows(a.unmapped); keyed_rows=read_rows(a.keyed)
    keyed={(int(r["family_id"]),r["target_cpu"]):r for r in keyed_rows if r.get("a4_subindex")}
    out=[]; families=Counter(); patterns=Counter(); windows=Counter()
    for r in unmapped:
        family=int(r["family_id"]); cpu=r["script_callsite"]; pos=cpu_off(cpu)
        kr=keyed.get((family,cpu)); explained=kr is not None
        window_hash=hashlib.sha256(rom[max(0,pos-8):min(len(rom),pos+10)]).hexdigest()
        row=dict(r); row.update({"keyed_dispatch_explained":int(explained),"key_hex":kr["key_hex"] if kr else "","opcode_window_sha256":window_hash}); out.append(row)
        if not explained: families[family]+=1; patterns[r["patterns"]]+=1; windows[window_hash]+=1
    residual=sum(not bool(r["keyed_dispatch_explained"]) for r in out)
    a.out_dir.mkdir(parents=True,exist_ok=True)
    with (a.out_dir/"event_source_residual_callsites.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    summary={"rom_sha256":sha,"unmapped_input":len(unmapped),"keyed_a4_intersection":len(unmapped)-residual,"residual_after_keyed":residual,
      "top_residual_families":[{"family":f"0x{x:02X}","count":n} for x,n in families.most_common(20)],
      "top_residual_patterns":[{"pattern":x,"count":n} for x,n in patterns.most_common(20)],
      "top_opcode_window_hashes":[{"sha256":x,"count":n} for x,n in windows.most_common(20)]}
    (a.out_dir/"event_source_residual_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
