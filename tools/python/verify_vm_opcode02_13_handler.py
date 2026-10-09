#!/usr/bin/env python3
"""Prove the concrete normal-VM 0x02 operand 0x13 dispatch/callee shape.

Normal VM table 0x02 handler C4:89A5 consumes a selector and dispatches
via three-byte pointer table C4:9BEE indexed by 3*(selector-1).
Selector 0x13 points to the C3/83 mirrored target 83:BBAB, which has a
bounded RTL return after a single JSL. This is a possible static return;
it does not prove runtime state or completion of the external JSL.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
SHA="F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"
SIZE=2097152

def verify(rom):
    offset=lambda addr:0x40000+addr
    dispatch=0x87D4+2*0x02
    if rom[offset(dispatch):offset(dispatch)+2]!=bytes.fromhex("A5 89"):
        raise ValueError("Normal VM 0x02 handler mismatch")
    # C4:89A5 selects 0x02 argument through a 3-byte table
    # at C4:9BEE: DEC A, ASL, ADC original gives 3*(arg-1);
    # JMP indirect long after C4:895E advances the VM pointer.
    handler=bytes.fromhex("B7 98 C2 30 29 FF 00 3A 85 00 0A 65 00 AA BD EE 9B 85 2A BD EF 9B 85 2B E2 30 20 5E 89 22 C7 89 84 60 DC 2A 00")
    if rom[offset(0x89A5):offset(0x89A5)+len(handler)]!=handler:
        raise ValueError("VM 0x02 selector dispatch signature changed")
    selector=0x13
    table=0x9BEE+3*(selector-1)
    ptr=rom[offset(table):offset(table)+3]
    if ptr!=bytes.fromhex("AB BB 83"):
        raise ValueError("VM 0x02/0x13 dispatch pointer mismatch")
    # Bank 83 high-half maps to canonical LoROM code mirrored in bank C3.
    target=0x30000+0xBBAB
    callee=bytes.fromhex("EE 68 12 C2 20 A9 BC BB 85 0F E2 20 22 14 AC 80 6B")
    if rom[target:target+len(callee)]!=callee:
        raise ValueError("VM 0x02/0x13 target RTL signature changed")
    return {
        "status":"validated_normal_vm_02_operand_13_static_return_shape",
        "opcode":"0x02","operand":"0x13","normal_handler":"C4:89A5",
        "table":"C4:9BEE","table_entry":"C4:9C24",
        "target":"83:BBAB","target_mirrored_rom":"C3:BBAB",
        "target_direct_return_opcode":"RTL",
        "operand_bytes_including_opcode":2,
        "unproven":"Actual VM normal mode, execution of JSL 80:AC14, player current map, story predicates and real runtime transition",
        "rom_sha256":SHA
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--rom",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path(__file__).resolve().parents[2]/"data/maps/transitions/vm_opcode02_13_proof.json")
    a=p.parse_args()
    rom=a.rom.read_bytes()
    if len(rom)!=SIZE or hashlib.sha256(rom).hexdigest().upper()!=SHA:
        raise SystemExit("Canonical ROM identity mismatch")
    data=verify(rom)
    a.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(data,ensure_ascii=False))
if __name__=="__main__":main()
