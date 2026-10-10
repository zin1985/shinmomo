#!/usr/bin/env python3
"""Synthetic fail-closed tests for 0x2E native boundary one-frame replay."""
from __future__ import annotations
import sys,unittest
from copy import deepcopy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from verify_native_south_exit_replay import summarize


def fixture():
    coords=[(0x2E,9,10),(0x2E,9,11),(0x2E,9,12),
            (0x2E,9,13),(0x50,29,17)]
    records=[]
    traces=[]
    for i,(pack,x,y) in enumerate(coords,1):
        prev=coords[i-2][0] if i>1 else 0x2E
        row=dict(step=i,before=100+i-1,after=100+i,
                 p0=prev,p1=pack,x=x,y=y,events=0,dropped=0,
                 file=f"test_{i}.json")
        trace=dict(
            kind="isolated_vm_execution_trace",input_sent=True,
            input_device="isolated_snes_gamepad",buttons="Down",player=1,
            requested_neutral_frames=0,requested_input_frames=1,
            advanced_frames=1,dropped_events=0,hook_errors="",events=[],
            before={"frame":row["before"],"w0305":prev},
            after={"frame":row["after"],"w0305":pack,
                   "w1573":x,"w157d":y}
        )
        records.append(row);traces.append(trace)
    return (
        dict(kind="native_exit_runtime_replay",frames=records,
             origin_state="vmtrace_tabidachi_pack2e_interior_20261011",
             current_user_desktop_untouched=True),
        traces
    )


class NativeExitReplayTests(unittest.TestCase):
    def test_five_frame_minimal_runtime_proof(self):
        m,t=fixture()
        out=summarize(m,t,"A"*64)
        self.assertEqual(out["source"]["confirmed_center_exit_cell"]["x"],9)
        self.assertEqual(out["source"]["confirmed_center_exit_cell"]["y"],12)
        self.assertEqual(out["replay"]["switch_frame"],105)
        self.assertFalse(out["replay"]["execution_hook_firing_proven"])
        self.assertIn("Exit width beyond x=9",out["does_not_prove"])

    def test_unobserved_center_cell_rejected(self):
        m,t=fixture()
        m["frames"][2]["y"]=11
        t[2]["after"]["w157d"]=11
        with self.assertRaisesRegex(ValueError,"inside-to-outside"):summarize(m,t,"A"*64)

    def test_wrong_destination_rejected(self):
        m,t=fixture()
        m["frames"][-1]["x"]=30
        t[-1]["after"]["w1573"]=30
        with self.assertRaisesRegex(ValueError,"Unexpected native return arrival"):summarize(m,t,"A"*64)

    def test_missing_frame_rejected(self):
        m,t=fixture()
        m["frames"][3]["before"]=106
        t[3]["before"]["frame"]=106
        m["frames"][3]["after"]=107
        t[3]["after"]["frame"]=107
        with self.assertRaisesRegex(ValueError,"Missing/overlapping"):summarize(m,t,"A"*64)

    def test_raw_trace_mismatch_rejected(self):
        m,t=fixture()
        t[-1]["after"]["w0305"]=0x4C
        with self.assertRaisesRegex(ValueError,"Trace and replay state"):summarize(m,t,"A"*64)

    def test_invalid_desktop_input_rejected(self):
        m,t=fixture()
        t[1]["input_device"]="desktop_keyboard"
        with self.assertRaisesRegex(ValueError,"Unsafe or incomplete"):summarize(m,t,"A"*64)

    def test_dropped_hook_buffer_rejected(self):
        m,t=fixture()
        t[1]["dropped_events"]=1
        with self.assertRaisesRegex(ValueError,"Unsafe or incomplete"):summarize(m,t,"A"*64)

    def test_production_metadata_keeps_navigability_unproven(self):
        import json
        data=json.loads((ROOT/"data/maps/transitions/pack2e_exact_south_exit_20261011.json").read_text(encoding="utf-8"))
        self.assertEqual(data["replay"]["switch_frame"],661546)
        self.assertEqual(data["source"]["first_outside_cell"],{"x":9,"y":13})
        self.assertEqual(data["replay"]["number_of_exact_input_frames"],23)
        self.assertFalse(data["replay"]["execution_hook_firing_proven"])
        self.assertEqual(data["destination"]["arrival"],{"x":29,"y":17})


if __name__=="__main__":
    unittest.main()
