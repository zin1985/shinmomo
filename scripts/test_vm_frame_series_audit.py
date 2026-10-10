#!/usr/bin/env python3
"""Fail-closed contract and regression tests for bounded WRAM frame series."""
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from audit_vm_frame_series import inspect_series


def state(frame,pack=0x2E,x=9,y=12,label="sample"):
    return {"label":label,"frame":frame,"w0305":pack,"w035f":0,
            "w1398":0,"w13b8":4,"ptr98_lo":0,"ptr99_hi":0,
            "ptr9a_bank":0,"w1573":x,"w157d":y,"w15cf":0,"w15d0":0}


def valid():
    before=state(100,label="before")
    samples=[state(101,0x2E,9,13),state(102,0x50,29,17)]
    return {"kind":"isolated_vm_frame_series","schema_version":1,
            "requested_frames":2,"advanced_frames":2,"input_sent":True,
            "input_device":"isolated_snes_gamepad",
            "buttons":"Down","player":1,
            "sampling_method":"onframeend_WRAM_no_PC_hook",
            "cpu_execution_hook_delivery_proven":False,
            "before":before,"after":dict(samples[-1],label="after"),
            "samples":samples}


class FrameSeriesTests(unittest.TestCase):
    def test_exact_switch_from_wram(self):
        out=inspect_series(valid())
        self.assertEqual(out["map_switch_count"],1)
        self.assertEqual(out["map_switches"][0]["frame"],102)
        self.assertEqual(out["map_switches"][0]["before_position"],{"x":9,"y":13})
        self.assertEqual(out["map_switches"][0]["after_position"],{"x":29,"y":17})
        self.assertFalse(out["map_switches"][0]["vm_handler_execution_proven"])
        self.assertEqual(out["new_graph_edges_added"],0)
    def test_neutral_framed_sample(self):
        d=valid()
        d["input_sent"]=False;d["input_device"]="none"
        d["buttons"]="";d["player"]=None
        self.assertFalse(inspect_series(d)["input_sent"])
    def test_no_frame_gaps(self):
        d=valid();d["samples"][0]["frame"]=100
        with self.assertRaisesRegex(ValueError,"shifted"):inspect_series(d)
    def test_no_out_of_order(self):
        d=valid();d["samples"][1]["frame"]=101
        with self.assertRaisesRegex(ValueError,"shifted"):inspect_series(d)
    def test_reject_missing_sample(self):
        d=valid();d["samples"].pop()
        with self.assertRaisesRegex(ValueError,"sample count"):inspect_series(d)
    def test_reject_final_inconsistent_state(self):
        d=valid();d["after"]["w0305"]=0x4C
        with self.assertRaisesRegex(ValueError,"disagree"):inspect_series(d)
    def test_reject_wrong_input_device(self):
        d=valid();d["input_device"]="desktop_keyboard"
        with self.assertRaisesRegex(ValueError,"isolated SNES"):inspect_series(d)
    def test_reject_invalid_buttons(self):
        d=valid();d["buttons"]="Up+Down"
        with self.assertRaisesRegex(ValueError,"isolated SNES"):inspect_series(d)
    def test_reject_copied_cpu_proof(self):
        d=valid();d["cpu_execution_hook_delivery_proven"]=True
        with self.assertRaisesRegex(ValueError,"CPU execute-hook"):inspect_series(d)
    def test_reject_truncated_frame_count(self):
        d=valid();d["advanced_frames"]=1
        with self.assertRaisesRegex(ValueError,"incomplete"):inspect_series(d)
    def test_reject_oversized_window(self):
        d=valid();d["requested_frames"]=121;d["advanced_frames"]=121
        with self.assertRaisesRegex(ValueError,"Unbounded"):inspect_series(d)
    def test_byte_overflow_rejected(self):
        d=valid();d["samples"][0]["w1398"]=256
        with self.assertRaisesRegex(ValueError,"byte"):inspect_series(d)
    def test_multiple_map_changes_observed_without_graph_promotion(self):
        d=valid()
        d["samples"][0]["w0305"]=0x4C
        out=inspect_series(d)
        self.assertEqual(out["map_switch_count"],2)
        self.assertEqual(out["confirmed_source_map_bindings_added"],0)


if __name__=="__main__":
    unittest.main()
