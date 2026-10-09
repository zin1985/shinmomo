#!/usr/bin/env python3
"""Verify normal-mode VM opcode 0x6E handler and two-byte dispatch advancement.

ROM opcode table C4:87D4 is indexed by 2*opcode. Verified 0x6E
destination is C4:93A9. Both conditional sides join C4:93D5,
which jumps to C4:895E (LDA #2; JMP C4:8410).
This is a static pointer/length proof, not reachability or VM mode proof.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

SHA="F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"
SIZE=2097152
def at(rom, address):
    return rom[0x40000+address:0x40000+address+24]

def check_handler(rom):
    table=0x40000+0x87D4
    expected={0x53:0x8B3F,0x56:0x8B6A,0x6E:0x93A9}
    real={f"0x{k:02X}": f"C4:{int.from_bytes(rom[table+2*k:table+2*k+2],'little'):04X}" for k in expected}
    for code,target in expected.items():
        actual=int.from_bytes(rom[table+2*code:table+2*code+2],"little")
        if actual!=target: raise ValueError(f"VM dispatch mismatch: opcode {code:02X} -> {actual:04X}")
    # Mainline before the BEQ, BEQ target, BRA merge, and JMP to the
    # common VM-pointer advance. This validates all in-handler branch
    # targets without having to assume source VM map state.
    direct={
        0x93A9:bytes.fromhex("B7 98 48 22 E8 B3 81 AA BC D9 05 68"),
        0x93B5:bytes.fromhex("F0 14 C9 FF D0 02 A9 00 22 88 AE 80 BD 59 07 09 08 9D 59 07 80 0A"),
        0x93CB:bytes.fromhex("BD 59 07 29 F7 09 10 9D 59 07"),
        0x93D5:bytes.fromhex("4C 5E 89"),
        0x895E:bytes.fromhex("A9 02 4C 10 84"),
    }
    for address,pattern in direct.items():
        offset=0x40000+address
        if rom[offset:offset+len(pattern)]!=pattern:
            raise ValueError(f"Normal VM 6E handler byte signature mismatch: C4:{address:04X}")
    assert (0x93B5+2+0x14)==0x93CB
    assert (0x93C9+2+0x0A)==0x93D5
    assert (0x93B9+2+2)==0x93BD
    return {
        "status":"validated_static_normal_vm_handler_signature",
        "opcode":"0x6E",
        "normal_vm_dispatch_table":"C4:87D4",
        "control_opcodes":real,
        "handler":"C4:93A9",
        "branch_join":"C4:93D5",
        "common_pointer_advance":"C4:895E",
        "vm_advance_bytes":2,
        "control_branch_condition":"BEQ +0x14; BNE +0x02; BRA +0x0A",
        "unproven":"Actual $1398 VM mode, active $0305 map, runtime callee return, instruction reachability",
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--rom",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path(__file__).resolve().parents[2]/"data/maps/transitions/vm_opcode6e_handler_proof.json")
    args=p.parse_args()
    rom=args.rom.read_bytes()
    if len(rom)!=SIZE or hashlib.sha256(rom).hexdigest().upper()!=SHA:
        raise SystemExit("Canonical ROM identity failed")
    data=check_handler(rom)
    data["rom_sha256"]=SHA
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(data,ensure_ascii=False))

if __name__=="__main__":main()
