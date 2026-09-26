#!/usr/bin/env python3
"""Build evidence-backed Shinmomo source (family, subindex) usage catalogs.

Inputs are the canonical ROM plus the already-established source-reader model.
No full decoded text or raw ROM data is emitted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

CA_BOUNDARY_OFFSET = 0x0AC000
CA_FINAL_SENTINEL_INDEX = 0xFA
FIRST_REAL_PACK = 0x14
LAST_REAL_PACK = 0xF9

CONFIRMED_SEEDS = [
    # family, subindex, domain, visible, evidence source, details
    (0x00,0x25,"recursive_token02","unknown",
     "data/weapon_special/vol015_trace/shinmomo_vol015_dispatch_token_trace/shinmomo_vol015_dispatch_token_trace_report_20260430.md",
     "token 02 C5 -> value 25 -> family type01 fallback -> C7:0000[0], record C7:0477"),
    (0x16,0x82,"weapon_descriptor","no",
     "data/weapon_special/vol015_trace/shinmomo_vol015_dispatch_token_trace/weapon_index16_corrected_9dbb_record_skip_20260430.csv",
     "corrected 9DBB cursor C7:9EA5"),
    (0x16,0x83,"weapon_descriptor","no",
     "data/weapon_special/vol015_trace/shinmomo_vol015_dispatch_token_trace/weapon_index16_corrected_9dbb_record_skip_20260430.csv",
     "corrected 9DBB cursor C7:9EB0"),
    (0x16,0x84,"weapon_descriptor","no",
     "data/weapon_special/vol015_trace/shinmomo_vol015_dispatch_token_trace/weapon_index16_corrected_9dbb_record_skip_20260430.csv",
     "corrected 9DBB cursor C7:9EC3"),
    (0x16,0xC1,"weapon_descriptor","no",
     "data/weapon_special/vol015_trace/shinmomo_vol015_dispatch_token_trace/weapon_index16_corrected_9dbb_record_skip_20260430.csv",
     "corrected 9DBB cursor C7:A566"),
    (0x16,0xC2,"weapon_descriptor","no",
     "data/weapon_special/vol015_trace/shinmomo_vol015_dispatch_token_trace/weapon_index16_corrected_9dbb_record_skip_20260430.csv",
     "corrected 9DBB cursor C7:A57D"),
    (0x16,0xC8,"weapon_descriptor","no",
     "data/weapon_special/vol015_trace/shinmomo_vol015_dispatch_token_trace/weapon_index16_corrected_9dbb_record_skip_20260430.csv",
     "corrected 9DBB cursor C7:A64D"),
]

DIALOGUE_SEEDS = {
    (0x4E,0x15):("strong_dialogue",
        "docs/analysis/family4e_compact_vm_revalidation.md"),
    (0x4F,0x00):("confirmed_dialogue",
        "archive/previous_zip_contents/shinmomo_vol013_mode02_mass_dump_v33/shinmomo_mode02_chain_C8_A7DD_v33_sample.csv"),
    (0x4F,0x01):("strong_dialogue",
        "archive/previous_zip_contents/shinmomo_vol013_mode02_mass_dump_v33/shinmomo_mode02_chain_C8_A7DD_v33_sample.csv"),
}

VISIBLE_TEXT_SEEDS = {
    (0x4E,0x16):("strong_visible_text",
        "docs/analysis/family4e_compact_vm_revalidation.md",
        "handler-proven A4 selection plus exact retained-v33 token match; parameterized event/system text"),
}

# Explicit compact-VM A4 sites whose instruction boundaries are proven from
# the C4:809D compact interpreter and A4 handler C4:84AE. These are deliberately
# separate from the generic byte-pattern heuristics so rejected raw A4-like
# payload bytes are not reintroduced.
VM_BOUNDARY_A4_SEEDS = {
    (0x4E,0x15):("CC:1B18",
        "opcode 09 at CC:1B14 is 4 bytes; A4 handler consumes opcode+operand"),
    (0x4E,0x16):("CC:1B1E",
        "opcode 09 at CC:1B1A is 4 bytes; A4 handler consumes opcode+operand"),
}

def cpu_from_file(off: int) -> str:
    return f"{0xC0 + (off >> 16):02X}:{off & 0xFFFF:04X}"

def file_from_cpu(bank: int, addr: int) -> int:
    return ((bank - 0xC0) << 16) | addr

def read_long(rom: bytes, off: int) -> tuple[int,int,str]:
    lo, hi, bank = rom[off:off+3]
    addr = lo | (hi << 8)
    return bank, addr, f"{bank:02X}:{addr:04X}"

def load_source_module(repo: Path):
    p = repo / "tools/python/catalog_dialogue_sources.py"
    spec = importlib.util.spec_from_file_location("catalog_dialogue_sources", p)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod

def read_ca_boundaries(rom: bytes) -> list[dict]:
    rows=[]
    for idx in range(CA_FINAL_SENTINEL_INDEX+1):
        off=CA_BOUNDARY_OFFSET+idx*3
        bank,addr,ptr=read_long(rom,off)
        rows.append({"index":idx,"table_offset":off,"bank":bank,"addr":addr,"ptr":ptr})
    return rows

def write_crosswalk(rom: bytes, source_entries: list[dict], out_dir: Path) -> None:
    ca=read_ca_boundaries(rom)
    rows=[]
    for idx in range(250):
        src=source_entries[idx]
        ca_entry=ca[idx]
        reserved=idx<FIRST_REAL_PACK
        start=end=span=""
        status="source_only_reserved_ca_slot"
        if FIRST_REAL_PACK <= idx <= LAST_REAL_PACK:
            start=ca[idx]["ptr"]; end=ca[idx+1]["ptr"]
            so=file_from_cpu(ca[idx]["bank"],ca[idx]["addr"])
            eo=file_from_cpu(ca[idx+1]["bank"],ca[idx+1]["addr"])
            span=eo-so
            status="confirmed_index_key"
        rows.append({
            "family_id_dec":idx,"family_id_hex":f"0x{idx:02X}",
            "source_master_offset":f"0x{src['table_offset']:06X}",
            "source_root":f"{src['bank']:02X}:{src['addr']:04X}",
            "source_root_file":f"0x{src['root_offset']:06X}",
            "source_mode":src["mode"],
            "ca_pack_boundary_offset":f"0x{ca_entry['table_offset']:06X}",
            "script_pack_start":start,"script_pack_end":end,"script_pack_span":span,
            "ca_reserved":int(reserved),"relation_status":status,
        })
    p=out_dir/"source_family_script_pack_crosswalk.csv"
    with p.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    summary={
        "rom_sha256":hashlib.sha256(rom).hexdigest().upper(),
        "source_family_entries":250,
        "ca_boundary_entries":len(ca),
        "ca_reserved_zero_entries":FIRST_REAL_PACK,
        "ca_real_pack_intervals":LAST_REAL_PACK-FIRST_REAL_PACK+1,
        "ca_final_sentinel_index":f"0x{CA_FINAL_SENTINEL_INDEX:02X}",
        "first_pack_index":f"0x{FIRST_REAL_PACK:02X}",
        "last_pack_index":f"0x{LAST_REAL_PACK:02X}",
        "relation":"for valid CA packs 0x14..0xF9, CA pack interval index equals C7 source-family index",
        "example":{"index":"0x16","script_pack":f"{ca[0x16]['ptr']}..{ca[0x17]['ptr']}",
                   "source_root":f"{source_entries[0x16]['bank']:02X}:{source_entries[0x16]['addr']:04X}"}
    }
    (out_dir/"source_family_script_pack_crosswalk_summary.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def add_occ(uses: dict, family: int, sub: int, pattern: str, off: int):
    key=(family,sub)
    u=uses.setdefault(key,{"patterns":set(),"cpus":set(),"occ":0})
    u["patterns"].add(pattern);u["cpus"].add(cpu_from_file(off));u["occ"]+=1

def scan_script_packs(rom: bytes) -> dict:
    ca=read_ca_boundaries(rom)
    uses={}
    for family in range(FIRST_REAL_PACK,LAST_REAL_PACK+1):
        a=ca[family]; z=ca[family+1]
        start=file_from_cpu(a["bank"],a["addr"]); end=file_from_cpu(z["bank"],z["addr"])
        pack=rom[start:end]
        for i in range(len(pack)):
            if pack[i]!=0xA4 or i+2>=len(pack): continue
            if pack[i+2]==0xB0:
                add_occ(uses,family,pack[i+1],"A4_xx_B0",start+i)
            if i+3<len(pack) and pack[i+2]==0xC0 and pack[i+3]==0xB5:
                add_occ(uses,family,pack[i+1],"A4_xx_C0_B5",start+i)
            if i+5<len(pack) and pack[i+2]==0xB2 and pack[i+4]==0xA4:
                add_occ(uses,family,pack[i+1],"A4_xx_B2_dd_A4_yy:first",start+i)
                add_occ(uses,family,pack[i+5],"A4_xx_B2_dd_A4_yy:second",start+i+4)
    for (family, sub), (cpu, _details) in VM_BOUNDARY_A4_SEEDS.items():
        bank = int(cpu[0:2], 16)
        addr = int(cpu[3:7], 16)
        off = file_from_cpu(bank, addr)
        if rom[off:off+2] != bytes([0xA4, sub]):
            raise ValueError(f"VM-boundary A4 seed mismatch at {cpu}")
        add_occ(uses, family, sub, "A4_xx_VM_boundary_proven", off)
    return uses



def _parse_keyed_dispatch_table(rom: bytes, pack_start: int, pack_end: int,
                                table_off: int, max_records: int = 16):
    """Parse conservative [key][target16] records used by C4:8699.

    All targets must stay inside the current CA script pack and the table must
    terminate with key 0.  Returns None on any structural violation.
    """
    bank = 0xC0 + (table_off >> 16)
    rows = []
    p = table_off
    for _ in range(max_records):
        if p >= pack_end:
            return None
        key = rom[p]
        if key == 0:
            return rows if len(rows) >= 2 else None
        if p + 2 >= pack_end:
            return None
        target16 = rom[p + 1] | (rom[p + 2] << 8)
        target = ((bank - 0xC0) << 16) | target16
        if not (pack_start <= target < pack_end):
            return None
        rows.append((key, target))
        p += 3
    return None


def scan_keyed_dispatch_a4(rom: bytes) -> tuple[dict, dict]:
    """Find A4 commands at independently anchored keyed-dispatch targets.

    A candidate table is accepted only when:
    - a raw 09 <ptr24> occurrence points inside the same CA script pack;
    - the pointer parses as at least two [key,target16] records plus key-0;
    - every target remains inside that pack; and
    - at least one target starts with 09 <the same table pointer>, giving an
      internal state-machine/self-reference cross-check.

    Once the table is accepted, a target beginning A4 <subindex> is a command
    boundary by construction. Source-reader reachability is still required
    later by decode_requested(), so this does not revive unrestricted A4 scans.
    """
    ca = read_ca_boundaries(rom)
    uses = {}
    tables = {}
    for family in range(FIRST_REAL_PACK, LAST_REAL_PACK + 1):
        a = ca[family]
        z = ca[family + 1]
        start = file_from_cpu(a["bank"], a["addr"])
        end = file_from_cpu(z["bank"], z["addr"])
        pack_bank = a["bank"]
        seen_tables = set()
        for call in range(start, max(start, end - 3)):
            if rom[call] != 0x09:
                continue
            lo, hi, bank = rom[call + 1:call + 4]
            if bank != pack_bank:
                continue
            table_off = file_from_cpu(bank, lo | (hi << 8))
            if table_off in seen_tables or not (start <= table_off < end):
                continue
            rows = _parse_keyed_dispatch_table(rom, start, end, table_off)
            if rows is None:
                continue
            ptr_bytes = bytes([0x09, lo, hi, bank])
            self_targets = sum(rom[target:target + 4] == ptr_bytes
                               for _, target in rows)
            if self_targets == 0:
                continue
            seen_tables.add(table_off)
            table_key = (family, table_off)
            tables[table_key] = {
                "record_count": len(rows),
                "self_reference_targets": self_targets,
                "keys": [key for key, _ in rows],
                "targets": [target for _, target in rows],
            }
            for key, target in rows:
                if target + 1 >= end or rom[target] != 0xA4:
                    continue
                sub = rom[target + 1]
                add_occ(
                    uses, family, sub,
                    f"A4_xx_keyed_dispatch_target:key_{key:02X}",
                    target,
                )
    return uses, tables


def _routine_start(rom: bytes, call: int, limit: int = 220) -> int:
    start=max((call>>16)<<16,call-limit)
    for p in range(call-1,start,-1):
        if rom[p] in (0x60,0x6B):
            return p+1
    return start

def _immediate_before(rom: bytes, call: int) -> int | None:
    if call>=2 and rom[call-2]==0xA9:
        return rom[call-1]
    return None

def _latest_static_family(rom: bytes, call: int) -> tuple[int | None,str]:
    start=_routine_start(rom,call)
    pat=bytes([0x8D,0xB4,0x12])
    pos=start; last=None
    while True:
        hit=rom.find(pat,pos,call)
        if hit<0:
            break
        last=hit; pos=hit+1
    if last is None:
        return None,""
    if last>=2 and rom[last-2]==0xA9:
        return rom[last-1],cpu_from_file(last)
    if last>=4 and rom[last-4]==0xAF:
        lo,hi,bank=rom[last-3:last]
        if 0xC0<=bank<=0xDF:
            off=file_from_cpu(bank,lo|(hi<<8))
            if 0<=off<len(rom):
                return rom[off],cpu_from_file(last)
    return None,cpu_from_file(last)

def scan_direct_source_calls(rom: bytes) -> dict:
    """Exact static source pairs passed through C4:A02D/A0B9/A0C3."""
    uses={}
    targets=[
        (0xA02D,"display_token_pipeline"),
        (0xA0B9,"generic_family2_selector"),
        (0xA0C3,"generic_source_selector"),
    ]
    for target,domain in targets:
        pat=bytes([0x22,target&0xFF,(target>>8)&0xFF,0x84])
        pos=0
        while True:
            call=rom.find(pat,pos)
            if call<0:
                break
            pos=call+1
            sub=_immediate_before(rom,call)
            if target==0xA0B9:
                family=2
                family_source="wrapper_fixed_02"
            else:
                family,family_source=_latest_static_family(rom,call)
            if family is None or sub is None:
                continue
            key=(family,sub)
            row=uses.setdefault(key,{
                "domains":set(),"cpus":set(),"family_sources":set(),
                "display":False,
            })
            row["domains"].add(domain)
            row["cpus"].add(cpu_from_file(call))
            if family_source:
                row["family_sources"].add(family_source)
            if target==0xA02D:
                row["display"]=True
    return uses

def token_meta(record: list[int]) -> tuple[int,str]:
    return len(record),hashlib.sha256(bytes(record)).hexdigest()

def decode_requested(mod, rom: bytes, entries: list[dict], pairs: set[tuple[int,int]]) -> dict:
    result={}
    by_family=defaultdict(set)
    for f,s in pairs: by_family[f].add(s)
    for family_id, subs in by_family.items():
        family=entries[family_id]
        overrides={s:mod.special_override(rom,family_id,s) for s in subs}
        normal=sorted(s for s in subs if overrides[s] is None)
        if normal:
            reader=mod.make_reader(rom,family)
            wanted=set(normal); max_sub=max(normal)
            for idx in range(max_sub+1):
                before=reader.cursor()
                try:
                    rec=mod.read_logical_record(reader)
                except (EOFError, ValueError):
                    # A4-like byte patterns can occur in non-script payload.
                    # Pairs that cannot be reached by the real source reader are rejected.
                    break
                if idx in wanted:
                    count,sha=token_meta(rec)
                    result[(family_id,idx)]={
                        "selection":"normal_master",
                        "selected_source_cpu":cpu_from_file(before["src"]),
                        "token_count":count,"token_sha256":sha,
                    }
        for sub,ov in overrides.items():
            if ov is not None:
                result[(family_id,sub)]={
                    "selection":"special_override",
                    "selected_source_cpu":ov["pointer"],
                    "token_count":"","token_sha256":"",
                }
    return result

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("rom",type=Path)
    ap.add_argument("--repo",type=Path,default=Path("."))
    ap.add_argument("--out-dir",type=Path,default=Path("data/dialogue"))
    args=ap.parse_args()
    rom=args.rom.read_bytes()
    if len(rom)!=2097152: raise SystemExit("unexpected ROM size")
    mod=load_source_module(args.repo)
    entries=mod.read_master(rom)
    args.out_dir.mkdir(parents=True,exist_ok=True)
    write_crosswalk(rom,entries,args.out_dir)

    script=scan_script_packs(rom)
    keyed, keyed_tables=scan_keyed_dispatch_a4(rom)
    for key, ku in keyed.items():
        su=script.setdefault(key,{"patterns":set(),"cpus":set(),"occ":0})
        su["patterns"].update(ku["patterns"])
        su["cpus"].update(ku["cpus"])
        su["occ"] += ku["occ"]
    direct=scan_direct_source_calls(rom)
    pairs=set(script) | set(direct)
    for i in range(mod.SPECIAL_COUNT):
        pairs.add((rom[mod.SPECIAL_FAMILY_OFFSET+i],rom[mod.SPECIAL_SUBINDEX_OFFSET+i]))
    pairs.update((f,s) for f,s,*_ in CONFIRMED_SEEDS)
    pairs.update(DIALOGUE_SEEDS)
    pairs.update(VISIBLE_TEXT_SEEDS)
    pairs.update(VM_BOUNDARY_A4_SEEDS)
    decoded=decode_requested(mod,rom,entries,pairs)
    # Keep only pairs that are either statically decodable or special overrides.
    # This removes false-positive A4-like byte patterns in non-script payload.
    required_seed_pairs={(f,s) for f,s,*_ in CONFIRMED_SEEDS} | set(DIALOGUE_SEEDS)
    missing_seed=required_seed_pairs-set(decoded)
    if missing_seed:
        raise ValueError(f"confirmed seed pairs failed to decode: {sorted(missing_seed)}")
    pairs=set(decoded)

    rows=[]
    for family,sub in sorted(pairs):
        ev=[]; domains=[]; visible="unknown"; sources=[]; details=[]
        u=script.get((family,sub))
        if u:
            ev.append("high_conf_static_A4")
            domains.append("script_pack_A4_source_selection")
        du=direct.get((family,sub))
        if du:
            ev.append("confirmed_direct_source_call")
            domains.extend(sorted(du["domains"]))
        ov=mod.special_override(rom,family,sub)
        if ov:
            ev.append("defined_override"); domains.append("AE3A_special_override")
        for sf,ss,dom,vis,src,det in CONFIRMED_SEEDS:
            if (sf,ss)==(family,sub):
                ev.append("confirmed_static");domains.append(dom);visible=vis;sources.append(src);details.append(det)
        if (family,sub) in DIALOGUE_SEEDS:
            visible,src=DIALOGUE_SEEDS[(family,sub)]
            domains=[d for d in domains if d!="script_pack_A4_source_selection"]
            domains.append("dialogue_script_A4_source_selection")
            sources.append(src)
        if (family,sub) in VISIBLE_TEXT_SEEDS:
            visible,src,det=VISIBLE_TEXT_SEEDS[(family,sub)]
            sources.append(src)
            details.append(det)
        if (family,sub) in VM_BOUNDARY_A4_SEEDS:
            _cpu,det=VM_BOUNDARY_A4_SEEDS[(family,sub)]
            ev.append("confirmed_vm_boundary_A4")
            sources.append("docs/analysis/family4e_compact_vm_revalidation.md")
            details.append(det)
        meta=decoded[(family,sub)]
        if du and du["display"] and visible=="unknown":
            visible="empty_display_source" if int(meta.get("token_count") or 0)==1 else "strong_visible_text"
        ent=entries[family]
        rows.append({
            "family_id":family,"family_hex":f"0x{family:02X}",
            "subindex":sub,"subindex_hex":f"0x{sub:02X}",
            "evidence_classes":";".join(sorted(set(ev))),
            "consumer_domains":";".join(sorted(set(domains))),
            "player_visible":visible,
            "script_pattern_hits":u["occ"] if u else 0,
            "script_callsite_count":len(u["cpus"]) if u else 0,
            "patterns":";".join(sorted(u["patterns"])) if u else "",
            "script_cpus":";".join(sorted(u["cpus"])) if u else "",
            "direct_callsite_count":len(du["cpus"]) if du else 0,
            "direct_call_cpus":";".join(sorted(du["cpus"])) if du else "",
            "direct_family_sources":";".join(sorted(du["family_sources"])) if du else "",
            "source_root":f"{ent['bank']:02X}:{ent['addr']:04X}",
            "source_mode":ent["mode"],
            "selection":meta["selection"],
            "selected_source_cpu":meta["selected_source_cpu"],
            "token_count":meta["token_count"],
            "token_sha256":meta["token_sha256"],
            "evidence_sources":";".join(sorted(set(sources))),
            "details":"; ".join(details),
        })
    with (args.out_dir/"source_pair_usage_catalog.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()));w.writeheader();w.writerows(rows)
    summary={
        "unique_usage_pairs":len(rows),
        "families_with_usage":len({r["family_id"] for r in rows}),
        "high_conf_script_pairs":sum("high_conf_static_A4" in r["evidence_classes"] for r in rows),
        "confirmed_static_pairs":sum("confirmed_static" in r["evidence_classes"] for r in rows),
        "defined_override_pairs":sum("defined_override" in r["evidence_classes"] for r in rows),
        "confirmed_direct_source_pairs":sum("confirmed_direct_source_call" in r["evidence_classes"] for r in rows),
        "display_pipeline_pairs":sum("display_token_pipeline" in r["consumer_domains"] for r in rows),
        "strong_visible_text_pairs":sum(r["player_visible"]=="strong_visible_text" for r in rows),
        "empty_display_source_pairs":sum(r["player_visible"]=="empty_display_source" for r in rows),
        "confirmed_dialogue_pairs":sum(r["player_visible"]=="confirmed_dialogue" for r in rows),
        "strong_dialogue_pairs":sum(r["player_visible"]=="strong_dialogue" for r in rows),
        "non_dialogue_confirmed_pairs":sum(r["player_visible"]=="no" for r in rows),
        "unknown_visibility_pairs":sum(r["player_visible"]=="unknown" for r in rows),
        "static_pattern_hits":sum(int(r["script_pattern_hits"]) for r in rows),
        "static_unique_callsites":len({cpu for r in rows for cpu in r["script_cpus"].split(";") if cpu}),
        "keyed_dispatch_tables":len(keyed_tables),
        "keyed_dispatch_table_families":len({family for family,_ in keyed_tables}),
        "keyed_dispatch_A4_pairs":len(keyed),
        "keyed_dispatch_A4_callsites":len({cpu for u in keyed.values() for cpu in u["cpus"]}),
    }
    (args.out_dir/"source_pair_usage_summary.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
