#!/usr/bin/env python3
"""Synthetic 4-stage frame-series replay fixture and fail-closed tests."""
from __future__ import annotations
import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from verify_vm_frame_series_replays import validate_series


def frame(n,pack,x,y,label="sample"):
    return {"label":label,"frame":n,"w0305":pack,"w035f":0,
            "w1398":0,"w13b8":4,"ptr98_lo":0,"ptr99_hi":0,
            "ptr9a_bank":0,"w1573":x,"w157d":y,"w15cf":0,"w15d0":0}


def make_series(start,steps,before_pack,before_xy,pack_end,xy_end,buttons):
    rows=[]
    for i in range(1,steps+1):
        p=pack_end if i==steps else before_pack
        xy=xy_end if i==steps else before_xy
        rows.append(frame(start+i,p,*xy))
    return {"kind":"isolated_vm_frame_series","schema_version":1,
            "requested_frames":steps,"advanced_frames":steps,
            "input_sent":bool(buttons),
            "input_device":"isolated_snes_gamepad" if buttons else "none",
            "buttons":buttons,"player":1 if buttons else None,
            "sampling_method":"onframeend_WRAM_no_PC_hook",
            "cpu_execution_hook_delivery_proven":False,
            "before":frame(start,before_pack,*before_xy,label="before"),
            "after":dict(rows[-1],label="after"),"samples":rows}


def corpus():
    a=make_series(661523,23,0x2E,(9,13),0x50,(29,17),"Down")
    a["samples"][0]["w157d"]=10
    b=make_series(662166,20,0x50,(29,56),0x4C,(55,237),"Down")
    c=make_series(663046,18,0x4C,(55,237),0x50,(55,237),"Down")
    c["before"]["w157d"]=236
    d=make_series(663064,120,0x50,(55,237),0x50,(29,55),"")
    for i,row in enumerate(d["samples"]):
        if row["frame"]>=663169:
            row["w1573"]=29
            row["w157d"]=55
    return dict(interior_exit=a,village_exit=b,world_entry=c,world_settle=d)


class FrameReplayTests(unittest.TestCase):
    def test_valid_realistic_four_stage_replay(self):
        r=validate_series(corpus())
        self.assertEqual(r["observed"]["world_pack4c_to_village_pack50"]["switch_to_settled_coordinate_delay_frames"],105)
        self.assertEqual(r["new_runtime_source_edges"],0)
        self.assertFalse(r["exact_CPU_VM_opcode_execution_proven"])
    def test_missing_final_arrival_rejected(self):
        d=corpus()
        for row in d["world_settle"]["samples"]:
            row["w1573"]=55
            row["w157d"]=237
        d["world_settle"]["after"]=dict(d["world_settle"]["samples"][-1],label="after")
        with self.assertRaisesRegex(ValueError,"Unexpected world_settle"):validate_series(d)
    def test_changed_arrival_after_settle_rejected(self):
        d=corpus()
        d["world_settle"]["samples"][-3]["w1573"]=55
        with self.assertRaisesRegex(ValueError,"did not remain stable"):validate_series(d)
    def test_wrong_pack_sequence_rejected(self):
        d=corpus();d["village_exit"]["samples"][8]["w0305"]=0x4C
        with self.assertRaisesRegex(ValueError,"Ambiguous/missing"):validate_series(d)
    def test_unknown_cpu_claim_rejected(self):
        d=corpus();d["world_entry"]["cpu_execution_hook_delivery_proven"]=True
        with self.assertRaisesRegex(ValueError,"execute-hook"):validate_series(d)
    def test_checked_in_metadata(self):
        d=json.loads((ROOT/"data/maps/transitions/tabidachi_frame_series_replay_20261011.json").read_text(encoding="utf-8"))
        self.assertEqual(d["observed"]["interior_pack2e_to_village_pack50"]["switch_frame"],661546)
        self.assertEqual(d["observed"]["village_pack50_to_world_pack4c"]["switch_frame"],662186)
        self.assertEqual(d["observed"]["world_pack4c_to_village_pack50"]["first_settled_arrival_frame"],663169)
        self.assertFalse(d["independent_cpu_hook_delivery_proven"])
        self.assertEqual(d["new_runtime_source_edges"],0)


if __name__=="__main__":
    unittest.main()
