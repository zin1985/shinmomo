#!/usr/bin/env python3
"""Negative mutation tests for normal VM 0x02 selector 0x13 static return."""
from __future__ import annotations
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from verify_vm_opcode02_13_handler import verify

class Opcode0213HandlerTests(unittest.TestCase):
    def fixture(self):
        rom=bytearray(0x50000)
        def write(address,payload):
            off=0x40000+address
            rom[off:off+len(payload)]=payload
        write(0x87D4+4,bytes.fromhex("A5 89"))
        write(0x89A5,bytes.fromhex("B7 98 C2 30 29 FF 00 3A 85 00 0A 65 00 AA BD EE 9B 85 2A BD EF 9B 85 2B E2 30 20 5E 89 22 C7 89 84 60 DC 2A 00"))
        write(0x9C24,bytes.fromhex("AB BB 83"))
        # 83:BBAB high-half mapped into ROM as bank C3.
        rom[0x3BBAB:0x3BBAB+17]=bytes.fromhex("EE 68 12 C2 20 A9 BC BB 85 0F E2 20 22 14 AC 80 6B")
        return rom

    def test_verified_operand13_pointer_and_rtl(self):
        r=verify(self.fixture())
        self.assertEqual(r["target"],"83:BBAB")
        self.assertEqual(r["operand_bytes_including_opcode"],2)

    def test_wrong_table_pointer_fails(self):
        r=self.fixture();r[0x49C24]=0xAC
        with self.assertRaisesRegex(ValueError,"dispatch pointer mismatch"):
            verify(r)

    def test_wrong_target_rtl_fails(self):
        r=self.fixture();r[0x3BBAB+16]=0x60
        with self.assertRaisesRegex(ValueError,"target RTL signature"):
            verify(r)

    def test_wrong_dispatch_table_opcode_fails(self):
        r=self.fixture();r[0x487D8]=0x00
        with self.assertRaisesRegex(ValueError,"handler mismatch"):
            verify(r)

if __name__=="__main__": unittest.main()
