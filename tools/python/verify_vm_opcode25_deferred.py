#!/usr/bin/env python3
"""Normal VM opcode 0x25 deferred-resume evidence, without runtime assumptions.

C4:9517 schedules C4:9535 via task registrar 80:AC1E and returns
synchronously. If the scheduler later invokes C4:9535, it advances the
VM script pointer by two bytes through C4:895E. This is a *possible*
asynchronous continuation, not proof of callback execution/flag state.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
SHA="F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"
SIZE=2097152

def verify(rom):
    if len(rom)<0x50000:raise ValueError("ROM too short for bank C4")
    def sig(bank,addr,pattern):
        b=bytes.fromhex(pattern)
        p=(bank-0xC0)*0x10000+addr
        if rom[p:p+len(b)]!=b:
            raise ValueError(f"Signature mismatch at {bank:02X}:{addr:04X}")
    sig(0xC4,0x87D4+0x25*2,"17 95")
    # Entry increments task context; queues $0F=$9535, $0D=$32;
    # JSL $80:AC1E, then saves task state, and ends with RTS.
    sig(0xC4,0x9517,"EE 68 12 C2 20 A9 35 95 85 0F E2 20 A9 32 85 0D 22 1E AC 80 20 57 87 B7 98 22 9F A1 81 60")
    sig(0xC4,0x9535,"22 61 87 84 22 93 A5 84 CE 68 12 20 5E 89 22 35 AD 80 6B")
    sig(0xC4,0x895E,"A9 02 4C 10 84")
    # The scheduler uses caller-bank registration; this signature must
    # match the independently documented registration routine.
    sig(0xC0,0xAC1E,"A3 03 85 11 A5 0D 5A DA 85 68")
    return {
        "schema_version":1,
        "status":"verified_normal_vm_deferred_callback_continuation",
        "opcode":"0x25",
        "normal_handler":"C4:9517",
        "scheduler":"80:AC1E",
        "registered_callback":"C4:9535",
        "callback_pointer_register":"$0F/$10",
        "callback_task_type":"0x32",
        "handler_returns_early":True,
        "callback_advance_routine":"C4:895E",
        "instruction_length_after_callback":2,
        "continuation_class":"deferred_async_potential_not_synchronous",
        "actual_callback_execution_proven":False,
        "vm_normal_mode_proven":False,
        "active_source_map_proven":False,
        "rom_sha256":SHA
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--rom",type=Path,required=True)
    ap.add_argument("--output",type=Path,default=Path(__file__).resolve().parents[2]/"data/maps/transitions/vm_opcode25_deferred_proof.json")
    args=ap.parse_args()
    rom=args.rom.read_bytes()
    if len(rom)!=SIZE or hashlib.sha256(rom).hexdigest().upper()!=SHA:
        raise SystemExit("Canonical ROM SHA/size mismatch")
    r=verify(rom)
    args.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False))
if __name__=="__main__":main()
