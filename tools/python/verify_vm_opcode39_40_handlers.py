#!/usr/bin/env python3
"""Static normal VM opcode 0x39/0x40 length evidence from canonical 65816 ROM.

0x39: reads one operand at Y=1; INY -> Y=2; JSR C4:841E and
JMP C4:840F advances by Y (two bytes including opcode).
0x40: reads two bytes and a fixed four-iteration loop for four more,
Y:1 -> 3 -> 7. BCC F5 repeats the loop at C4:8FC4.
BRA CC at C4:8FCF joins at C4:8F9D; JSR C4:840F advances Y=7.
Only a possible normal-mode CFG continuation, not runtime state proof.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

SHA="F6A345E2F07F0CBC4EFF7D4FF06AE88A814A98FDF100C7BF7351168C73916A98"
SIZE=2097152

def verify(rom):
    if len(rom) < 0x50000:
        raise ValueError("Insufficient ROM for C4 handlers")
    def sig(addr,hexbytes):
        b=bytes.fromhex(hexbytes)
        if rom[0x40000+addr:0x40000+addr+len(b)]!=b:
            raise ValueError(f"C4:{addr:04X} signature changed")
    for opcode,handler in ((0x39,0x9803),(0x40,0x8FB3)):
        sig(0x87D4+2*opcode,handler.to_bytes(2,'little').hex(' '))
    sig(0x9803,"B7 98 C8 22 A4 BB 80 20 1E 84 4C 0F 84")
    sig(0x8FB3,"B7 98 85 0F C8 B7 98 85 10 C8 B2 0F 8D 56 18 A2 00")
    sig(0x8FC4,"B7 98 9D 57 18 C8 E8 E0 04 90 F5 80 CC")
    sig(0x8F9D,"C2 20 A5 A4 8D 5B 18 E2 20 A5 A6 8D 5D 18 20 0F 84 22 BD AD 81 60")
    sig(0x840F,"98 18 65 98 85 98 90 06 E6 99 D0 02 E6 9A 60")
    # Relative branch target = instruction end + signed displacement
    assert 0x8FCF+(-11)==0x8FC4 # BCC F5 at C4:8FCD
    assert 0x8FD1+(-52)==0x8F9D # BRA CC at C4:8FCF
    # Branch target in 0x39 uses known JMP C4:840F (pointer update by Y=2).
    return {
        "schema_version":1,
        "status":"verified_normal_mode_static_opcode_length_and_control_flow",
        "opcode39":{"normal_handler":"C4:9803","operand_count":1,"instruction_length":2,"vm_pointer_advance":"C4:840F","external_jsl_return_unproven":"80:BBA4"},
        "opcode40":{"normal_handler":"C4:8FB3","fixed_initial_operands":2,"loop_reads":4,"loop_target":"C4:8FC4","branch_merge":"C4:8F9D","instruction_length":7,"vm_pointer_advance":"C4:840F","external_jsl_return_unproven":"81:ADBD"},
        "normal_vm_mode_required":True,
        "not_proven":"Player $0305, actual $1398 normal mode, JSL return, story predicates and real runtime visit",
        "rom_sha256":SHA
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--rom",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path(__file__).resolve().parents[2]/"data/maps/transitions/vm_opcode39_40_proof.json")
    args=p.parse_args()
    rom=args.rom.read_bytes()
    if len(rom)!=SIZE or hashlib.sha256(rom).hexdigest().upper()!=SHA:
        raise SystemExit("Canonical ROM identity mismatch")
    d=verify(rom)
    args.output.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(d,ensure_ascii=False))

if __name__=="__main__":main()
