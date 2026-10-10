#!/usr/bin/env python3
"""Fail-closed opcode 0x39/0x40 normal-VM ROM signature unit tests."""
from __future__ import annotations
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from verify_vm_opcode39_40_handlers import verify

class Handler3940Tests(unittest.TestCase):
    def fixture(self):
        rom=bytearray(0x50000)
        def put(addr,h):
            b=bytes.fromhex(h)
            rom[0x40000+addr:0x40000+addr+len(b)]=b
        put(0x87D4+2*0x39,"03 98")
        put(0x87D4+2*0x40,"B3 8F")
        put(0x9803,"B7 98 C8 22 A4 BB 80 20 1E 84 4C 0F 84")
        put(0x8FB3,"B7 98 85 0F C8 B7 98 85 10 C8 B2 0F 8D 56 18 A2 00")
        put(0x8FC4,"B7 98 9D 57 18 C8 E8 E0 04 90 F5 80 CC")
        put(0x8F9D,"C2 20 A5 A4 8D 5B 18 E2 20 A5 A6 8D 5D 18 20 0F 84 22 BD AD 81 60")
        put(0x840F,"98 18 65 98 85 98 90 06 E6 99 D0 02 E6 9A 60")
        return rom

    def test_both_lengths_verified(self):
        result=verify(self.fixture())
        self.assertEqual(result["opcode39"]["instruction_length"],2)
        self.assertEqual(result["opcode40"]["instruction_length"],7)
        self.assertIn("81:ADBD",result["opcode40"]["external_jsl_return_unproven"])

    def test_wrong_dispatch_pointer_rejected(self):
        r=self.fixture();r[0x40000+0x87D4+2*0x40]=0
        with self.assertRaisesRegex(ValueError,"signature changed"):verify(r)

    def test_wrong_loop_count_rejected(self):
        r=self.fixture();r[0x40000+0x8FCC]=5
        with self.assertRaisesRegex(ValueError,"signature changed"):verify(r)

    def test_wrong_loop_or_join_branch_rejected(self):
        for addr in (0x8FCE,0x8FD0):
            with self.subTest(addr=addr):
                r=self.fixture();r[0x40000+addr]^=1
                with self.assertRaisesRegex(ValueError,"signature changed"):verify(r)

    def test_wrong_vm_pointer_advance_rejected(self):
        r=self.fixture();r[0x40000+0x840F]=0xEA
        with self.assertRaisesRegex(ValueError,"signature changed"):verify(r)

if __name__=="__main__":unittest.main()
