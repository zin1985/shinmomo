#!/usr/bin/env python3
"""Fail-closed VM entry reachability using exact CFG functions from the canonical catalog.

Avoid duplicating the proven opcode grammar: AST-import only the trusted,
self-contained nested CFG functions, initialization, and literal safe lengths.
Only derived addresses/diagnostics are written, never ROM bytes.
"""
from __future__ import annotations
import ast
import csv
import hashlib
import json
import sys
from collections import deque
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"tools/python"))
import catalog_map_selectors as cms

ROM_SHA="F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"
SOURCE=ROOT/"tools/python/catalog_map_transition_candidates.py"
CSV=ROOT/"data/maps/transitions/vm56_source_ownership_audit.json"
FRAME_XREF=ROOT/"data/events/event_source_crosslink.csv"
OUTPUT=ROOT/"data/maps/transitions/vm56_entry_cfg_frontier.json"


def file_offset(addr):
    a,b=addr.split(":")
    bank=int(a,16)
    if not 0xC0<=bank<=0xFF:raise ValueError(addr)
    return ((bank-0xC0)<<16)|int(b,16)


def cpu_addr(offset):
    return f"{0xC0+(offset>>16):02X}:{offset&0xFFFF:04X}"


def make_reachability(rom, entries, *, include_return_checker=False):
    """Reuse original proven CFG opcode grammar; no text-scraping of instruction lengths."""
    tree=ast.parse(SOURCE.read_text(encoding="utf-8"),filename=str(SOURCE))
    main=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="main")
    wanted_functions={
        "signed8", "cfg_ptr_file", "cfg_bound_for", "cfg_opcode_length",
        "cfg_prove_return", "cfg_target_reachability",
    }
    parts=[]
    for node in main.body:
        if isinstance(node,ast.Assign) and any(
            isinstance(t,ast.Name) and t.id=="cfg_safe_lengths" for t in node.targets
        ):
            parts.append(node)
        elif isinstance(node,ast.For) and isinstance(node.target,ast.Name) and node.target.id=="_op":
            parts.append(node)
        elif isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and isinstance(node.value.func.value,ast.Name) and node.value.func.value.id=="cfg_safe_lengths" and node.value.func.attr=="update":
            parts.append(node)
        elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name) and node.target.id in {"cfg_return_memo","cfg_return_visiting"}:
            parts.append(node)
        elif isinstance(node,ast.FunctionDef) and node.name in wanted_functions:
            parts.append(node)
    extracted={node.name for node in parts if isinstance(node,ast.FunctionDef)}
    if extracted!=wanted_functions or not (10 <= len(parts) <= 15):
        raise RuntimeError(f"CFG source AST shape changed: functions={extracted} nodes={len(parts)}")
    ns=dict(rom=rom,cfg_entries=entries,deque=deque,set=set,dict=dict,len=len,range=range)
    module=ast.fix_missing_locations(ast.Module(body=parts,type_ignores=[]))
    code=compile(module,str(SOURCE),"exec")
    exec(code,ns,ns)
    if include_return_checker:
        return ns["cfg_target_reachability"],ns["cfg_opcode_length"],ns["cfg_prove_return"]
    return ns["cfg_target_reachability"],ns["cfg_opcode_length"]


def investigate(rom, audit, xrefs, max_targets=None):
    entries=[]
    packs={}
    for pack_id in range(cms.FIRST_REAL_PACK,cms.LAST_REAL_PACK+1):
        pack=cms.parse_pack(rom,pack_id)
        if not pack:continue
        packs[pack_id]=pack
        for rec in pack["records"]:
            if (pack_id,rec["record_index"]) in cms.EXCLUDED_NON_VM_RECORDS:continue
            header=cms.parse_record_header(rom,rec)
            if not header:continue
            for e in header["entries"]:
                entries.append((e["start"],e["end"],pack_id,rec["record_index"],e["entry_id"]))
    reach,op_len,return_checker=make_reachability(rom,entries,include_return_checker=True)
    xrefs_by_record={}
    for x in xrefs:xrefs_by_record.setdefault(x["record_id"],[]).append(x)
    out=[]
    for item in audit["owner_trace_queue"][:max_targets]:
        packid=int(item["script_pack"],16)
        record=int(item["script_record"])
        entryid=int(item["script_entry"],16)
        addr=item["trigger_addr"]
        off=file_offset(addr)
        matches=[e for e in entries if e[2]==packid and e[3]==record and e[4]==entryid and e[0]<=off and off+4<=e[1]]
        if len(matches)!=1:raise ValueError(f"Unbounded or ambiguous entry at {addr}: {matches}")
        start,end,_,_,_=matches[0]
        body=rom[start:end]
        reachable,blockers=reach(body,start,off-start)
        scheduled_resume=None
        if addr=="CC:F4F9":
            # Exact opcode 0x25 0x01 is in this parsed entry at CC:F47A.
            # The normal VM handler C4:9517 queues C4:9535 via 80:AC1E.
            # Its callback advances two bytes, but scheduler dispatch
            # at runtime is not guaranteed by static CFG reachability.
            resume_addr="CC:F47A"
            site=file_offset(resume_addr)
            if rom[site:site+2]!=bytes([0x25,0x01]) or not start<=site<off:
                raise ValueError("Deferred opcode 0x25 proof site changed")
            before_resume,resume_blockers=reach(body,start,site-start)
            if not before_resume:
                raise ValueError(f"Scheduler registration site not CFG reachable: {resume_blockers}")
            scheduled_resume={
                "registration_opcode_addr":resume_addr,
                "normal_vm_handler":"C4:9517",
                "scheduler":"80:AC1E",
                "deferred_callback":"C4:9535",
                "callback_vm_advance":2,
                "registration_path_cfg_possible":True,
                "callback_executed_in_runtime":False,
                "continuation_requires_scheduler":True,
            }
        # Classify unresolved nested calls against independently parsed entry
        # bounds. A matching entry is a possible research target, never proof
        # that the callee returns.
        unresolved_callees=[]
        for reason in sorted(blockers):
            if not reason.startswith(("A0:","B1:")):
                continue
            op,bank,low=reason.split(":")
            ptr=file_offset(bank+":"+low)
            hosts=[e for e in entries if e[0]<=ptr<e[1]]
            return_ok, return_seen, return_blockers=return_checker((int(bank,16)<<16)|int(low,16))
            unresolved_callees.append({
                "opcode":op,
                "callee_addr":bank+":"+low,
                "return_checker_static_status": "bounded_return_proven" if return_ok else "not_proven",
                "return_checker_blockers":sorted(return_blockers),
                "bounded_entry_count":len(hosts),
                "bounded_entry_candidates":[{
                    "entry_start":cpu_addr(e[0]),
                    "entry_end_exclusive":cpu_addr(e[1]),
                    "script_pack":f"0x{e[2]:02X}",
                    "record_index":e[3],
                    "entry_id":f"0x{e[4]:02X}"
                } for e in hosts[:5]],
                "callee_return_proven":bool(return_ok),
            })
        if addr=="CC:AD64":
            # Former blockers from the baseline 57acc1d audit; the handler
            # length fix must independently resolve every nested return.
            for extra in ("CA:DA86","CA:DA93","CC:AE86"):
                if any(x["callee_addr"]==extra for x in unresolved_callees):
                    continue
                bank,low=extra.split(":")
                ptr=(int(bank,16)<<16)|int(low,16)
                return_ok, return_seen, return_blockers=return_checker(ptr)
                hosts=[e for e in entries if e[0]<=file_offset(extra)<e[1]]
                unresolved_callees.append({
                    "opcode":"A0",
                    "callee_addr":extra,
                    "bounded_entry_count":len(hosts),
                    "return_checker_static_status":"bounded_return_proven" if return_ok else "not_proven",
                    "return_checker_blockers":sorted(return_blockers),
                    "callee_return_proven":bool(return_ok),
                })
        xref=xrefs_by_record.get(item["event_record"],[])
        site_meta=[]
        for x in xref:
            at=file_offset(x["script_callsite"])
            site_meta.append({
                "script_callsite":x["script_callsite"],
                "selected_source_cpu":x["selected_source_cpu"],
                "position_in_target_entry":"inside" if start<=at<end else "before" if at<start else "after",
                "rom_address_order_to_terminal":"before" if at<off else "after" if at>off else "same",
                "is_proven_vm_caller":False,
            })
        out.append({
            "trigger_addr":addr,"source_vm_pack":item["script_pack"],
            "record_index":record,"entry_id":item["script_entry"],
            "entry_start":cpu_addr(start),"entry_end_exclusive":cpu_addr(end),
            "bounded_entry_bytes":end-start,"target_offset_from_entry":off-start,
            "terminal_pattern_valid":list(rom[off:off+1])==[0x56] and rom[off+3]==0xB0,
            "entry_to_terminal_cfg_reachable":reachable,
            "static_path_class":"deferred_callback_possible" if scheduled_resume else "normal_vm_candidate_path",
            "scheduled_resume_evidence":scheduled_resume,
            "cfg_blockers":sorted(blockers),
            "unresolved_nested_callees":unresolved_callees,
            "cfg_interpretation":"Potential CFG path only, not proof runtime state, VM mode, or source map",
            "source_selection_sites":site_meta,
            "source_selections_within_entry":sum(s["position_in_target_entry"]=="inside" for s in site_meta),
            "source_map_identified":False,
        })
    return {"schema_version":1,"kind":"vm56_entry_cfg_frontier",
            "canonical_rom_sha256":ROM_SHA,"cfg_grammar_reused_from":"tools/python/catalog_map_transition_candidates.py",
            "targets_audited":len(out),"targets":out,
            "promotion_policy":"No player source map inferred from source selections, script pack, or a possible VM CFG path."}


def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--rom",type=Path,required=True)
    ap.add_argument("--output",type=Path,default=OUTPUT)
    args=ap.parse_args()
    rom=args.rom.read_bytes()
    if len(rom)!=2097152 or hashlib.sha256(rom).hexdigest().upper()!=ROM_SHA:
        raise SystemExit("Canonical ROM identity mismatch")
    audit=json.loads(CSV.read_text(encoding="utf-8"))
    with FRAME_XREF.open(encoding="utf-8-sig",newline="") as f:xrefs=list(csv.DictReader(f))
    report=investigate(rom,audit,xrefs)
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    for t in report["targets"]:
        print(json.dumps({k:v for k,v in t.items() if k!="source_selection_sites"},ensure_ascii=False))


if __name__=="__main__":
    main()
