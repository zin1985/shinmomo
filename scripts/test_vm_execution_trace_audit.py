#!/usr/bin/env python3
"""Fail-closed synthetic regression for background VM execution-trace audit."""
from __future__ import annotations
import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from audit_vm_execution_trace import inspect_trace, cpu_addr


def trace():
    return {
        "kind":"isolated_vm_execution_trace",
        "input_sent":False,
        "requested_neutral_frames":2,
        "advanced_frames":2,
        "hook_registered":18,
        "hook_errors":"",
        "event_limit":256,
        "dropped_events":0,
        "before":{"frame":100,"w0305":241},
        "after":{"frame":102,"w0305":241},
        "events":[]
    }


def observed_vm56():
    return {
        "frame":101,"hook":"vm56_map_transition",
        "cpu_pc":0x8B6A,"cpu_pbr":0xC4,
        "cpu_y":1,
        "vm_script_ptr_cpu":0xCC3DF1,
        "w0305_map_pack":0xF1,
        "w035f_vm_mode":0,"w1398_dispatch_mode":0,
    }


class VMExecutionTraceAuditTests(unittest.TestCase):
    def test_empty_observation_no_false_transition(self):
        got=inspect_trace(trace(),[])
        self.assertFalse(got["any_vm56_handler_executed"])
        self.assertEqual(got["confirmed_source_map_bindings"],0)
        self.assertEqual(got["event_count"],0)

    def test_runtime_handler_hit_does_not_prove_source(self):
        d=trace()
        d["events"]=[observed_vm56()]
        catalog=[{"trigger_addr":"CC:3DF1","script_pack":"0x60",
                  "destination_pack":"0x25","destination_entry_id":"0x02"}]
        got=inspect_trace(d,catalog)
        self.assertTrue(got["any_vm56_handler_executed"])
        self.assertEqual(got["confirmed_source_map_bindings"],0)
        self.assertFalse(got["events"][0]["source_map_configuration_proven"])
        self.assertEqual(got["events"][0]["catalog_candidates_at_exact_pointer"][0]["trigger_addr"],"CC:3DF1")
        self.assertEqual(got["events"][0]["operand_fetch_cpu_estimate"],"CC:3DF2")

    def test_observed_deferred_callback_is_not_source_proof(self):
        d=trace()
        e=observed_vm56()
        e["hook"]="vm25_deferred_callback"
        d["events"]=[e]
        got=inspect_trace(d,[])
        self.assertTrue(got["any_vm25_callback_executed"])
        self.assertFalse(got["any_vm56_handler_executed"])
        self.assertEqual(got["confirmed_source_map_bindings"],0)

    def test_non_neutral_capture_rejected(self):
        d=trace();d["input_sent"]=True
        with self.assertRaisesRegex(ValueError,"Input"):inspect_trace(d,[])

    def test_declared_isolated_gamepad_trace(self):
        d=trace()
        d.update({
            "requested_neutral_frames":0,
            "requested_input_frames":2,
            "input_sent":True,
            "input_device":"isolated_snes_gamepad",
            "buttons":"Down",
            "player":1,
        })
        d["events"]=[observed_vm56()]
        out=inspect_trace(d,[])
        self.assertTrue(out["input_sent"])
        self.assertEqual(out["isolated_gamepad_frames_advanced"],2)
        self.assertEqual(out["confirmed_source_map_bindings"],0)

    def test_forged_desktop_input_rejected(self):
        d=trace()
        d.update({
            "requested_neutral_frames":0,"requested_input_frames":2,
            "input_sent":True,"input_device":"desktop_keyboard",
            "buttons":"Down","player":1
        })
        with self.assertRaisesRegex(ValueError,"isolated SNES gamepad"):
            inspect_trace(d,[])

    def test_overly_large_gamepad_window_rejected(self):
        d=trace()
        d.update({"requested_neutral_frames":0,"requested_input_frames":121,
                  "input_sent":True,"input_device":"isolated_snes_gamepad",
                  "buttons":"Down","player":1,"advanced_frames":121})
        with self.assertRaisesRegex(ValueError,"frame count"):
            inspect_trace(d,[])

    def test_mismatched_end_frame_rejected(self):
        d=trace();d["after"]["frame"]=103
        with self.assertRaisesRegex(ValueError,"frame span"):inspect_trace(d,[])

    def test_unregistered_hooks_rejected(self):
        d=trace();d["hook_registered"]=0
        with self.assertRaisesRegex(ValueError,"No execution hooks"):inspect_trace(d,[])

    def test_outside_frame_event_rejected(self):
        d=trace()
        event=observed_vm56();event["frame"]=105
        d["events"]=[event]
        with self.assertRaisesRegex(ValueError,"out-of-frame"):inspect_trace(d,[])

    def test_unknown_hook_rejected(self):
        d=trace()
        event=observed_vm56();event["hook"]="spoofed_transition"
        d["events"]=[event]
        with self.assertRaisesRegex(ValueError,"Unknown"):inspect_trace(d,[])

    def test_capacity_overflow_not_completely_confirmed(self):
        d=trace();d["dropped_events"]=2
        got=inspect_trace(d,[])
        self.assertFalse(got["trace_complete_without_overflow"])
        self.assertEqual(got["dropped_events"],2)

    def test_negative_and_unmapped_ptrs_ignored(self):
        self.assertIsNone(cpu_addr(-1))
        self.assertIsNone(cpu_addr(0x840000))
        self.assertEqual(cpu_addr(0xC0FFFF),"C0:FFFF")


if __name__=="__main__":
    unittest.main()
