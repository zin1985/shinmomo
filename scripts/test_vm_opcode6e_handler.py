#!/usr/bin/env python3
"""Evidence and negative mutation tests for 65816 VM 0x6E handler."""
from __future__ import annotations
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from verify_vm_opcode6e_handler import check_handler

class Opcode6eEvidenceTests(unittest.TestCase):
    def fixture(self):
        rom=bytearray(0x50000)
        def write_at(ad,value):rom[0x40000+ad:0x40000+ad+len(value)]=value
        for code,handler in [(0x53,0x8B3F),(0x56,0x8B6A),(0x6E,0x93A9)]:
            write_at(0x87D4+2*code,handler.to_bytes(2,"little"))
        write_at(0x93A9,bytes.fromhex("B7 98 48 22 E8 B3 81 AA BC D9 05 68"))
        write_at(0x93B5,bytes.fromhex("F0 14 C9 FF D0 02 A9 00 22 88 AE 80 BD 59 07 09 08 9D 59 07 80 0A"))
        write_at(0x93CB,bytes.fromhex("BD 59 07 29 F7 09 10 9D 59 07"))
        write_at(0x93D5,bytes.fromhex("4C 5E 89"))
        write_at(0x895E,bytes.fromhex("A9 02 4C 10 84"))
        return rom

    def test_proven_signature(self):
        out=check_handler(self.fixture())
        self.assertEqual(out["handler"],"C4:93A9")
        self.assertEqual(out["vm_advance_bytes"],2)
        self.assertIn("0x6E",out["control_opcodes"])

    def test_wrong_handler_pointer_fails_closed(self):
        rom=self.fixture()
        rom[0x40000+0x87D4+0x6E*2]=0x00
        with self.assertRaisesRegex(ValueError,"dispatch mismatch"):
            check_handler(rom)

    def test_wrong_handler_branch_fails_closed(self):
        rom=self.fixture()
        rom[0x40000+0x93B5]=0x80 # replace proven BEQ
        with self.assertRaisesRegex(ValueError,"handler byte signature mismatch"):
            check_handler(rom)

    def test_wrong_common_advance_fails_closed(self):
        rom=self.fixture()
        rom[0x40000+0x895F]=0x03
        with self.assertRaisesRegex(ValueError,"handler byte signature mismatch"):
            check_handler(rom)

if __name__=="__main__":unittest.main()
