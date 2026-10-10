#!/usr/bin/env python3
"""Offline fixture tests for coordinate-sensitive Tabidachi world/village proof."""
from __future__ import annotations
import copy,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools/python"))
from verify_tabidachi_world_roundtrip import summarize


def fixtures(directory):
    v=[]
    w=[]
    for i in range(1,21):
        pack=0x4C if i==20 else 0x50
        y=237 if i==20 else 54 if i<3 else 55 if i<11 else 56
        x=55 if i==20 else 29
        before_pack=0x50
        v.append(dict(step=i,frame0=1000+i-1,frame1=1000+i,
                      pack0=before_pack,pack1=pack,x=x,y=y,hook_hits=0))
    for i in range(1,19):
        pack=0x50 if i==18 else 0x4C
        w.append(dict(step=i,frame0=2000+i-1,frame1=2000+i,
                      pack0=0x4C,pack1=pack,x=55,
                      y=236 if i==1 else 237,hook_hits=0))
    for rows in (v,w):
        for row in rows:
            path=Path(directory)/f"{row['frame1']}.json"
            trace=dict(kind="isolated_vm_execution_trace",
              input_sent=True,input_device="isolated_snes_gamepad",
              buttons="Down",player=1,requested_input_frames=1,
              requested_neutral_frames=0,advanced_frames=1,
              hook_errors="",dropped_events=0,events=[],
              before={"frame":row["frame0"],"w0305":row["pack0"]},
              after={"frame":row["frame1"],"w0305":row["pack1"],
                     "w1573":row["x"],"w157d":row["y"]})
            path.write_text(json.dumps(trace),encoding="utf-8")
            row["file"]=str(path)
    village=dict(kind="native_world_return_variant_replay",
                 start_state="vmtrace_tabidachi_pack50_south_x29_y54_20261011",
                 rows=v)
    world=dict(kind="world_to_village_exact_reentry",
               origin_state="vmtrace_world_pack4c_x55_y236_preentry_20261011",
               input_device="isolated_snes_gamepad",rows=w)
    settled=dict(source="vmtrace_world_pack4c_x55_y236_preentry_20261011.State",
                 switch_frame=2018,settled_pack="0x50",
                 settled_x="0x1D",settled_y="0x37",settled_frame=2178)
    return village,world,settled


class TabidachiCoordinateVariantsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.v,self.w,self.settled=fixtures(self.tmp.name)
    def tearDown(self):
        self.tmp.cleanup()
    def calc(self):
        return summarize(self.v,self.w,self.settled,{"a":"A"*64})
    def test_valid_two_way_evidence(self):
        d=self.calc()
        self.assertEqual(d["village_to_world"]["arrival"],{"x":55,"y":237})
        self.assertEqual(d["world_to_village"]["settled_arrival"],{"x":29,"y":55})
        self.assertEqual(len(d["position_dependent_native_return"]["confirmed_coordinate_pairs"]),2)
        self.assertFalse(d["position_dependent_native_return"]["general_coordinate_transform_proven"])
    def test_bad_source_x_rejected(self):
        self.v["rows"][3]["x"]=28
        with self.assertRaises(ValueError):self.calc()
    def test_forged_controller_rejected(self):
        p=Path(self.w["rows"][5]["file"])
        d=json.loads(p.read_text(encoding="utf-8"))
        d["input_device"]="desktop_keyboard"
        p.write_text(json.dumps(d),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"Unsafe/incomplete"):self.calc()
    def test_settled_arrival_must_match(self):
        self.settled["settled_x"]="0x1C"
        with self.assertRaisesRegex(ValueError,"Post-transition"):self.calc()
    def test_frame_gap_rejected(self):
        self.w["rows"][7]["frame0"]=4000
        self.w["rows"][7]["frame1"]=4001
        with self.assertRaisesRegex(ValueError,"Missing frame"):self.calc()
    def test_production_metadata_preserves_two_variants_not_formula(self):
        d=json.loads((ROOT/"data/maps/transitions/tabidachi_x29_world_x55_roundtrip_20261011.json").read_text(encoding="utf-8"))
        self.assertEqual(d["village_to_world"]["switch_frame"],662186)
        self.assertEqual(d["world_to_village"]["switch_to_pack_0x50_frame"],663064)
        self.assertFalse(d["position_dependent_native_return"]["full_exit_width_proven"])
        self.assertEqual(d["cpu_hook_events_observed"],0)


if __name__=="__main__": unittest.main()
