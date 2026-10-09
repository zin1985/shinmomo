#!/usr/bin/env python3
"""Regression coverage for exact-entry VM 0x56 CFG diagnostic reuse."""
from __future__ import annotations
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from audit_vm56_entry_cfg import make_reachability


class Vm56CfgFrontierTests(unittest.TestCase):
    def test_terminal_directly_at_entry_start(self):
        body=bytes([0x56,0x70,0x03,0xB0])
        reach,length=make_reachability(body,[(0,4,0x70,1,3)])
        self.assertEqual(length(body,0),3)
        self.assertTrue(reach(body,0,0)[0])

    def test_unknown_opcode_blocks_fail_closed(self):
        body=bytes([0x25,0x56,0x70,0x03,0xB0])
        reach,_=make_reachability(body,[(0,5,0x70,1,3)])
        found,blockers=reach(body,0,1)
        self.assertFalse(found)
        self.assertIn("op:25",blockers)

    def test_bounded_known_instruction_before_terminal(self):
        body=bytes([0xA4,0x01,0x56,0x70,0x03,0xB0])
        reach,_=make_reachability(body,[(0,6,0x70,1,3)])
        self.assertEqual(reach(body,0,2),(True,set()))

    def test_verified_opcode6e_two_byte_length(self):
        code=bytes([0x6E,0x01,0x56,0x70,0x03,0xB0])
        reach,length=make_reachability(code,[(0,len(code),0,0,0)])
        self.assertEqual(length(code,0),2)
        self.assertEqual(reach(code,0,2),(True,set()))

    def test_verified_opcode02_13_two_byte_dispatch(self):
        code=bytes([0x02,0x13,0x56,0xF9,0x03,0xB0])
        reach,length=make_reachability(code,[(0,len(code),0,0,0)])
        self.assertEqual(length(code,0),2)
        self.assertEqual(reach(code,0,2),(True,set()))

    def test_repo_frontier_recorded_without_false_source_promotion(self):
        doc=json.loads((ROOT/"data/maps/transitions/vm56_entry_cfg_frontier.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["targets_audited"],10)
        self.assertEqual(sum(r["entry_to_terminal_cfg_reachable"] for r in doc["targets"]),8)
        self.assertTrue(all(not r["source_map_identified"] for r in doc["targets"]))
        self.assertTrue(all(r["source_selections_within_entry"]==0 for r in doc["targets"]))
        self.assertEqual(doc["targets"][0]["trigger_addr"],"CC:AD64")
        self.assertEqual(doc["targets"][0]["entry_start"],"CC:AC74")
        operand13=[r for r in doc["targets"] if r["trigger_addr"]=="CE:1303"]
        self.assertEqual(len(operand13),1)
        self.assertTrue(operand13[0]["entry_to_terminal_cfg_reachable"])
        self.assertEqual(operand13[0]["cfg_blockers"],[])
        self.assertEqual(doc["targets"][0]["cfg_blockers"],[])
        callees=doc["targets"][0]["unresolved_nested_callees"]
        self.assertEqual([c["callee_addr"] for c in callees],["CA:DA86","CA:DA93","CC:AE86"])
        self.assertTrue(all(c["bounded_entry_count"]==1 for c in callees))
        self.assertTrue(all(c["callee_return_proven"] for c in callees))
        self.assertEqual(sum(r["terminal_pattern_valid"] for r in doc["targets"]),10)


if __name__=="__main__":
    unittest.main()
