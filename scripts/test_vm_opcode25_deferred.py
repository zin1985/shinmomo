#!/usr/bin/env python3
"""Fail-closed normal VM 0x25 deferred scheduler callback signatures."""
from __future__ import annotations
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from verify_vm_opcode25_deferred import verify

class Handler25Tests(unittest.TestCase):
    def fixture(self):
        rom=bytearray(0x50000)
        def put(bank,addr,h):
            b=bytes.fromhex(h)
            pos=(bank-0xC0)*0x10000+addr
            rom[pos:pos+len(b)]=b
        put(0xC4,0x87D4+2*0x25,"17 95")
        put(0xC4,0x9517,"EE 68 12 C2 20 A9 35 95 85 0F E2 20 A9 32 85 0D 22 1E AC 80 20 57 87 B7 98 22 9F A1 81 60")
        put(0xC4,0x9535,"22 61 87 84 22 93 A5 84 CE 68 12 20 5E 89 22 35 AD 80 6B")
        put(0xC4,0x895E,"A9 02 4C 10 84")
        put(0xC0,0xAC1E,"A3 03 85 11 A5 0D 5A DA 85 68")
        return rom

    def test_proven_deferred_length_never_claims_runtime(self):
        d=verify(self.fixture())
        self.assertEqual(d["registered_callback"],"C4:9535")
        self.assertEqual(d["instruction_length_after_callback"],2)
        self.assertFalse(d["actual_callback_execution_proven"])
        self.assertTrue(d["handler_returns_early"])

    def test_bad_callback_registration_rejected(self):
        r=self.fixture();r[0x40000+0x951D]^=0x01
        with self.assertRaisesRegex(ValueError,"Signature mismatch"):verify(r)

    def test_bad_scheduler_signature_rejected(self):
        r=self.fixture();r[0xAC1E]=0xFF
        with self.assertRaisesRegex(ValueError,"Signature mismatch"):verify(r)

    def test_bad_callback_return_rejected(self):
        r=self.fixture();r[0x40000+0x9547]=0x60
        with self.assertRaisesRegex(ValueError,"Signature mismatch"):verify(r)

    def test_bad_vm_pointer_advance_rejected(self):
        r=self.fixture();r[0x40000+0x895F]=0x03
        with self.assertRaisesRegex(ValueError,"Signature mismatch"):verify(r)

if __name__=="__main__":unittest.main()
