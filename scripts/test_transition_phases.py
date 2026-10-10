#!/usr/bin/env python3
"""Phase-transition classifier regression: state deltas are not opcode hits."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from audit_transition_phases import collect

from test_vm_frame_series_replays import corpus


class TransitionPhasesTests(unittest.TestCase):
    def setUp(self):
        d=corpus()
        self.a=d["world_entry"]
        self.b=d["world_settle"]

    def test_one_switch_then_delayed_settle(self):
        report=collect(self.a,self.b)
        self.assertEqual(report["source_pack"],0x4C)
        self.assertEqual(report["destination_pack"],0x50)
        self.assertEqual(report["pack_switch_frame"],663064)
        self.assertEqual(report["first_settled_arrival_frame"],663169)
        self.assertEqual(report["switch_to_settle_delay_frames"],105)
        self.assertEqual(report["settled_arrival"],{"x":29,"y":55})
        self.assertFalse(report["exact_cpu_handler_execution_proven"])
        self.assertFalse(report["new_source_map_binding_promoted"])

    def test_noncontiguous_frame_windows_rejected(self):
        self.b["before"]["frame"]+=1
        self.b["after"]["frame"]+=1
        for row in self.b["samples"]:
            row["frame"]+=1
        with self.assertRaisesRegex(ValueError,"not contiguous"):
            collect(self.a,self.b)

    def test_mismatched_state_at_boundary_rejected(self):
        self.b["before"]["w0305"]=0x2E
        with self.assertRaisesRegex(ValueError,"State changed"):
            collect(self.a,self.b)

    def test_mouse_input_not_accepted_as_settle(self):
        self.b["input_sent"]=True
        self.b["input_device"]="isolated_snes_gamepad"
        self.b["buttons"]="A"
        self.b["player"]=1
        with self.assertRaisesRegex(ValueError,"neutral settling"):
            collect(self.a,self.b)

    def test_missing_map_switch_rejected(self):
        self.a["samples"][-1]["w0305"]=0x4C
        self.a["after"]["w0305"]=0x4C
        self.b["before"]["w0305"]=0x4C
        self.b["after"]["w0305"]=0x4C
        for row in self.b["samples"]:
            row["w0305"]=0x4C
        with self.assertRaisesRegex(ValueError,"exactly one"):
            collect(self.a,self.b)

    def test_second_map_switch_rejected(self):
        self.b["samples"][0]["w0305"]=0x4C
        with self.assertRaisesRegex(ValueError,"exactly one"):
            collect(self.a,self.b)

    def test_lack_of_settled_arrival_rejected(self):
        for row in self.b["samples"]:
            row["w1573"],row["w157d"]=55,237
        self.b["after"]["w1573"],self.b["after"]["w157d"]=55,237
        with self.assertRaisesRegex(ValueError,"Could not prove"):
            collect(self.a,self.b)

    def test_unstable_post_arrival_rejected(self):
        self.b["samples"][-2]["w1573"]=55
        with self.assertRaisesRegex(ValueError,"Could not prove"):
            collect(self.a,self.b)

    def test_unsupported_short_stability_rejected(self):
        with self.assertRaisesRegex(ValueError,"Invalid stable-window"):
            collect(self.a,self.b,stability_frames=0)

    def test_schema2_selector_delta_is_tracked(self):
        for doc in (self.a,self.b):
            doc["schema_version"]=2
            for row in [doc["before"],*doc["samples"],doc["after"]]:
                row.update(w0306=2,w126e=0x4C,w12b4=0x4C,w12b5=0)
        for row in self.a["samples"]:
            if row["frame"]>=663064:
                row["w126e"]=0x50
        self.a["after"]["w126e"]=0x50
        self.b["before"]["w126e"]=0x50
        for row in self.b["samples"]:
            row["w126e"]=0x50
        self.b["after"]["w126e"]=0x50
        result=collect(self.a,self.b)
        self.assertEqual(result["selector_raw_at_switch"]["w126e"],0x50)
        self.assertTrue(result["selector_changes_near_switch"])
        self.assertFalse(result["VM_opcode_53_or_56_executed_proven"])
    def test_mixed_schema_versions_rejected(self):
        self.a["schema_version"]=2
        for row in [self.a["before"],*self.a["samples"],self.a["after"]]:
            row.update(w0306=2,w126e=0x4C,w12b4=0x4C,w12b5=0)
        with self.assertRaisesRegex(ValueError,"schema differ"):collect(self.a,self.b)
    def test_repository_evidence_explicitly_denies_opcode_proof(self):
        p=ROOT/"data/maps/transitions/tabidachi_world_entry_phase_evidence_20261011.json"
        d=json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(d["pack_switch_frame"],663064)
        self.assertEqual(d["first_settled_arrival_frame"],663169)
        self.assertEqual(d["raw_script_pointer_at_switch"],{"bank":204,"high":7,"low":222})
        self.assertEqual(d["event_entry_byte_at_switch"],2)
        self.assertEqual(d["saved_pack_bytes_at_switch"],{"w15cf":76,"w15d0":80})
        self.assertFalse(d["VM_opcode_53_or_56_executed_proven"])
        self.assertFalse(d["new_source_map_binding_promoted"])


if __name__=="__main__":
    unittest.main()
