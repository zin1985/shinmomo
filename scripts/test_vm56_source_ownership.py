#!/usr/bin/env python3
"""Regression tests for ROM-proven VM 0x56 terminal inventory and callsite audit."""
import sys
import unittest
import hashlib
from unittest.mock import patch
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from audit_vm56_source_ownership import audit, read_csv, file_offset


def row(addr="CC:1234",pack="0x70",entry="0x03",source=""):
    return {"trigger_type":"vm_opcode_0x56_terminal","trigger_addr":addr,
            "destination_pack":pack,"destination_entry_id":entry,
            "source_config_id":source,"event_record":"", "script_pack":"0x70",
            "script_record":"1","script_entry":"0x02",
            "destination_config_id":"cfg_target"}


class Vm56AuditTests(unittest.TestCase):
    def test_rom_matches_terminal_bytes(self):
        rom=bytearray(2097152)
        off=file_offset("CC:1234")
        rom[off:off+4]=bytes([0x56,0x70,0x03,0xB0])
        with patch("audit_vm56_source_ownership.EXPECTED_SHA", hashlib.sha256(rom).hexdigest().upper()):
            result=audit([row()],[],[],bytes(rom))
        self.assertEqual(result["byte_exact_terminal_56_operands_b0_verified"],1)
        self.assertEqual(result["rom_validation_issues"],[])

    def test_tampered_opcode_fails(self):
        rom=bytearray(2097152)
        off=file_offset("CC:1234")
        rom[off:off+4]=bytes([0x56,0x70,0x04,0xB0])
        with patch("audit_vm56_source_ownership.EXPECTED_SHA", hashlib.sha256(rom).hexdigest().upper()):
            result=audit([row()],[],[],bytes(rom))
        self.assertEqual(result["byte_exact_terminal_56_operands_b0_verified"],0)
        self.assertEqual(result["rom_validation_issues"][0]["error"],"ROM_opcode_tail_mismatch")

    def test_address_validation(self):
        for value in ["80:1234","GG:1234","C0:0000:0000","FF:FFFF"]:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    file_offset(value)

    def test_frame_with_one_validated_source_selection_is_just_a_lead(self):
        e=row()
        e["event_record"]="F70-L001"
        frame={"record_id":"F70-L001","record_start":"CC:1200",
               "record_end_exclusive":"CC:1400"}
        selected={"record_id":"F70-L001","script_callsite":"CC:1300",
                  "selected_source_cpu":"C9:0020","subindex_hex":"0x01",
                  "evidence_class":"validated_source_selection_in_structural_record"}
        result=audit([e],[frame],[selected],None,[e])
        self.assertEqual(result["counts"]["frame_plus_source_selection"],1)
        self.assertEqual(result["counts"]["source_unbound_in_viewer"],1)
        self.assertEqual(result["owner_trace_queue"][0]["viewer_source_config_id"],None)
        self.assertEqual(e["source_config_id"],"")

    def test_invalid_event_record_containment_flagged(self):
        e=row()
        e["event_record"]="F70-L001"
        result=audit([e],[{"record_id":"F70-L001","record_start":"CC:0100",
                           "record_end_exclusive":"CC:0200"}],[])
        self.assertEqual(result["rom_validation_issues"][0]["error"],"trigger_outside_declared_record")

    def test_current_catalog_frame_links_are_consistent(self):
        c=read_csv(ROOT/"data/maps/transitions/map_transition_candidates.csv")
        frames=read_csv(ROOT/"data/events/event_record_frame_catalog.csv")
        x=read_csv(ROOT/"data/events/event_source_crosslink.csv")
        report=audit(c,frames,x)
        self.assertFalse(report["rom_validation_issues"],report["rom_validation_issues"][:5])
        self.assertEqual(report["terminal_0x56_total"],722)
        self.assertEqual(report["counts"]["within_structural_event_frame"],10)
        self.assertEqual(report["counts"]["frame_plus_source_selection"],7)
        self.assertEqual(report["counts"]["no_event_frame"],712)


if __name__=="__main__":
    unittest.main()
